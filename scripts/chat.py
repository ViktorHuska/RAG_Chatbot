"""Talk to the handbook agent from the terminal.

Run from the repository root:

    python -m scripts.chat                    # user  — just the answer
    python -m scripts.chat dev                # dev   — plus which searches ran
    python -m scripts.chat debug              # debug — plus the retrieved text
    python -m scripts.chat --as jdoe          # answer as a specific employee
    python -m scripts.chat dev --as mgarcia   # both

`user` is what the chat UI will show. `dev` is what you want while tuning the
prompt: a wrong answer built on the right sections is a different bug from a
wrong answer built on the wrong ones, and the final text alone cannot tell you
which you have. `debug` is for when a search returns something surprising.

Without `--as`, the agent has no idea who is asking and hedges across countries
and levels. With it, ask the same question as `jdoe` and `asmith` and watch the
answers diverge.
"""

import argparse
import io
import sys

from langchain_core.messages import AIMessageChunk

from app.agent import ChatContext, build_agent
from app.employees import get_employee, list_employees

LEVELS = ("user", "dev", "debug")


def stream_turn(agent, messages: list, level: str, context: ChatContext) -> list:
    """Run one turn, printing tokens as they arrive. Returns the new history.

    Three stream modes at once, each answering a different question:

        messages  what is the model writing, token by token
        updates   what did each step just do (searches, results)
        values    what does the full conversation look like now

    `messages` alone would stream the answer but make searches invisible — a
    tool call arrives as chunks with empty text, so the screen just sits there.
    `updates` fills that gap.
    """
    state = {"messages": messages}
    last_message_id = None

    for mode, payload in agent.stream(
        {"messages": messages},
        context=context,
        stream_mode=["messages", "updates", "values"],
    ):
        if mode == "messages":
            chunk, _ = payload

            # The tool's output streams through here too, and its text is the
            # raw retrieved chunks. Only the model's own words belong on screen,
            # so this checks the chunk type rather than just testing for text.
            if isinstance(chunk, AIMessageChunk) and (text := chunk.text):
                # A turn that searches produces two assistant messages: what it
                # said before the tool call, and the answer after. Without a
                # break they run together as "...the policy.In Germany, you...".
                if last_message_id is not None and chunk.id != last_message_id:
                    print("\n")
                last_message_id = chunk.id

                print(text, end="", flush=True)

        elif mode == "updates" and level != "user":
            # {node_name: {"messages": [...]}} for whichever node just ran.
            for node_output in payload.values():
                for message in node_output.get("messages", []):
                    # One assistant message can hold several tool calls — the
                    # model is allowed to fire off searches in parallel.
                    for call in getattr(message, "tool_calls", []):
                        print(f"\n  [search] {call['args']['query']}")

                    if message.__class__.__name__ == "ToolMessage":
                        if level == "debug":
                            print(f"\n{message.content}\n")
                        else:
                            print(f"  [found]  {len(message.content)} characters")

        elif mode == "values":
            state = payload

    print()
    return state["messages"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with the handbook agent.")
    parser.add_argument(
        "level", nargs="?", default="user", choices=LEVELS,
        help="how much of the agent's working to show",
    )
    parser.add_argument(
        # `as` is a Python keyword, so the attribute needs its own name.
        "--as", dest="employee_id", metavar="ID",
        help="answer as this employee (see app/employees.py for the roster)",
    )
    args = parser.parse_args()
    level = args.level

    # The § in citations is not in the default Windows console codepage, so
    # printing one would raise UnicodeEncodeError without this. The isinstance
    # narrows the type — sys.stdout is declared as TextIO, which has no
    # .reconfigure(), and it really can be some other object when output is
    # captured or redirected. Skipping is right then: a replaced stream is
    # already handling encoding itself.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")

    # Resolved here purely to fail fast on a typo and to print who you are. The
    # agent looks the employee up again from the id — the CLI does not hand it
    # a profile object, so nothing changes when a web server is the caller.
    who = "anonymous"
    if args.employee_id:
        employee = get_employee(args.employee_id)
        if employee is None:
            known = ", ".join(e.id for e in list_employees())
            sys.exit(f"No employee {args.employee_id!r}. Known ids: {known}")
        who = f"{employee.name} — {employee.location}, {employee.level}"

    context = ChatContext(employee_id=args.employee_id)
    agent = build_agent()

    print("Ask about the Meridian Systems handbook. `exit` to quit.")
    print(f"[{level}]  asking as: {who}\n")

    # Kept across turns so follow-up questions work — "what about in Ireland?"
    # only makes sense if the model can still see what was asked before.
    messages = []

    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break

        messages.append({"role": "user", "content": question})

        # Reassigning is what preserves history. The tool calls and their
        # results have to stay in the list — Claude's API requires every tool
        # call to be followed by its result, so pruning them breaks the next turn.
        messages = stream_turn(agent, messages, level, context)


if __name__ == "__main__":
    main()