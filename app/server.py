"""The web face of the handbook agent.

Run from the repository root:

    uvicorn app.server:app --reload

Conversations persist server-side as LangGraph checkpoints, one thread per
chat, in SQLite. The browser holds only addresses — which thread ids exist and
what to call them — and sends one new message per turn; the graph loads the
rest of the conversation from the store before it runs. That is the canonical
LangGraph shape: the agent owns its state, the client owns a pointer to it.

The cost of that choice, stated plainly: the server is no longer stateless. A
restart keeps every chat (the store is a file), but running two copies means
two stores unless they share one. Fine for a single-instance demo, and a
deliberate trade for persistence that survives a page refresh.
"""

import json
import threading
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel, Field

from app.agent import ChatContext, build_agent
from app.config import BASE_DIR, CHATS_DB, DAILY_TOKEN_BUDGET
from app.employees import list_employees


class DailyTokenBudget:
    """Per-IP spending ceiling, reset daily, held in memory.

    In memory on purpose: this protects an API key on a demo, it is not
    billing. A restart forgiving everyone is an acceptable failure, a Redis
    dependency for a portfolio deployment is not. The lock is there because
    the server handles requests concurrently, and lost-update on a counter is
    exactly the classic race.
    """

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._lock = threading.Lock()
        # ip -> (day the count belongs to, tokens spent that day). Keyed by
        # day so stale entries reset themselves on first touch after midnight
        # rather than needing a sweeper.
        self._spent: dict[str, tuple[date, int]] = {}

    def remaining(self, ip: str) -> int:
        with self._lock:
            day, spent = self._spent.get(ip, (date.today(), 0))
            if day != date.today():
                spent = 0
            return max(0, self.limit - spent)

    def charge(self, ip: str, tokens: int) -> None:
        with self._lock:
            today = date.today()
            day, spent = self._spent.get(ip, (today, 0))
            if day != today:
                spent = 0
            self._spent[ip] = (today, spent + tokens)


def client_ip(request: Request) -> str:
    """The caller's address, preferring the proxy's forwarded header.

    Deployed behind a hosting platform's proxy, request.client is the proxy —
    every visitor would share one budget. X-Forwarded-For carries the real
    address; its first entry is the original client. A caller can forge the
    header when the server is exposed directly, so this is abuse resistance
    for a demo, not authentication.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the expensive things once, at startup, not per request.

    build_agent() opens the Chroma index, which loads the embedding model —
    seconds of work. Doing it here means the first user request is fast, and a
    broken index fails the server at boot, loudly, instead of failing the first
    visitor quietly.

    The checkpointer is the async flavour because the routes are async: the
    graph awaits the store between steps, and a sync saver would block the
    event loop on every write. It is an async context manager — the connection
    lives exactly as long as the server does, which is what `async with`
    wrapped around `yield` expresses.
    """
    CHATS_DB.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(CHATS_DB)) as checkpointer:
        app.state.agent = build_agent(checkpointer=checkpointer)
        app.state.budget = DailyTokenBudget(DAILY_TOKEN_BUDGET)
        yield
    # Leaving the `async with` closes the SQLite connection. Chroma, the
    # embedding model, and the budget state just die with the process.


app = FastAPI(
    title="Meridian Handbook Assistant",
    description="RAG chat over a synthetic employee handbook.",
    lifespan=lifespan,
)


# Thread ids are client-minted (crypto.randomUUID in the page). The pattern
# keeps them boring: anything that is both a SQLite key and a URL path segment
# should not be allowed to contain surprises.
THREAD_ID_PATTERN = r"^[A-Za-z0-9_-]{8,64}$"


class ChatRequest(BaseModel):
    thread_id: str = Field(pattern=THREAD_ID_PATTERN)
    # One turn, not the history — the store has the history. Capped because it
    # is client input and unbounded input is a cost hole.
    message: str = Field(min_length=1, max_length=4000)
    employee_id: str | None = None


class WireMessage(BaseModel):
    """One displayable turn, as GET /chats/{id} returns it."""

    role: Literal["user", "assistant"]
    content: str


