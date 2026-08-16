---
doc_id: IT-001
title: Equipment, Provisioning, and IT Support
version: 4.3
effective: 2026-02-15
owner: IT Operations
---

# IT-001 — Equipment, Provisioning, and IT Support

## 1. Purpose

### 1.1 Scope
This document covers the hardware Meridian issues, the refresh cycle for each class of equipment, peripherals, mobile devices, provisioning and return, software installation, and how to get help.

### 1.2 Related Documents
Data handling rules that apply to every device are in SEC-001. Furniture and connectivity are not covered here: desk and chair come from the home office stipend (WRK-001 §6) and internet from the allowance in HR-003 §8.

### 1.3 Amendment Notice
Section 3 was amended effective 15 February 2026 to add a supported Linux option. See POL-000 §3.4.

## 2. Provisioning

### 2.1 Before the Start Date
IT ships equipment to arrive at least 2 business days before the start date, provided the hiring manager submits the equipment request at least 10 business days in advance. Late requests are the most common cause of a new hire without a laptop on day one.

### 2.2 Accounts
Accounts are created the day before the start date and activated on the start date. Access beyond the baseline set requires a request from the manager through the access system, subject to the approval matrix in SEC-001 §4.2.

### 2.3 Baseline Access
Email, calendar, Slack, the document system, the ticketing system, Workday, and the expense system are provisioned to every employee automatically. No access to customer data of any classification is provisioned by default.

## 3. Standard Equipment

### 3.1 Laptop by Job Family
Equipment standard is keyed to **job family**, not to job level and not to tenure.

| Job family | Standard machine |
| --- | --- |
| Engineering, Data, Security | MacBook Pro 14", 36 GB RAM |
| Product, Design | MacBook Pro 14", 24 GB RAM |
| Go-To-Market, Customer Experience, Finance, People | MacBook Air 15", 16 GB RAM |
| Platform and Infrastructure Engineering (on request) | Dell Latitude with Ubuntu LTS, 32 GB RAM |

*(The Ubuntu option was added by amendment on 15 February 2026 — POL-000 §3.4. Windows is not a supported employee platform; it is available only on managed lab hardware.)*

### 3.2 Refresh Cycle
Equipment is refreshed on a fixed schedule from the issue date, not on request. This schedule is also used for depreciated valuation when equipment is not returned (HR-007 §7.4).

| Item | Refresh interval |
| --- | --- |
| Laptop — Engineering, Data, Security, Platform | 36 months |
| Laptop — all other job families | 48 months |
| External monitor | 60 months |
| Docking station | 60 months |
| Mobile phone (on-call engineers only, §3.4) | 24 months |
| Security key | Replaced on failure or loss, no fixed interval |

### 3.3 Early Replacement
A machine may be replaced before its refresh date where it has a hardware fault that cannot be repaired economically, or where a documented change in role requires a different specification. Preference is not a qualifying reason.

### 3.4 Mobile Phones
Meridian issues a mobile phone only to employees on an active on-call rotation (ENG-001 §3) and to employees whose role requires a separate device for customer-facing communication. All other employees use a personal device with the managed work profile, and receive no phone stipend. A phone issued for on-call is returned when the employee leaves the rotation permanently, not between rotations.

## 4. Peripherals

### 4.1 Allowance
Each employee has a peripherals allowance of **USD 400** on joining, refreshed by a further USD 400 at each laptop refresh (§3.2).

### 4.2 What It Covers
External keyboard and mouse, headset, webcam, laptop stand, cables and adapters, and one external monitor where the employee does not have one from a previous allocation. Items purchased from this allowance are Meridian property and are returnable (HR-007 §7.1) — unlike home office furniture, which is not (WRK-001 §6.4).

### 4.3 Office Peripherals
Meridian offices provide monitors, keyboards, mice, and docking stations at every bookable desk. The peripherals allowance is intended for the home setup, not to duplicate what the office already has.

## 5. Contractors

### 5.1 No Company Hardware
Contractors (HR-001 §2.5) are **not** issued Meridian laptops, monitors, peripherals, or phones, and have no peripherals allowance, no home office stipend, and no internet allowance.

### 5.2 How Contractors Access Systems
Contractors use their own device to connect to a managed virtual desktop. All work is performed inside the virtual desktop; no Meridian data may be stored on the contractor's own device, and the virtual desktop blocks clipboard transfer and local drive redirection.

### 5.3 Security Keys
Contractors requiring access to systems that mandate hardware-key authentication (SEC-001 §4.4) are issued a key, which is returnable at the end of the engagement. This is the only Meridian hardware a contractor holds.

### 5.4 Exception
A contractor engaged for more than 12 months on a full-time-equivalent basis may be issued a managed laptop with the approval of the functional executive and the Security team. This is an exception and requires renewal at each contract extension.

## 6. Return and Disposal

### 6.1 On Termination
Return obligations, the 10-business-day deadline, and non-return charges are in HR-007 §7. Do not wipe or factory-reset a device before returning it; IT performs the wipe as part of the documented chain of custody required by SEC-001 §6.3.

### 6.2 On Refresh
The replaced machine is returned within 10 business days of receiving the replacement. IT will not process a further request from an employee holding an unreturned prior device.

### 6.3 Disposal
Retired devices are wiped to the standard in SEC-001 §6.3 and either redeployed as loan stock or disposed of through a certified recycler with a certificate of destruction retained.

### 6.4 Employee Purchase
Employees may purchase their retired laptop at the depreciated value under §3.2, subject to the device having been wiped and re-imaged by IT first. Devices that held Restricted data are not available for purchase.

## 7. Software

### 7.1 Approved Catalogue
Software available for self-service installation is listed in the internal catalogue. Anything in the catalogue may be installed without a request.

### 7.2 Anything Else
Software outside the catalogue requires an IT request and, where it processes company or customer data, a Security review. Installing unapproved software with administrative rights is a breach of HR-008 §5.2.

### 7.3 Administrative Rights
Engineering, Data, Security, and Platform job families have standing local administrative rights on their machines. Other job families receive time-limited elevation on request.

### 7.4 Licence Ownership
Software licences purchased by Meridian remain Meridian property. Do not use a personal licence for company work, or a company licence for personal work.

## 8. Loss, Damage, and Theft

### 8.1 Reporting
Report a lost or stolen device **immediately** to IT and, in parallel, to Security under SEC-001 §7.1, which requires notification within one hour. IT triggers a remote lock and wipe.

### 8.2 Replacement
A lost or stolen device is replaced at no cost to the employee. Meridian does not charge employees for lost equipment; the security response matters more than the hardware, and charging for loss encourages under-reporting.

### 8.3 Damage
Accidental damage is repaired or replaced at no cost. Repeated damage is a conversation with the manager, not a charge.

## 9. Support

### 9.1 Getting Help
Raise a ticket in the IT portal or use the `#it-help` channel. Target first response is 4 working hours for standard issues and 1 hour for anything blocking work entirely.

### 9.2 Loan Equipment
Every office keeps loan laptops and travel adapters. Loans over 5 business days require a ticket.

### 9.3 Out of Hours
IT does not operate an out-of-hours desk. Employees on an active on-call rotation have an escalation path to the on-call platform engineer for infrastructure access issues only; this is not general IT support.
