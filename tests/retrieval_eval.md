# Retrieval Evaluation Set

Questions for testing the Meridian Systems handbook bot, with the documents a correct
answer must draw on and the specific failure mode each one probes.

**This file lives outside `corpus/` on purpose — it must never be indexed.** It contains the
answers, so a bot that could retrieve it would score well for the wrong reason.

---

## Tier 1 — Single-hop (retrieval sanity check)

These should work as soon as the index builds. If they fail, the problem is chunking or
embedding, not reasoning.

| # | Question | Must cite | Correct answer |
|---|---|---|---|
| 1 | How many company holidays do employees in Ireland get? | HR-004 §2.1 | 10, plus 2 floating days (§2.2) |
| 2 | What's the 401(k) match? | HR-003 §4.2 | 100% up to 4%, per pay period, no year-end true-up |
| 3 | How long is a performance improvement plan? | HR-005 §5.2 | 60 days, extendable once by up to 30 |
| 4 | What laptop does a designer get? | IT-001 §3.1 | MacBook Pro 14", 24 GB |
| 5 | When must I report a lost laptop? | SEC-001 §7.1, IT-001 §8.1 | Within one hour, to `#security-incidents` |

---

## Tier 2 — Cross-document (the main event)

A correct answer requires pulling from **two or more documents**. A bot that retrieves only
the obvious document will produce a confidently incomplete answer.

### 6. "I've been here three years. How much PTO do I get?"
**Must cite:** HR-004 §3.1 **and** HR-001 §4.1
**Correct:** 20 days — three years' service is Tenure Tier B (25–60 months, HR-001 §4.1), and
Tier B accrues 20 days (HR-004 §3.1).
**Failure mode:** answering with the whole table instead of resolving the tier, or missing that
the tier definition lives in a different document entirely.

### 7. "I'm an engineer in Dublin going on call next week. What do I get paid for it?"
**Must cite:** ENG-001 §5.3 (**not** §5.2)
**Correct:** 12% of weekly base salary for primary. Plus compensatory time off 1:1 for
out-of-hours incident work, and an 11-hour rest period if night work exceeds 2 hours. **Not**
the USD 500 flat stipend, which is US/Canada only.
**Failure mode:** the single most important trap in the corpus. Retrieving §5.2 and answering
"$500" is confidently wrong. Watch whether the bot notices the country qualifier at all.

### 8. "Does my Irish pension contribution change as I stay longer?"
**Must cite:** HR-003 §5.2 **and** HR-001 §4.1
**Correct:** Yes — 5% / 7% / 9% by tenure tier, starting after 6 months. Requires resolving
the tier definition from HR-001.
**Failure mode:** stating the percentages without explaining what a "tier" is.

### 9. "My conference ticket was approved. Can I book flights?"
**Must cite:** HR-006 §5.1 **and** FIN-001 §3.2
**Correct:** No. Learning-budget approval does not authorize travel; the trip needs separate
pre-approval under FIN-001 §3.1. Both documents flag this explicitly as a common error.
**Failure mode:** answering yes, or answering from HR-006 alone.

### 10. "Who pays for my desk chair, monitor, and internet?"
**Must cite:** WRK-001 §6.3, IT-001 §4, HR-003 §8
**Correct:** Three separate budgets — chair from the home office stipend (USD 750 initial),
monitor from the IT peripherals allowance (USD 400), internet from the HR-003 §8 allowance
(USD 50/month). They cannot be pooled.
**Failure mode:** answering from one document and missing the other two.

---

## Tier 3 — Superseded values (does the bot check POL-000?)

The amendment log records changes that contradict the surrounding text. Each of these has a
plausible-but-stale wrong answer available in the corpus.

### 11. "How many PTO days can I carry into next year, and when do they expire?"
**Must cite:** HR-004 §4.2 and/or POL-000 §3.1
**Correct:** 10 days, expiring 30 June. **Stale wrong answer:** 5 days expiring 31 March.
**Note:** HR-004 §4.2 has already absorbed this amendment, so both sources agree. This tests
whether the bot handles a document that references its own amendment without getting confused.

### 12. "What's the meal per diem for a trip to London?"
**Must cite:** FIN-001 §5.1 and POL-000 §3.2
**Correct:** Depends on travel date — USD 95 to 31 March 2026, USD 110 from 1 April 2026.
The rate is set by date of travel, not date of claim.
**Failure mode:** giving one number without the date qualifier. A great answer asks when the
trip is, or states both.

### 13. "How many days a year can I work from another country?"
**Must cite:** WRK-001 §4.2, §4.3, POL-000 §3.3
**Correct:** 30 days total, but no more than 20 in any single country.
**Failure mode:** answering "30" and omitting the sub-limit — the sub-limit was deliberately
*not* changed by the amendment, so a bot that reads only the changelog gets it half right.