def sse(event: str, data: dict) -> str:
    """One Server-Sent Event, wire-formatted."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# response_model=None: the return annotation is a union of concrete Response
# classes, which is for the reader and the type checker — FastAPI must not try
# to build a serialization schema out of it.
@app.post("/chat", response_model=None)
async def chat(request: Request, body: ChatRequest) -> StreamingResponse | JSONResponse:
    """Answer one turn of a thread, streamed as it happens.

    The response is an SSE stream with four event types:

        search  {query}   the agent ran a handbook search
        token   {text}    the next piece of the answer
        done    {text}    the complete answer, once, at the end
        error   {detail}  something failed mid-stream

    `done` carries the full text even though the client watched it arrive in
    pieces: the client renders from that, not from glued tokens, so a dropped
    token during rendering cannot corrupt what it shows.
    """
    budget = request.app.state.budget
    ip = client_ip(request)
    if budget.remaining(ip) <= 0:
        # Nothing has streamed yet, so a real status code still works — and a
        # 429 is kinder to clients than an in-band error event, because every
        # HTTP library already knows what it means.
        return JSONResponse(
            status_code=429,
            content={"detail": "Daily demo limit reached for this address. "
                               "Come back tomorrow."},
        )

    agent = request.app.state.agent
    context = ChatContext(employee_id=body.employee_id)
    config = {"configurable": {"thread_id": body.thread_id}}

    async def stream():
        # Two stream modes: `messages` for tokens, `updates` for everything
        # that happened at the step level — searches, and the model calls whose
        # usage we charge for. No `values` mode: the full state now includes
        # the loaded history, so "what is new this turn" is only knowable from
        # updates, where each step's output appears exactly once.
        final_text = ""
        spent = 0
        last_id = None
        try:
            async for mode, payload in agent.astream(
                {"messages": [{"role": "user", "content": body.message}]},
                config=config,
                context=context,
                stream_mode=["messages", "updates"],
            ):
                if mode == "messages":
                    chunk, _ = payload
                    # Tool output streams through here too; only the model's
                    # own words go to the client.
                    if isinstance(chunk, AIMessageChunk) and (text := chunk.text):
                        if last_id is not None and chunk.id != last_id:
                            yield sse("token", {"text": "\n\n"})
                        last_id = chunk.id
                        yield sse("token", {"text": text})

                elif mode == "updates":
                    for node_output in payload.values():
                        for message in node_output.get("messages", []):
                            for call in getattr(message, "tool_calls", []):
                                yield sse("search", {"query": call["args"]["query"]})
                            if isinstance(message, AIMessage):
                                if message.usage_metadata:
                                    spent += (message.usage_metadata["input_tokens"]
                                              + message.usage_metadata["output_tokens"])
                                if message.text:
                                    final_text = message.text

            yield sse("done", {"text": final_text})

        except Exception:
            # The stream may already be half-sent, so an HTTP error status is
            # no longer possible — the error has to travel in-band. Detail
            # stays out of the payload: stack traces are for the server log,
            # not for whoever is poking at a public demo.
            yield sse("error", {"detail": "something went wrong; try again"})

        finally:
            # In `finally` so an interrupted stream still pays for the tokens
            # it consumed before dying.
            budget.charge(ip, spent)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        # Proxies are allowed to buffer "text/event-stream" unless told not
        # to; buffering would turn streaming back into one big wait.
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/chats/{thread_id}")
async def chat_history(request: Request, thread_id: str) -> list[WireMessage]:
    """The displayable turns of one thread, for reopening a chat in the UI.

    Reads the graph's own checkpoint — there is no second copy of the
    conversation to drift out of sync with it. Tool calls and tool results are
    filtered out: they are the agent's working, not the conversation.

    Ownership is the thread id itself. The ids are 122-bit random UUIDs minted
    in the browser, so guessing one is not a practical attack; but anyone who
    has an id can read that chat. For a demo with synthetic data that is the
    right trade. A real deployment would bind threads to an authenticated user.
    """
    state = await request.app.state.agent.aget_state(
        {"configurable": {"thread_id": thread_id}}
    )
    messages = state.values.get("messages", [])
    if not messages:
        raise HTTPException(status_code=404, detail="no such chat")

    turns = []
    for message in messages:
        if isinstance(message, HumanMessage):
            turns.append(WireMessage(role="user", content=message.text))
        # An AIMessage with no text is a pure tool call — not a turn to show.
        elif isinstance(message, AIMessage) and message.text:
            turns.append(WireMessage(role="assistant", content=message.text))
    return turns


@app.get("/employees")
def employees() -> list[dict]:
    """The demo personas, for the picker in the UI.

    Returns display fields only. The absence of anything sensitive here is the
    point of the demo data being synthetic — but the habit of choosing fields
    for a public endpoint explicitly, rather than dumping rows, is the part
    worth keeping.
    """
    return [
        {
            "id": e.id,
            "name": e.name,
            "location": e.location,
            "level": e.level,
            "worker_type": e.worker_type,
            "tenure_months": e.tenure_months,
        }
        for e in list_employees()
    ]


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """The chat page. One file, no build step — FileResponse is enough."""
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health() -> dict:
    """Liveness probe: the process is up and the agent was built.

    Deliberately does no real work — no model call, no search. Hosting
    platforms poll this every few seconds, and a health check that costs
    tokens is a bill, not a check.
    """
    return {"status": "ok"}
