---
doc_id: SEC-001
title: Security and Data Handling
version: 6.2
effective: 2026-01-01
owner: Security
---

# SEC-001 — Security and Data Handling

## 1. Purpose

### 1.1 Scope
This document sets the security obligations of every person with access to Meridian systems — employees, contractors, interns, and third parties under contract. It applies in every location and to every device used for Meridian work, whether company-owned or personal.

### 1.2 Non-Negotiable
Unlike most policies in this handbook, the requirements here do not admit manager discretion. A manager cannot approve an exception to this document. Exceptions are granted only by the Security team through the documented exception process (§9).

## 2. Accounts and Authentication

### 2.1 Single Sign-On
All access is through the company identity provider. Systems that cannot integrate with SSO require a Security exception and are not permitted to hold Confidential or Restricted data.

### 2.2 Multi-Factor Authentication
MFA is mandatory on every account, with no exceptions and no opt-out period. SMS-based codes are not an accepted factor.

### 2.3 Password Manager
1Password is provided to every employee and contractor and must be used for any credential not covered by SSO. Credentials must never be stored in documents, spreadsheets, code, ticket comments, or chat messages.

### 2.4 Shared Credentials
Shared accounts are prohibited. Where a system genuinely cannot support individual accounts, the credential is held in a shared 1Password vault with access logged, and the arrangement is registered with Security and reviewed quarterly.

## 3. Data Classification

### 3.1 Public
Information Meridian has deliberately published. Marketing material, published documentation, the public website. No handling restrictions.

### 3.2 Internal
Default classification for company information not intended for publication. Internal roadmaps, team documents, most Slack conversation, aggregate metrics. May be shared freely inside Meridian; may not be shared outside without approval.

### 3.3 Confidential
Information whose disclosure would cause material harm. Unreleased financials, personnel files, salary data, security findings, contract terms, customer lists, and source code. Access is granted on a need-to-know basis, and sharing outside Meridian requires an NDA and owner approval.

### 3.4 Restricted
The highest classification. Customer data held in or transiting Meridian systems, production credentials and secrets, encryption keys, and personal data of customers' end users. Access requires documented business justification, approval under §4.2, and hardware-key authentication (§4.4). Restricted data must never leave the controlled environment described in §4.3.

### 3.5 Labelling
Documents holding Confidential or Restricted material must be labelled in the title or header. When in doubt, classify upward; a wrongly-Confidential document is an inconvenience, a wrongly-Internal customer record is an incident.

## 4. Customer Data

### 4.1 The Governing Rule
**Customer data is never copied to a local disk, personal cloud storage, or an unapproved tool.** This applies to exports, screenshots, query results, CSV downloads, and log extracts. There is no "just for debugging" exception.

### 4.2 Access Approval
Access to Restricted data requires: a stated business justification recorded in the access system, approval by the data owner, and approval by the employee's manager. Access is granted for a defined period, defaulting to 90 days, and expires automatically.

### 4.3 The Atlas Sandbox
Investigation of customer data is performed in the Atlas Sandbox, a controlled environment with session recording, no egress to the public internet, and no clipboard or file transfer to the local machine. If a task appears to require taking customer data out of the Sandbox, the task is wrong; raise it with Security rather than working around the control.

### 4.4 Hardware Keys
Access to production systems holding Restricted data requires a FIDO2 hardware security key. Software authenticators are not sufficient for this tier. Keys are issued by IT (IT-001 §3.2) and to contractors under IT-001 §5.3.

### 4.5 Quarterly Access Review
Every access grant to Confidential and Restricted systems is reviewed quarterly by the data owner. Access not affirmatively re-approved is removed automatically. Managers receive a review list; failure to complete a review within 10 business days results in the access being revoked by default rather than retained by default.

### 4.6 Access on Departure
Restricted access is revoked when notice is given, not on the last day. See HR-007 §6.2.

## 5. Devices and Tools

### 5.1 Device Requirements
Every device used for Meridian work must have full-disk encryption enabled, automatic screen lock at 5 minutes or less, the current supported operating system version, and the management agent installed. Devices failing these checks are blocked from SSO automatically.

### 5.2 Personal Devices
A personal phone may access Meridian email and Slack through the managed work profile. A personal computer may not be used for Meridian work at all, except by contractors through the virtual desktop described in IT-001 §5.2.

