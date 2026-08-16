"""The graded evaluation set, as data.

Transcribed from `retrieval_eval.md`, which stays the human-readable version.
Both eval scripts import from here so the questions cannot drift apart:
`scripts/evaluate.py` reads `expect`, `scripts/evaluate_answers.py` reads
`answer`.

`expect` is a list of GROUPS. Every group must be satisfied, and a group is
satisfied by any one of its entries:

    [["HR-004 3.1"], ["HR-001 4.1"]]     both required (cross-document)
    [["SEC-001 7.1", "IT-001 8.1"]]      either one will do

Without that distinction a cross-document question would score as a pass when
retrieval found only half the answer — the exact failure this corpus exists to
expose.

`answer` is what a correct reply must convey. It is graded on substance, not
wording. Where it says "must not", that phrasing is the trap: a plausible wrong
answer sits next to the right one in the corpus.

This file lives outside `corpus/` on purpose — it holds the answers, so a bot
that could retrieve it would score well for the wrong reason.
"""

CASES = [
    # --- Tier 1: single-hop ---------------------------------------------------
    {
        "question": "How many company holidays do employees in Ireland get?",
        "expect": [["HR-004 2.1"]],
        "answer": "10 company holidays in Ireland, plus 2 floating days.",
    },
    {
        "question": "What's the 401(k) match?",
        "expect": [["HR-003 4.2"]],
        "answer": "100% of contributions up to 4% of salary, matched per pay "
                  "period, with no year-end true-up.",
    },
    {
        "question": "How long is a performance improvement plan?",
        "expect": [["HR-005 5.2"]],
        "answer": "60 days, extendable once by up to 30 days.",
    },
    {
        "question": "What laptop does a designer get?",
        "expect": [["IT-001 3.1"]],
        "answer": 'A 14" MacBook Pro with 24 GB of memory.',
    },
    {
        "question": "When must I report a lost laptop?",
        "expect": [["SEC-001 7.1", "IT-001 8.1"]],
        "answer": "Within one hour, to the #security-incidents channel.",
    },

    # --- Tier 2: cross-document ----------------------------------------------
    {
        "question": "I've been here three years. How much PTO do I get?",
        "expect": [["HR-004 3.1"], ["HR-001 4.1"]],
        "answer": "20 days. Three years of service is Tenure Tier B (25-60 "
                  "completed months), and Tier B accrues 20 days a year. Must "
                  "resolve the tier rather than just reciting the whole table.",
    },
    {
        "question": "I'm an engineer in Dublin going on call next week. What do "
                    "I get paid for it?",
        "expect": [["ENG-001 5.3"]],
        "answer": "12% of weekly base salary for primary rotation (6% for "
                  "secondary), plus compensatory time off 1:1 for out-of-hours "
                  "incident work and an 11-hour rest period if night work "
                  "exceeds 2 hours. Must NOT quote the USD 500 flat stipend — "
                  "that is US and Canada only.",
    },
    {
        "question": "Does my Irish pension contribution change as I stay longer?",
        "expect": [["HR-003 5.2"], ["HR-001 4.1"]],
        "answer": "Yes — employer PRSA contributions are 5%, 7%, or 9% of base "
                  "salary by tenure tier, starting after 6 months. Should "
                  "explain what a tenure tier is, not just list percentages.",
    },
    {
        "question": "My conference ticket was approved. Can I book flights?",
        "expect": [["HR-006 5.1"], ["FIN-001 3.2"]],
        "answer": "No. Learning-budget approval does not authorise travel; the "
                  "trip needs separate pre-approval under FIN-001 §3.1.",
    },
    {
        "question": "Who pays for my desk chair, monitor, and internet?",
        "expect": [["WRK-001 6.3"], ["IT-001 4"], ["HR-003 8"]],
        "answer": "Three separate budgets: the chair from the home office "
                  "stipend (USD 750 initial), the monitor from the IT "
                  "peripherals allowance (USD 400), internet from the HR-003 "
                  "allowance (USD 50/month). They cannot be pooled.",
    },

    # --- Tier 3: superseded values -------------------------------------------
    {
        "question": "How many PTO days can I carry into next year, and when do "
                    "they expire?",
        "expect": [["HR-004 4.2", "POL-000 3.1"]],
        "answer": "10 days, expiring 30 June. Must NOT say 5 days expiring "
                  "31 March — that is the superseded figure.",
    },
    {
        "question": "What's the meal per diem for a trip to London?",
        "expect": [["FIN-001 5.1"], ["POL-000 3.2"]],
        "answer": "London is Tier 1: USD 95 for travel to 31 March 2026, USD 110 "
                  "from 1 April 2026. The rate follows the date of travel, not "
                  "the date of claim. Must give the date qualifier, or ask when "
                  "the trip is — a single bare number is wrong.",
    },
    {
        "question": "How many days a year can I work from another country?",
        "expect": [["WRK-001 4.2"], ["WRK-001 4.3"]],
        "answer": "30 days in total, and no more than 20 in any single country. "
                  "Omitting the 20-day sub-limit is a failure.",
    },
    {
        "question": "How often can I be on call?",
        "expect": [["ENG-001 3.3"], ["POL-000 3.6"]],
        "answer": "At most one week in four. Must NOT say one week in three — "
                  "that is the superseded figure.",
    },

    # --- Tier 4: near-miss disambiguation ------------------------------------
    {
        "question": "I'm moving to Berlin. What will Meridian cover?",
        "expect": [["WRK-001 5.4"], ["HR-002 8.3"]],
        "answer": "If the employee initiated the move: nothing. No relocation "
                  "assistance, approval is still required first, and base salary "
                  "adjusts to the new zone. The USD 20,000 international "
                  "assistance applies only where Meridian initiates the move — "
                  "quoting it without that condition is a failure.",
    },
    {
        "question": "I'm working from Portugal for three weeks. What do I claim?",
        "expect": [["WRK-001 4.1", "WRK-001 4.5"]],
        "answer": "Nothing. Work-from-anywhere is entirely at the employee's "
                  "cost and business travel insurance does not cover it. Also "
                  "needs approval 21 days in advance. Must NOT apply travel per "
                  "diems or hotel caps.",
    },
    {
        "question": "Is Singapore Tier 1 or Zone 2?",
        "expect": [["HR-002 3.5"], ["FIN-001 5.1"]],
        "answer": "Both — they are two different systems. Salary Zone 2 and "
                  "travel Tier 1. Must NOT treat this as a contradiction.",
    },
    {
        "question": "When do my expense claims need to be in?",
        "expect": [["FIN-001 7.2"], ["HR-006 8.2"]],
        "answer": "30 days for travel expenses, 60 days for learning budget "
                  "claims. Two different deadlines.",
    },

    # --- Tier 5: exception handling ------------------------------------------
    {
        "question": "What laptop does a contractor get?",
        "expect": [["IT-001 5.1", "IT-001 5.2"]],
        "answer": "None. Contractors use their own device via a managed virtual "
                  "desktop; the only Meridian hardware they hold is a security "
                  "key. There is a >12-month exception. Must NOT answer from the "
                  "job-family laptop table.",
    },
    {
        "question": "Can I get business class to Singapore? I'm an IC6.",
        "expect": [["FIN-001 4.2"], ["ORG-002 2.3"]],
        "answer": "No. Business class requires M4/IC7 and above AND a flight "
                  "over 10 hours. IC6 maps to M3, not M4, so an IC6 does not "
                  "qualify on level regardless of duration.",
    },
    {
        "question": "I was rehired after two years away. Do I get my sabbatical "
                    "back?",
        "expect": [["HR-004 8.3"], ["HR-001 4.3"]],
        "answer": "No. Rehire starts a new continuous-service clock — back to "
                  "Tier A — and 61 new months are required, regardless of prior "
                  "service or a sabbatical already taken.",
    },
    {
        "question": "Am I paid overtime for incident work?",
        "expect": [["ENG-001 5.2"], ["HR-001 2.6"]],
        "answer": "Only if you are a non-exempt US employee, in which case "
                  "overtime is paid in addition to the stipend. Exempt US "
                  "employees get the stipend only; EU employees get compensatory "
                  "time off instead.",
    },
]

# Tier 6 — the handbook does not cover these. The correct behaviour is to say so
# and name who to ask, not to extrapolate from a similar policy. Scored
# separately: here a refusal is the right answer, so passing the cases above
# says nothing about passing these.
REFUSAL_CASES = [
    {
        "question": "What's the parental leave policy in Brazil?",
        "answer": "Should say the handbook does not cover Brazil — no Brazilian "
                  "legal entity exists. Must not extrapolate from another "
                  "country's policy.",
    },
    {
        "question": "How much equity does an IC5 get?",
        "answer": "Should decline to give a number. HR-002 §9 describes the "
                  "mechanism but publishes no amounts.",
    },
    {
        "question": "What's my salary band?",
        "answer": "Should say bands are not published in the handbook, and "
                  "direct the employee to Workday and their manager.",
    },
    {
        "question": "What's Meridian's stock price?",
        "answer": "Should say Meridian is privately held, so there is no stock "
                  "price.",
    },
    {
        "question": "Write me a Python script to sort a list.",
        "answer": "Should decline as off-topic and redirect to handbook "
                  "questions.",
    },
]