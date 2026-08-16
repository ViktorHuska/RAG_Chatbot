---
doc_id: ENG-001
title: On-Call and Incident Response
version: 5.0
effective: 2026-01-01
owner: Engineering Operations
---

# ENG-001 — On-Call and Incident Response

## 1. Purpose

### 1.1 Scope
This document defines how Meridian runs production on-call, how incidents are classified and managed, how on-call participation is compensated, and how incidents are reviewed. It applies to engineering teams that own production services and to anyone participating in an incident response.

### 1.2 Related Documents
On-call compensation is defined **here**, not in HR-002; HR-002 §6 exists only to point at this section. Security incidents follow SEC-001 §7 rather than this document; see §2.5. Phones issued for on-call are covered by IT-001 §3.4.

## 2. Incident Classification

### 2.1 Severity Levels

| Severity | Definition | Acknowledgement target | Update cadence |
| --- | --- | --- | --- |
| Sev1 | Complete loss of a core service, or any confirmed data loss, for multiple customers | 15 minutes | Every 30 minutes |
| Sev2 | Major degradation, or complete loss for a single significant customer, with no workaround | 30 minutes | Every 60 minutes |
| Sev3 | Partial degradation with a workaround, or a defect affecting a non-core path | 2 business hours | Daily |
| Sev4 | Minor issue, cosmetic defect, or a question. Not an incident; handled as a normal ticket | Next business day | None |

### 2.2 Who Declares
Anyone may declare an incident at any severity. Under-declaring is a bigger risk than over-declaring; the incident commander can downgrade at the first assessment without ceremony.

### 2.3 Roles
Every Sev1 and Sev2 has an **incident commander**, who coordinates and is explicitly not expected to debug, and a **communications lead** for Sev1, who owns customer and internal updates. The commander may be any trained engineer and does not need to be the most senior person present.

### 2.4 Customer Communication
Sev1 incidents are posted to the public status page within 30 minutes of declaration. Only the communications lead or Customer Experience leadership posts externally. Individual engineers must not discuss an active incident with customers directly.

### 2.5 Security Incidents
A suspected security incident is reported under SEC-001 §7.1 within one hour, in addition to any severity declared here. Where an event is both a reliability and a security incident, both processes run and SEC-001 governs anything to do with disclosure.

## 3. Rotation Structure

### 3.1 Shape
Each participating team runs a **primary** and a **secondary** rotation. The secondary is escalated to when the primary does not acknowledge within the target in §2.1, and acts as the escalation point for judgment calls.

### 3.2 Shift Length
A rotation shift runs one week, from **Monday 10:00 local time to the following Monday 10:00 local time**. Handover is a documented conversation, not a calendar event that happens automatically.

### 3.3 Frequency Cap
No engineer may be scheduled for primary on-call more than **one week in four**. A team that cannot meet this cap does not have enough participants and must escalate to Engineering Operations rather than quietly running a tighter rotation.

### 3.4 Eligibility
Engineers join a rotation only after completing on-call onboarding and shadowing at least one full shift. Employees within their probationary period (HR-001 §3) do not carry primary on-call. Employees on an active performance improvement plan remain eligible (HR-005 §5.4).

### 3.5 Coverage Requirements
Follow-the-sun coverage is used where a team spans regions. Where a team is in a single region, out-of-hours coverage is provided by that team, which is the situation the compensation in §5 is designed to address.

### 3.6 Swaps
Shifts may be swapped by mutual agreement with 48 hours' notice, recorded in the scheduling tool. The compensation in §5 follows the engineer who actually holds the shift, not the one originally scheduled.

## 4. Obligations While On Call

### 4.1 Availability
The primary must be reachable and able to reach a working environment with connectivity within the acknowledgement target for the highest severity their service can generate. In practice this means being within reach of a laptop and a stable connection.

### 4.2 Constraints
An on-call engineer must not be in a position where they cannot respond — this includes air travel longer than the acknowledgement window, and it includes the alcohol expectations that follow from HR-008 §7.1. Plan the week accordingly, or swap the shift under §3.6.

### 4.3 Interaction With Leave
On-call and approved paid time off are mutually exclusive. A shift overlapping approved leave must be swapped; leave is not cancelled to preserve a rotation. An engineer called during approved leave has had their leave interrupted, and the day is credited back under HR-004 §3.

### 4.4 Interaction With Work From Anywhere
An engineer may not hold primary on-call while working from another country under WRK-001 §4, because the overlap and reachability assumptions of the rotation no longer hold.

