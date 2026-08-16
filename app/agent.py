"""The handbook agent: Claude plus the `search_handbook` tool.

Agentic RAG — the model decides when to search and how many times, rather than
one fixed retrieval pass being stuffed into the prompt. That matters here
because the corpus cross-references itself constantly: the PTO rate lives in
HR-004 but the tenure tiers it depends on live in HR-001, and no single search
finds both.
"""

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

# Importing config first also loads .env, which is where ANTHROPIC_API_KEY comes
# from. ChatAnthropic reads that variable itself — the key is never passed here.
from app.config import CHAT_MODEL
from app.employees import get_employee
from app.rag.retriever import get_store, search_handbook

SYSTEM_PROMPT = """You answer questions about the Meridian Systems employee \
handbook for employees of the company.

Use the search_handbook tool before answering any policy question. Do not answer
from memory — you have no reliable knowledge of this company's policies, and a
plausible-sounding invented answer is worse than no answer.

Search more than once when the first result is incomplete. Handbook sections
refer to each other constantly: a section on time off will say the rate depends
on "tenure tier, as defined in HR-001 §4" without saying what the tiers are. When
a result points at another document or section you have not read, search for it
before answering.

Watch for qualifiers that narrow a rule:
- Country or legal entity. On-call pay, pension, and leave all differ between
  the US, Canada, Ireland, Germany, and Singapore. A figure written for one
  country is wrong for another.
- Job level, and worker type. Contractors and interns are excluded from many
  policies that cover regular employees.
- Tenure. Several entitlements scale with length of service.
If the answer depends on one of these and the employee has not said which
applies to them, give the relevant cases rather than picking one.

POL-000 is the amendment log. Where it records a change to a figure or date, it
supersedes the original text, and rates can differ by the date of the event —
say which applies from when.

Cite the sections you used, inline, as [HR-004 §3.1]. Cite only identifiers that
appeared in a search result.

Search before saying you do not know something. You cannot tell what the
handbook contains without looking, so "the handbook does not cover this" is a
claim that requires a search behind it — at least two, in different wording,
since the phrasing that failed is usually the employee's rather than the
handbook's. Never decline a question about Meridian without having searched.

The handbook describes the company as well as its policies: which legal entities
exist, where the offices are, how the organisation is structured, what the
products do. Questions about those are in scope.

If the handbook genuinely does not cover something, say so plainly and suggest
who to ask.
Do not extrapolate from a similar policy, and do not guess at figures the
handbook deliberately does not publish, such as individual salary bands. Decline
requests unrelated to the handbook.

Answer in a few sentences where a few sentences will do. Lead with the answer,
then the conditions attached to it.

Do not narrate your searching. "The results did not cover Germany, so let me
search again" tells the employee nothing they need — just run the search and
answer. Their view is the answer, not the process.

If you got something wrong, correct it in a sentence and move on. Do not
apologise at length, restate what you searched for, or explain what you should
have done differently. A follow-up question is not by itself proof you erred —
if your earlier answer was right, say so plainly instead of retracting it."""


EMPLOYEE_PREAMBLE = """You are answering for a specific employee:

{profile}

Answer for this person. Do not ask which country, level, worker type or tenure
applies — you have been told. Where a policy differs along one of those lines,
give the branch that applies to them and name the branch, so they can see why
their answer is what it is.

Where a policy excludes them, say that plainly rather than describing what other
people get. Contractors in particular are outside most of this handbook.

The employee details above are authoritative about the person. They are not part
of the handbook, so do not cite them as a section — cite the handbook sections
that establish what their situation entitles them to."""


class ChatContext(BaseModel):
    """Per-request context, declared to `create_agent` as its `context_schema`.

    Not state. State is the conversation, which the agent owns and mutates.
    This is what the caller knows and the agent does not — who is asking. It is
    supplied at invoke time and never modified.
    """

    employee_id: str | None = Field(
        default=None,
        description="Employee to answer as. None means answer generically.",
    )


@dynamic_prompt
def handbook_prompt(request: ModelRequest) -> str:
    """Build the system prompt for this request, from who is asking.

    Runs before every model call. Baking the employee into `create_agent`
    instead would mean one agent object per person, so the server would rebuild
    the whole graph per request rather than holding one and passing context
    through it.

    The profile lands in the system prompt rather than the message history so it
    sits ahead of the conversation in the cached prefix: one cache entry per
    employee, and their details are not re-sent inside every turn.
    """
    # Callers are not obliged to pass a context at all — invoke() without one
    # leaves runtime.context as None. Both eval scripts do exactly that, and
    # they mean the same thing as an explicit empty context: anonymous.
    context = request.runtime.context
    employee_id = context.employee_id if context is not None else None
    if not employee_id:
        return SYSTEM_PROMPT

    employee = get_employee(employee_id)
    if employee is None:
        # An unknown id means the caller is wrong, not the employee. Falling
        # back to the generic prompt is the safe failure — hedged answers rather
        # than confident ones about the wrong person.
        return SYSTEM_PROMPT

    return SYSTEM_PROMPT + "\n\n" + EMPLOYEE_PREAMBLE.format(
        profile=employee.as_context()
    )


def build_agent():
    """Wire the model, the tool, and the prompt middleware into one agent.

    Built once per process. Who is asking arrives per invocation:

        agent.invoke({"messages": [...]}, context=ChatContext(employee_id="jdoe"))
    """
    # Open the index here rather than on the first search. It moves the embedding
    # model's load time to startup where it is expected, and keeps construction
    # off the worker threads that run parallel tool calls.
    get_store()

    model = ChatAnthropic(
        model=CHAT_MODEL,
        # Answers cite a handful of sections — they do not need to be long.
        # Haiku 4.5 can go to 64000, but a low ceiling caps the cost of any one
        # request, which matters for a public demo.
        max_tokens=2048,
        # No `effort` here. It is supported on Opus 4.5+ and Sonnet 4.6+, but
        # errors on Haiku 4.5 — this model has no reasoning-depth control.
        #
        # Automatic prompt caching: the API marks the last cacheable block, so
        # the whole prefix — tools, system prompt, and every prior turn — is
        # read back at ~10% of input price on the next call. Answering one
        # question takes at least two calls (decide to search, then answer) and
        # the second repeats everything the first sent, so this pays for itself
        # within a single question.
        #
        # Note the prefix must stay byte-identical to be reused. Nothing here
        # interpolates a timestamp or a session id into the system prompt, and
        # nothing should start: one varying byte near the front silently
        # disables caching for everything after it.
        model_kwargs={"cache_control": {"type": "ephemeral"}},
    )

    return create_agent(
        model=model,
        tools=[search_handbook],
        # The middleware supplies the system prompt, so there is no static
        # `system_prompt=` here — passing both would be ambiguous.
        middleware=[handbook_prompt],
        context_schema=ChatContext,
    )