### 5.3 Artificial Intelligence Tools
Approved AI assistants may be used for Meridian work. **Confidential data may be entered only into tools on the approved list**, which is maintained by Security and reflects the contractual data-handling terms in place. **Restricted data — including any customer data — must never be entered into any AI tool, approved or not.** Generated output is the employee's responsibility to review (HR-008 §5.3).

### 5.4 Personal Cloud Storage
Personal Dropbox, Google Drive, iCloud, and equivalents must not hold Meridian data of any classification, including Internal.

### 5.5 Removable Media
USB mass storage is blocked by policy on managed devices. Requests for exceptions are handled under §9.

## 6. Handling and Retention

### 6.1 Sharing Externally
External sharing of Confidential material requires an executed NDA and data owner approval, and must use the approved secure sharing mechanism rather than an email attachment.

### 6.2 Retention
Data is retained per the retention schedule maintained by Legal. Employees must not create parallel copies that escape the schedule — a personal archive of customer tickets is a compliance failure even if it is well-intentioned.

### 6.3 Destruction
Devices and media are wiped to NIST 800-88 Purge standard before redeployment or disposal, by IT, with a record retained (IT-001 §6.3). This is why employees must not wipe returned devices themselves (HR-007 §7.3) — a self-wipe breaks the documented chain of custody.

## 7. Incidents

### 7.1 Report Within One Hour
Report a suspected security incident to the `#security-incidents` Slack channel, or to `security@meridiansystems.example` if Slack is unavailable, **within one hour of becoming aware of it**. This is mandatory, not discretionary, and applies outside working hours and while travelling.

### 7.2 What Counts as an Incident
A lost or stolen device; a credential that may have been exposed; a phishing message that was clicked or replied to; customer data sent to the wrong recipient; an unexpected access prompt; a suspicion that any system is behaving as though someone else is using your account; discovery of customer data in a place it should not be.

### 7.3 No Blame for Reporting
An employee who reports promptly is never disciplined for the underlying mistake, including for clicking a phishing link or losing a laptop. Late reporting and non-reporting are the disciplinary matters. This mirrors the equipment loss stance in IT-001 §8.2 and exists for the same reason.

### 7.4 Do Not Investigate Alone
Do not attempt to remediate, delete evidence, or contact an external party. Preserve the state of the system and let the incident responders work.

### 7.5 Relationship to Engineering Incidents
A **security** incident is reported under this section. An **availability or reliability** incident is declared and run under ENG-001 §2. An event may be both, in which case both processes run in parallel and the security process takes precedence on any question of disclosure or external communication.

## 8. Privacy and Regulatory

### 8.1 Data Controller
Meridian Systems Ireland Ltd. is the data controller for EEA and UK personal data. Meridian Systems, Inc. is the controller elsewhere. Data subject requests are routed to `privacy@meridiansystems.example` and must be acknowledged within 5 business days.

### 8.2 Subprocessors
No new subprocessor may be engaged to process customer data without Security and Legal review and an update to the published subprocessor list, which requires customer notice periods to be observed.

### 8.3 Cross-Border Transfer
Transfers of personal data out of the EEA rely on the standard contractual clauses in the customer agreement. Do not build a system or a workflow that moves customer personal data across a border without Security review.

## 9. Exceptions

### 9.1 Process
An exception request states the control to be excepted, the business need, the duration, and the compensating control. It is approved by the Head of Security, or by the CTO where the Head of Security is conflicted.

### 9.2 Duration
Exceptions are time-limited, to a maximum of 12 months, and expire automatically. There are no standing exceptions.

### 9.3 Register
All exceptions are recorded in the exception register and reviewed quarterly by the leadership team.

## 10. Training

### 10.1 Onboarding
Security training is completed within the first 10 business days of employment. Access to Confidential systems is contingent on completion.

### 10.2 Annual Refresher
An annual refresher is mandatory for all employees and contractors. Non-completion within 30 days of the deadline results in suspension of access to Confidential and Restricted systems until completed.

### 10.3 Phishing Simulation
Meridian runs periodic phishing simulations. Results are used for training, not for discipline; there is no individual reporting to managers of simulation failures.