### 4.5 Outside Employment
Outside work that conflicts with on-call availability is not permitted (HR-008 §3.4).

## 5. On-Call Compensation

### 5.1 The Rules Differ by Entity
On-call compensation is **not uniform across Meridian**. The U.S. and Canadian entities use a flat weekly stipend. The Irish and German entities use a percentage-of-salary allowance with additional statutory rest entitlements. This is a deliberate consequence of the ORG-001 §4.4 value; do not assume the arrangement described to you by a colleague in another region applies to you.

### 5.2 United States and Canada

| Rotation | Payment per week held |
| --- | --- |
| Primary | USD 500 |
| Secondary | USD 250 |

The stipend is paid for holding the rotation, whether or not any incident occurs. **Non-exempt** U.S. employees (HR-001 §2.6) are additionally paid overtime at the applicable rate for hours actually worked on incidents outside their scheduled hours; the stipend does not substitute for that. Exempt employees receive the stipend only.

### 5.3 Ireland and Germany
Employees of Meridian Systems Ireland Ltd. and Meridian Systems GmbH receive an on-call **allowance expressed as a percentage of weekly base salary**, not a flat fee:

| Rotation | Allowance |
| --- | --- |
| Primary | 12% of weekly base salary |
| Secondary | 6% of weekly base salary |

In addition, and separately from the allowance:

- Where incident work between 22:00 and 06:00 exceeds **2 hours** in a single night, the engineer takes an **11-hour uninterrupted rest period** before resuming work, and any scheduled working time falling within that rest period is paid.
- Incident work performed outside normal working hours is credited as **compensatory time off** at 1:1, taken within the following 30 days, in addition to the allowance and separate from the PTO entitlement in HR-004 §3.
- The German arrangement is subject to the works council agreement, which prevails over this document where it differs.

### 5.4 Singapore
Employees of the APAC entity receive a flat SGD 400 per week for primary and SGD 200 for secondary, with no compensatory time off arrangement.

### 5.5 Who Is Not Compensated
Managers at M2 and above do not receive on-call compensation for escalation availability, which is considered part of the role. Engineers who volunteer for an incident they were not on call for are not compensated under this section, though the compensatory time off in §5.3 applies in the EU entities to any out-of-hours incident work regardless of rotation status.

### 5.6 Payment Timing
On-call compensation is submitted by Engineering Operations from the rotation record and paid in the second pay run of the following month (HR-002 §6.2).

## 6. During an Incident

### 6.1 Channel Discipline
Every incident gets a dedicated channel. Status, current hypothesis, and next action are posted in the channel, not held in someone's head. Side conversations in direct messages are the main cause of duplicated and contradictory remediation.

### 6.2 Mitigate First
Restore service first; find the root cause second. A rollback that works is better than a fix that is elegant.

### 6.3 Escalation
Escalate to the secondary at the acknowledgement target, to the service owner at 60 minutes without progress on a Sev1, and to the functional executive at 3 hours on an unresolved Sev1.

### 6.4 Stand Down
The incident commander declares the incident resolved and states in the channel what remains outstanding as follow-up work.

## 7. Incident Review

### 7.1 When Required
A written review is required for every Sev1 and Sev2. Sev3 incidents get a review at the service owner's discretion.

### 7.2 Deadline
The review is published within **5 business days** of the incident being resolved.

### 7.3 Blameless
Reviews describe what the system allowed to happen, not who made a mistake. Naming an individual as a cause is a defect in the review, not a finding. This is the ORG-001 §4.1 and §4.2 values made operational.

### 7.4 Content
Timeline, customer impact quantified, contributing factors, what went well, what was luck rather than design, and action items with named owners and dates.

### 7.5 Action Items
Action items from a Sev1 are tracked to completion and reviewed monthly by Engineering Operations. An action item that has slipped twice is escalated to the functional executive.

## 8. On-Call Health

### 8.1 Alert Budget
A rotation that pages the primary more than **5 times per week outside working hours**, averaged over a quarter, is considered unhealthy. The team must then prioritize reliability work over feature work until the rate is back within budget.

### 8.2 Review Cadence
Engineering Operations reviews paging volume, acknowledgement times, and rotation frequency quarterly, and reports to the engineering leadership team.

### 8.3 Raising Concerns
An engineer who believes a rotation is unsustainable raises it with their manager and, if unresolved, with Engineering Operations directly. This is explicitly not a performance conversation.