### 14. "How often can I be on call?"
**Must cite:** ENG-001 §3.3, POL-000 §3.6
**Correct:** Maximum one week in four. **Stale wrong answer:** one week in three.

---

## Tier 4 — Near-miss disambiguation

Two topics with heavy vocabulary overlap. Sloppy retrieval pulls the wrong one.

### 15. "I'm moving to Berlin. What will Meridian cover?"
**Must cite:** WRK-001 §5.4, HR-002 §8.3, and HR-002 §3.4
**Correct:** If employee-initiated: nothing — no relocation assistance, approval still required
first, and base salary adjusts to the new zone. Assistance (USD 20,000 international) applies
only where Meridian initiates the move.
**Failure mode:** retrieving FIN-001 (travel) and quoting per diems, or quoting the USD 20,000
without the company-initiated condition.

### 16. "I'm working from Portugal for three weeks. What do I claim?"
**Must cite:** WRK-001 §4.1, §4.5
**Correct:** Nothing. Work-from-anywhere is entirely at the employee's cost, and business
travel insurance does not cover it. Also needs approval 21 days in advance.
**Failure mode:** applying FIN-001 per diems and hotel caps — the vocabulary overlap
("working abroad", "days", "country") is very high.

### 17. "Is Singapore Tier 1 or Zone 2?"
**Must cite:** HR-002 §3.5 and FIN-001 §5.1
**Correct:** Both. Salary Zone 2 (HR-002 §3.3), travel Tier 1 (FIN-001 §5.1). Two different
systems that use similar-sounding names, flagged explicitly in HR-002 §3.5.
**Failure mode:** treating them as the same system and declaring a contradiction.

### 18. "When do my expense claims need to be in?"
**Must cite:** FIN-001 §7.2, and ideally HR-006 §8.2
**Correct:** 30 days for travel expenses; 60 days for learning budget claims. Different
deadlines, changed by POL-000 §3.9.

---

## Tier 5 — Exception handling

The general rule is easy to find; the exception is a sentence somewhere else.

### 19. "What laptop does a contractor get?"
**Must cite:** IT-001 §5.1, §5.2
**Correct:** None. Contractors use their own device via a managed virtual desktop. The only
Meridian hardware they hold is a security key (§5.3). There's a >12-month exception in §5.4.
**Failure mode:** answering from the IT-001 §3.1 job-family table.

### 20. "Can I get business class to Singapore?"
**Must cite:** FIN-001 §4.2, ORG-002 §2.3
**Correct:** Only at M4/IC7 and above, and only on flights over 10 hours — or for anyone
arriving under 12 hours before a customer commitment. Requires knowing IC7 maps to M4 but
IC6 does **not** (ORG-002 §2.3).
**Failure mode:** saying IC6 qualifies.

### 21. "I was rehired after two years away. Do I get my sabbatical back?"
**Must cite:** HR-004 §8.3, HR-001 §4.3, HR-007 §8.4
**Correct:** No. Rehire starts a new continuous-service clock — back to Tier A, and 61 new
months are needed for sabbatical regardless of prior service or a sabbatical already taken.

### 22. "Am I paid overtime for incident work?"
**Must cite:** ENG-001 §5.2, HR-001 §2.6
**Correct:** Only if you're a non-exempt US employee — then overtime is paid *in addition* to
the stipend. Exempt US employees get the stipend only. EU employees get compensatory time
off instead (§5.3).

---

## Tier 6 — Correct refusal

The bot should say the handbook doesn't cover it rather than inventing an answer.

| # | Question | Expected behaviour |
|---|---|---|
| 23 | What's the parental leave policy in Brazil? | No Brazilian entity exists (ORG-001 §2.3). Should say so, not extrapolate. |
| 24 | How much equity does an IC5 get? | HR-002 §9 describes the mechanism but publishes no amounts. Should decline to give a number. |
| 25 | What's my salary band? | HR-002 §3.1 — bands aren't published; directs to Workday and the manager. |
| 26 | What's Meridian's stock price? | Privately held (ORG-001 §2.2). Should refuse. |
| 27 | Write me a Python script to sort a list. | Off-topic; the system prompt should decline and redirect to handbook topics. |

---

## Suggested starter questions for the demo UI

Pick ones that fail visibly without good retrieval and are quick to verify:

1. *"I've been here three years — how much PTO do I get?"* (Q6 — cross-doc tier resolution)
2. *"I'm on call next week in Dublin. What am I paid?"* (Q7 — the EU/US trap)
3. *"My conference ticket is approved. Can I book flights now?"* (Q9 — the process trap)
4. *"What's the per diem for a trip to London in May?"* (Q12 — the superseded rate)

---

## Scoring notes

For each question, record: (a) did retrieval surface every required document; (b) was the
answer factually right; (c) were the citations right and specific to the section. It is
entirely possible to get (b) right with (a) wrong — a plausible answer from a single document
— which is why (a) is scored separately.
