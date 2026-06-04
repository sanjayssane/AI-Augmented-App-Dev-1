# Product Requirements Document
## MCQ Online Test Platform
### Role-Based Examination System with Examiner & Examinee Portals

---

| Field | Details |
|---|---|
| **Document Version** | 2.1 |
| **Status** | Revised — Gap Closure & API Contracts |
| **Date** | June 3, 2026 |
| **Prepared For** | Development Team |
| **Classification** | Internal |
| **Standards Applied** | WCAG 2.1 AA · GDPR (Regulation EU 2016/679) · OWASP Top 10 (2021) · OWASP ASVS L2 |

---

> **Architect's Note — v2.1 Changes**
>
> This revision closes product, security, and operational gaps identified in the v2.0 review. Additions include: **Exam Session Rules** (§3.6), clarified Examinee entry/resume and PRN retake policy, **`SessionQuestion`** data model, **`is_correct` computation policy**, **Technology Stack** (§9.5), **REST API contracts** (§9.6–9.7), deployment/data-residency guidance, GDPR process deliverables, load-test and DR criteria, and expanded acceptance criteria. Session authentication is specified as **opaque server-side sessions** (not stateless JWT).
>
> v2.0 incorporated OWASP, GDPR, WCAG, audit logging, and the revised data model from the initial architect review.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [User Roles & Hierarchy](#2-user-roles--hierarchy)
3. [Functional Requirements](#3-functional-requirements) — includes [§3.6 Exam Session Rules](#36-exam-session-rules)
4. [Security Requirements — OWASP](#4-security-requirements--owasp-top-10-2021)
5. [Privacy & Data Protection — GDPR](#5-privacy--data-protection--gdpr)
6. [Accessibility Requirements — WCAG 2.1 AA](#6-accessibility-requirements--wcag-21-aa)
7. [Audit, Logging & Monitoring](#7-audit-logging--monitoring)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [System Architecture Overview](#9-system-architecture-overview) — includes [§9.5 Stack](#95-technology-stack), [§9.6 API](#96-rest-api-contracts), [§9.7 Errors](#97-api-error-catalogue)
10. [User Flows](#10-user-flows)
11. [Assumptions & Constraints](#11-assumptions--constraints)
12. [Out of Scope](#12-out-of-scope-v10)
13. [Acceptance Criteria](#13-acceptance-criteria)
14. [Revision History](#14-revision-history)

**Appendices (within §9):** [9.5 Technology Stack](#95-technology-stack) · [9.6 REST API Contracts](#96-rest-api-contracts) · [9.7 API Error Catalogue](#97-api-error-catalogue)

---

## 1. Introduction

### 1.1 Purpose

This Product Requirements Document (PRD) defines the functional and non-functional requirements for the MCQ Online Test Platform — a web-based application that enables structured multiple-choice question examinations. The document serves as the authoritative specification for design, development, and quality assurance teams.

### 1.2 Project Overview

The MCQ Online Test Platform is a role-based examination system supporting two distinct user roles: **Examinee** and **Examiner**. The platform allows Examinees to register, attempt a 50-question MCQ test, navigate freely between questions, and receive a final score upon submission. Examiners have administrative privileges to manage the question bank — adding, editing, and deleting questions — as well as access to all recorded Examinee responses.

This system processes personal data (name and PRN) and must be designed with **Privacy by Design** (GDPR Article 25), **Security by Design** (OWASP ASVS), and **Accessibility by Design** (WCAG 2.1 AA) as first-class architectural principles — not afterthoughts.

### 1.3 Scope

The platform will encompass the following core capabilities:

- User registration and role-based authentication (Examiner / Examinee)
- A structured 50-question MCQ test interface for Examinees
- Non-disclosed answer feedback during the test — no right/wrong hints while the test is active
- Bidirectional question navigation (Next / Previous) with full response editability
- Score computation and display upon test submission
- Persistent, GDPR-compliant storage of every Examinee's responses for post-test review
- A question management console exclusively for Examiners
- Immutable audit logging of all administrative and security-relevant actions
- Full WCAG 2.1 AA accessibility compliance across all interfaces
- A versioned **REST API** with OpenAPI 3.1 documentation (§9.6–9.7)

### 1.4 Definitions and Acronyms

| Term | Definition |
|---|---|
| **MCQ** | Multiple Choice Question |
| **PRN** | Permanent Registration Number — unique identifier for each Examinee |
| **Examiner** | Privileged user role with authority to manage the question bank and view all results |
| **Examinee** | Standard user role that takes the test |
| **Question Bank** | Repository of all MCQ items managed by the Examiner |
| **Session** | An active test attempt by an Examinee from start to End Test |
| **Score** | Total marks awarded; 1 mark per correct answer, maximum 50 |
| **PII** | Personally Identifiable Information (PRN, Name) |
| **GDPR** | General Data Protection Regulation (EU) 2016/679 |
| **OWASP** | Open Web Application Security Project |
| **ASVS** | Application Security Verification Standard (OWASP) |
| **WCAG** | Web Content Accessibility Guidelines (W3C) |
| **CSRF** | Cross-Site Request Forgery |
| **XSS** | Cross-Site Scripting |
| **IDOR** | Insecure Direct Object Reference |
| **CSP** | Content Security Policy |
| **HSTS** | HTTP Strict Transport Security |
| **JWT** | JSON Web Token |
| **MFA** | Multi-Factor Authentication |
| **DPA** | Data Processing Agreement |
| **SessionQuestion** | Immutable row binding one question (and version) to a test session at a fixed display position (1–50) |
| **LIA** | Legitimate Interests Assessment (GDPR Article 6(1)(f) supporting documentation) |
| **DPIA** | Data Protection Impact Assessment (GDPR Article 35) |
| **RTO / RPO** | Recovery Time Objective / Recovery Point Objective (disaster recovery) |
| **Problem Details** | RFC 7807 `application/problem+json` error response format |

---

## 2. User Roles & Hierarchy

The platform enforces a two-tier role hierarchy. Each role has distinct access privileges and capabilities. **All role enforcement must be performed server-side** — client-side role checks are informational only and must never be relied upon for access control (OWASP A01).

```
┌─────────────────────────────────────────────┐
│                  EXAMINER                   │
│         (Administrative Role)               │
│                                             │
│  • Manage question bank (Add/Edit/Delete)   │
│  • View all examinee records & scores       │
│  • Cannot take the test                     │
│  • All actions are audit-logged             │
└──────────────────────┬──────────────────────┘
                       │ manages / views
                       ▼
┌─────────────────────────────────────────────┐
│                  EXAMINEE                   │
│             (Test-Taker Role)               │
│                                             │
│  • Register with PRN + Name                 │
│  • Attempt the 50-question MCQ test         │
│  • Review own submitted responses only      │
│  • Cannot access other examinees' data      │
└─────────────────────────────────────────────┘
```

### 2.1 Examiner (Administrative Role)

The Examiner is the privileged administrator of the test platform, responsible for maintaining the integrity and content of the question bank.

**Examiner privileges include:**

- Full CRUD access to the question bank (Create, Read, Update, Delete questions)
- View all recorded Examinee responses and test attempts
- Access to score records across all Examinees
- Cannot take the test in the Examiner role

**Authorization enforcement:**

- Every API endpoint serving Examiner functions must verify the `EXAMINER` role claim on the server before processing the request
- A valid Examiner session must never grant access to Examinee test endpoints and vice versa

### 2.2 Examinee (Test-Taker Role)

The Examinee is the standard user who registers with personal details and takes the MCQ test.

**Examinee capabilities include:**

- Registration using Permanent Registration Number (PRN) and Name
- Attempt the 50-question MCQ test
- Navigate between questions in any order
- Modify responses before final submission
- View their own final score after clicking End Test
- Review **only their own** submitted responses post-test

**Authorization enforcement:**

- All response and session endpoints must validate that the requesting Examinee's session ID matches the resource being accessed (IDOR protection — OWASP A01)
- An Examinee must never be able to retrieve another Examinee's responses, even with a valid session token

---

## 3. Functional Requirements

### 3.1 User Registration & Authentication

#### 3.1.1 Examinee Registration

Upon accessing the platform, an Examinee must complete a registration form before starting the test.

**Mandatory fields:**

- **Permanent Registration Number (PRN)** — alphanumeric, max 20 characters, regex-validated
- **Full Name** — text, max 100 characters, trimmed

**Validation rules:**

- PRN is non-empty and conforms to the defined alphanumeric format
- Name is non-empty after whitespace trimming
- A duplicate PRN for an already-completed test session returns **409 CONFLICT** with a generic message when retake is disabled (default); no other Examinee data is exposed (see §3.1.5)

**Privacy notice (GDPR Article 13):**

- A concise privacy notice must be displayed at registration stating: what data is collected (PRN, Name), the purpose (examination administration), the retention period, and the Examinee's rights
- The Examinee must acknowledge the notice before proceeding (checkbox or equivalent)

#### 3.1.2 Role Selection at Login

The login/entry screen shall present the user with a role selection:

- **Login as Examiner** — requires username + password (`POST /api/v1/auth/examiner/login`)
- **Enter as Examinee** — single form: PRN, Name, privacy acknowledgement (`POST /api/v1/auth/examinee/entry`); automatically resumes an ACTIVE session or starts a new one per §3.1.5

#### 3.1.3 Examiner Authentication

Examiner login shall be protected by username and password.

**Requirements:**

- Passwords stored using **bcrypt** with a minimum cost factor of **12** (or Argon2id with minimum m=19456, t=2, p=1 — OWASP ASVS 2.4.1)
- Login endpoint must enforce **rate limiting**: maximum 5 failed attempts per account per 15-minute window, followed by a temporary lockout (OWASP A07)
- After lockout, a cooldown period of at least 15 minutes must pass before further attempts are accepted
- Error messages must use a **generic response**: *"Invalid username or password"* — never reveal which field is incorrect (OWASP A07)
- Session tokens must be issued post-authentication and must be invalidated on logout (no re-use)

#### 3.1.4 Session Management

- All authenticated sessions (both roles) shall use **opaque server-side session IDs** transmitted via **HttpOnly, Secure, SameSite=Strict cookies** — never in `localStorage` (OWASP A07). See §3.1.4 and §9.5.
- Examiner session token expiry: **60 minutes** of inactivity
- Examinee session token expiry: **4 hours** (to accommodate long test sessions) or until End Test, whichever comes first
- **Concurrent sessions:** By default, a new Examiner login invalidates all prior active sessions for that account (see §4.7). For Examinees, only **one ACTIVE `TestSession` per `user_id`** is permitted; a second browser tab receives the same session via the cookie, and concurrent answer writes are resolved with **last-write-wins** per `question_id` using `If-Match` / `updated_at` (see §9.6.4).
- Session fixation must be prevented: a new session token must be issued immediately after login
- **Authentication mechanism (v2.1):** Use **opaque server-side session IDs** stored in Redis (or the primary database) and transmitted via HttpOnly cookies. Stateless JWTs are **not** used for session management, to satisfy logout invalidation and concurrent-session policies.

#### 3.1.5 Examinee Entry, Registration, and Resume

Examinee entry is a **single unified flow** (`POST /api/v1/auth/examinee/entry`) that handles registration, login, resume, and retake policy in one server decision:

| Server state for PRN | Name match? | Privacy ack | Result |
|---|---|---|---|
| No user exists | — | Required | Create `User` + new `TestSession` with 50 `SessionQuestion` rows |
| User exists, ACTIVE session | Must match stored name (case-insensitive trim) | Required on first entry only per device if not stored | Return existing ACTIVE session (resume) |
| User exists, COMPLETED session, retake **disabled** (default) | Must match | Required | `409 CONFLICT` — generic message: *"This registration number has already completed the test."* |
| User exists, COMPLETED session, retake **enabled** (institution config) | Must match | Required | Create new `TestSession`; prior attempts retained |

**Identity assurance (v1.0 risk acceptance):** Examinee authentication relies on **PRN + Name** only. This is suitable for low-stakes or proctored classroom use. The institution must document this limitation in its LIA/DPIA. v2 may add institution-issued access codes or SSO.

#### 3.1.6 Examiner Account Provisioning

- The **first Examiner** account is created via a one-time **bootstrap** command or environment-seeded credentials rotated on first login (§4.5).
- Additional Examiner accounts are created only by an authenticated Examiner via `POST /api/v1/examiner/users/examiners` (see §9.6.8).
- **Password policy:** minimum 12 characters; at least one uppercase, one lowercase, one digit; maximum 128 characters; checked server-side on create and password change.
- Password reset remains out of scope (§12); administrators deactivate compromised accounts (`PATCH .../examiners/{id}` with `is_active: false`) and issue new credentials out of band.

---

### 3.2 Test Interface (Examinee)

#### 3.2.1 Test Structure

- The test shall consist of **exactly 50 questions**
- Each question shall be of Multiple Choice (single correct answer) format
- Each question shall have **four answer options** labelled A, B, C, D
- Questions shall be presented **one at a time**
- Question text and options must be **HTML-encoded on output** to prevent stored XSS if an Examiner has injected script content (OWASP A03)

#### 3.2.2 Question Display

For each question, the interface shall clearly display:

- Question number (e.g., *Question 7 of 50*)
- Question text
- Four answer options as **radio buttons** with associated `<label>` elements explicitly linked via `for`/`id` attributes (WCAG 1.3.1, 4.1.2)
- Current selection highlighted and pre-filled if the question was previously answered
- The entire radio button group must be wrapped in a `<fieldset>` with a descriptive `<legend>` (WCAG 1.3.1)

#### 3.2.3 Navigation Controls

Each question screen shall include two navigation buttons:

| Button | Behaviour | Disabled State |
|---|---|---|
| **Previous** | Navigates to the immediately preceding question | Visible but `aria-disabled="true"` on Question 1; must still be keyboard-focusable (WCAG 2.1.1) |
| **Next** | Navigates to the immediately following question | Visible but `aria-disabled="true"` on Question 50; must still be keyboard-focusable (WCAG 2.1.1) |

> ⚠️ **Accessibility Note:** Disabled buttons must remain in the tab order and must announce their disabled state to screen readers via `aria-disabled="true"`. Using the HTML `disabled` attribute removes the element from the tab order and is not permitted here.

Navigation shall **not** submit or lock any answer. The Examinee may navigate freely between all 50 questions at any point during the test.

Focus must be programmatically managed on question load: focus shall move to the question heading or the question container on each navigation action (WCAG 2.4.3).

#### 3.2.4 Response Editability

- The Examinee shall be able to change their answer to **any question at any time** before clicking End Test
- Revisiting a previously answered question shall display the currently selected answer pre-filled and allow overwriting it
- Response updates must be persisted server-side immediately (auto-save on selection) to guard against data loss from accidental browser closure

#### 3.2.5 No Real-Time Feedback

> ⚠️ **Critical Rule:** The system shall **NOT** display whether an answered question is correct or incorrect during the test. No colour coding, icons, messages, or ARIA announcements shall indicate answer correctness until after the test is ended. This rule applies to all 50 questions throughout the entire test session.

This must also be enforced at the **API level** — the response endpoint must never return `is_correct` data to an Examinee during an active session.

#### 3.2.6 Progress Indicator

The interface shall display a progress summary showing the number of questions answered vs. total (e.g., *32 / 50 Answered*).

- The progress indicator must have a text equivalent readable by screen readers (WCAG 1.1.1, 1.3.1)
- It must not rely solely on colour to convey status (WCAG 1.4.1)
- An optional question navigator panel may indicate which questions have been answered and which remain unattempted, using both colour **and** a visible symbol (e.g., a tick or dot) to differentiate states

#### 3.2.7 End Test

An **End Test** button shall be prominently and persistently visible throughout the test. Upon clicking:

1. A confirmation **modal dialog** shall appear asking the Examinee to confirm submission
   - *Example: "You have answered X of 50 questions. Are you sure you want to end the test?"*
   - The dialog must trap keyboard focus within the modal while open (WCAG 2.1.2)
   - The dialog must be announced to screen readers via `role="dialog"` and `aria-labelledby` (WCAG 4.1.3)
   - Pressing `Escape` must dismiss the dialog and return focus to the End Test button
2. Upon confirmation, the test session is closed server-side — **no further edits are permitted**
3. The system shall immediately compute and display the final score
4. The End Test action must be protected against CSRF via a synchronised token or SameSite cookie policy (OWASP A01)

---

### 3.3 Scoring

**Scoring rules:**

| Condition | Marks Awarded |
|---|---|
| Correct answer selected | 1 |
| Incorrect answer selected | 0 |
| Question left unanswered | 0 |
| **Maximum possible score** | **50** |

> There is **no negative marking** in this version.

**Score computation must be performed server-side only.** The client must never be trusted to submit or calculate a score (OWASP A01, A04).

**The score screen shall display:**

- Total score (e.g., *38 / 50*)
- Number of correct answers
- Number of incorrect answers
- Number of unattempted questions
- An option to review submitted responses

---

### 3.4 Response Recording & Review

#### 3.4.1 Storage of Responses

Upon test submission (End Test confirmed), the system shall persistently store the following data per test attempt:

- Reference to the Examinee user record (foreign key, not a plain-text copy of PRN — see Data Model)
- Date and timestamp of submission (UTC)
- Answer selected for each of the 50 questions (or `null` if unanswered)
- Snapshot of the `question_id` and `question_version` at time of submission (via `SessionQuestion` — frozen at session start)
- Final score (computed server-side at submit; `Response.is_correct` populated only at submit — see §3.6.4)

> **GDPR Note:** Response records constitute personal data and are subject to the retention and erasure policies defined in Section 5.

#### 3.4.2 Examinee Response Review

After submission, the Examinee shall be able to access a **read-only review screen** showing each question, the answer they selected, and the correct answer.

Access to this screen must verify server-side that the session belongs to the Examinee who owns the record (IDOR protection — OWASP A01).

#### 3.4.3 Examiner Access to Records

The Examiner portal shall provide:

- A list of all completed test attempts with PRN, Name, Score, and Timestamp
- Drill-down view of individual Examinee response details
- Export of results via `GET /api/v1/examiner/sessions/export` (CSV, UTF-8 with BOM). Export includes: `session_id`, `prn`, `name`, `score`, `submitted_at`, `correct_count`, `incorrect_count`, `unattempted_count`. Each export is **audit-logged**. PRN/Name columns are omitted if the requesting context is a redacted/anonymised export (`?anonymised=true`).

All Examiner access to Examinee records must be logged in the audit trail (see Section 7).

---

### 3.5 Question Management (Examiner Only)

#### 3.5.1 View Question Bank

The Examiner shall view all questions in the question bank in a list/table format with options and correct answers visible. All question management actions must be server-side authorised with the `EXAMINER` role.

#### 3.5.2 Add Question

The Examiner shall be able to add a new question by providing:

- Question text (max 2000 characters; must be sanitised server-side before storage — OWASP A03)
- Four answer options A, B, C, D (each max 500 characters; sanitised server-side)
- Correct answer designation

All fields are mandatory before saving. A unique `question_id` is assigned automatically. Each question is also assigned a `question_version` starting at 1, incrementing on each edit.

#### 3.5.3 Edit Question

The Examiner may edit any existing question's text, options, or correct answer.

- On save, the existing question record must be **soft-updated**: the original version is retained in a `question_versions` archive table; the current record's `question_version` is incremented
- This ensures response records referencing older versions remain historically accurate
- Active ongoing test sessions are not affected — they reference the version that was current when the session started
- All edits are recorded in the audit log (Section 7)

#### 3.5.4 Delete Question

- The Examiner may delete a question using a **soft-delete** (`deleted_at` timestamp, `is_deleted` flag) — records are not physically removed (required for audit integrity and GDPR Article 17 balancing with legal obligation retention)
- A confirmation prompt must appear before marking as deleted
- The system must warn the Examiner if deletion would bring the active question count below 50
- Deleted questions must not appear in new test sessions but must remain resolvable for historical response records

---

### 3.6 Exam Session Rules

#### 3.6.1 Question Selection and Ordering

When a new `TestSession` is created, the server:

1. Verifies **≥ 50 active** (`is_deleted = false`) questions exist; otherwise returns `503 SERVICE_UNAVAILABLE` with problem code `INSUFFICIENT_QUESTION_BANK`.
2. Selects **exactly 50** questions using the institution's configured **`question_selection_mode`**:
   - **`FIXED_ORDER`** (default): all active questions sorted by `question_id` ascending; if more than 50 exist, the first 50 are used. All Examinees receive the **same questions in the same order** for a given bank state.
   - **`RANDOM_SAMPLE`**: cryptographically random sample of 50 without replacement; order shuffled per session. Seed and algorithm are logged server-side for audit reproducibility.
3. Creates 50 **`SessionQuestion`** rows with `position` (1–50), `question_id`, and `question_version_snapshot` frozen at session start.
4. Pre-creates 50 **`Response`** rows with `selected_option = null`; `is_correct` remains **NULL** until session submission.

Ongoing Examiner edits to the live `Question` row do **not** affect an ACTIVE session — scoring uses `SessionQuestion.question_version_snapshot` and archived `QuestionVersion` content.

#### 3.6.2 Exam Duration vs Session Expiry

| Concept | v1.0 behaviour |
|---|---|
| **Exam time limit** | None — Examinee may take unlimited wall-clock time |
| **Session cookie / server session TTL** | 4 hours of **inactivity**; activity = any authenticated Examinee API call |
| **Absolute maximum session age** | 24 hours from `start_time`; server auto-completes with current answers if exceeded (audit-logged) |

#### 3.6.3 Abandoned and Resumed Sessions

- An Examinee who closes the browser may **resume** the same ACTIVE session via `POST /api/v1/auth/examinee/entry` with the same PRN + Name within the TTL above.
- Interim session state (unsubmitted answers) is retained for **session duration + 24 hours** after last activity, then purged by a scheduled job unless the session was COMPLETED (see §5.4).

#### 3.6.4 `is_correct` Field Policy

- `Response.is_correct` MUST remain **NULL** while `TestSession.status = ACTIVE`.
- On `POST .../submit`, the server sets `is_correct` for all 50 rows in a single transaction, then sets `TestSession.score`.
- No Examinee-facing endpoint may return `is_correct` until `status = COMPLETED`.

#### 3.6.5 Pre-Session Bank Enforcement

- Session creation is **rejected** if active question count &lt; 50 (see §3.6.1).
- Examiner delete/edit warnings when count would fall below 50 remain as specified in §3.5.4.

---

## 4. Security Requirements — OWASP Top 10 (2021)

This section maps explicit security controls to each OWASP Top 10 category. All controls are mandatory for production deployment.

### 4.1 A01 — Broken Access Control

- **Server-side enforcement:** Every API route must validate the caller's role claim before executing any logic. Client-side role checks are advisory only.
- **IDOR protection:** All endpoints that return session, response, or score data scoped to an Examinee must verify `session.examinee_id == authenticated_user.id` server-side.
- **Least privilege:** Examinees must have no access to question `correct_option` data during an active test session. This field must be excluded from all Examinee-facing API responses until after session closure.
- **Path traversal:** File upload is out of scope for v1.0. If introduced later, all file paths must be validated against an allowlist.
- **Direct URL access:** Authenticated routes must not be accessible without a valid session token, regardless of how the URL is constructed.

### 4.2 A02 — Cryptographic Failures

- **TLS:** All client–server communication must use **TLS 1.2 minimum** (TLS 1.3 preferred). TLS 1.0 and 1.1 must be disabled.
- **HSTS:** The server must return `Strict-Transport-Security: max-age=31536000; includeSubDomains` on all responses.
- **Data at rest:** The database must encrypt sensitive columns (Name, PRN) at rest using AES-256 or equivalent, or use full-disk encryption at the infrastructure level.
- **Password hashing:** bcrypt (cost ≥ 12) or Argon2id. Plain-text or reversibly encrypted passwords are prohibited.
- **PII in logs:** PRN and Name must be **masked or excluded** from all application logs. Log entries must reference internal `user_id` only.
- **Secrets management:** Database credentials, session signing/encryption keys, and any API keys must be stored in a secrets manager (e.g., HashiCorp Vault, AWS Secrets Manager) — never in source code or environment files committed to version control.

### 4.3 A03 — Injection

- **Parameterised queries:** All database interactions must use parameterised queries or an ORM with prepared statements. String concatenation in SQL is prohibited.
- **Input sanitisation:** All user-supplied inputs (question text, options, name, PRN) must be sanitised server-side before storage. This is separate from client-side validation, which is advisory only.
- **Output encoding:** All data rendered in HTML (question text, option text, name) must be HTML-entity-encoded on output to prevent stored XSS.
- **Content Security Policy:** The server must return a `Content-Security-Policy` header restricting script sources to the application's own origin (`script-src 'self'`). Inline scripts are prohibited.

### 4.4 A04 — Insecure Design

- **Score server-side only:** Final score computation must occur exclusively on the server. Any client-submitted score value must be ignored.
- **Rate limiting:** Login endpoint: max 5 attempts per 15 minutes per account. Registration endpoint: max 10 registrations per IP per hour.
- **Account lockout:** After 5 consecutive failed Examiner login attempts, the account is locked for 15 minutes. Lockout events must be audit-logged.
- **Threat model:** A lightweight threat model (STRIDE or similar) must be produced during the design phase and reviewed by a security lead before development begins.
- **Correct answer exposure:** The `correct_option` field must never be included in API responses to Examinees during an active test session — this is an insecure design risk, not merely an access control issue.

### 4.5 A05 — Security Misconfiguration

- **HTTP security headers** — the following headers are mandatory on all responses:

  | Header | Required Value |
  |---|---|
  | `Content-Security-Policy` | `default-src 'self'; script-src 'self'; object-src 'none'` |
  | `X-Frame-Options` | `DENY` |
  | `X-Content-Type-Options` | `nosniff` |
  | `Referrer-Policy` | `strict-origin-when-cross-origin` |
  | `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` |
  | `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |

- **Error handling:** Production error responses must never expose stack traces, database errors, or internal paths. Generic error messages must be used. Detailed errors are logged server-side only.
- **Default credentials:** Any default Examiner credentials from setup must be rotated before deployment. The system should enforce a password change on first login.
- **Dependency scanning:** All third-party libraries and packages must be scanned for known CVEs as part of the CI/CD pipeline (e.g., `npm audit`, `Snyk`, `Dependabot`).

### 4.6 A06 — Vulnerable and Outdated Components

- A **software bill of materials (SBOM)** must be maintained listing all third-party dependencies and their versions.
- Automated dependency scanning must run on every build. Builds with **Critical** or **High** severity CVEs must fail the pipeline.
- Dependencies must be updated at minimum monthly. Security patches must be applied within 72 hours of disclosure.

### 4.7 A07 — Identification and Authentication Failures

- Session tokens must be **cryptographically random**, minimum 128 bits of entropy (ASVS 3.2.2).
- Tokens must be transmitted via **HttpOnly, Secure, SameSite=Strict cookies** only — never in query parameters or response bodies intended for `localStorage`.
- **Session fixation prevention:** A fresh session token must be issued immediately upon successful authentication.
- **Logout:** Logout must invalidate the server-side session record. Token expiry alone is insufficient.
- **Concurrent session policy:** By default, a new Examiner login must invalidate all prior active sessions for that account.
- **Session timeout:** Examiner sessions expire after 60 minutes of inactivity. Examinee sessions expire after 4 hours or upon test completion.

### 4.8 A08 — Software and Data Integrity Failures

- **Question bank integrity:** All question edits are versioned and audit-logged. No edit is destructive (soft-update only).
- **Score integrity:** Score records written at session close are immutable — no UPDATE must be permitted on a closed session's score column.
- **CI/CD pipeline:** Build and deployment pipelines must be protected with access controls. Artefacts must be signed. Supply chain attacks must be mitigated by pinning dependency versions and verifying checksums.
- **Session token validation:** Opaque session IDs must be validated against the server-side store on every request; unknown or expired IDs are rejected with `401`.

### 4.9 A09 — Security Logging and Monitoring Failures

See Section 7 (Audit, Logging & Monitoring) for detailed logging requirements. At minimum, the following events must generate security log entries:

- Successful and failed authentication attempts (Examiner)
- Account lockout events
- Role escalation attempts (e.g., Examinee attempting to access Examiner endpoints)
- Question bank changes (add, edit, delete) with actor identity
- Test session open and close events
- Any 4xx/5xx API responses with the request context (excluding PII from log body)

### 4.10 A10 — Server-Side Request Forgery (SSRF)

- SSRF is not a primary risk for this application in v1.0 as there are no URL-fetching features.
- If any future feature involves server-side URL resolution (e.g., fetching question images), an allowlist of permitted URL schemes and domains must be enforced.

---

## 5. Privacy & Data Protection — GDPR

This section applies to all processing of personal data (PRN, Name) collected from Examinees, and any operational data held about Examiners. The platform must be designed and operated in accordance with GDPR (EU) 2016/679.

### 5.1 Lawful Basis for Processing (Article 6)

| Data | Purpose | Lawful Basis |
|---|---|---|
| Examinee PRN + Name | Identify the Examinee, administer the test, record results | **Legitimate interests** (Article 6(1)(f)) of the institution conducting the examination, balanced against Examinee interests; or **contract performance** (Article 6(1)(b)) if examination is part of an enrolment agreement. A written **LIA** must be completed and approved by the Data Controller before production go-live. |
| Examinee test responses + score | Generate and store examination results | Same basis as above |
| Examiner username + password hash | Authentication and access control for administrative function | **Legitimate interests** (Article 6(1)(f)) |

### 5.2 Privacy Notice (Article 13)

A privacy notice must be displayed to Examinees **at the point of registration**, before any data is collected. The notice must include:

- Identity and contact details of the Data Controller (the institution deploying the platform)
- Purpose and lawful basis for processing
- Data retention period (see 5.4)
- Whether data is shared with third parties
- Examinee rights: access, rectification, erasure, restriction, objection
- Contact for data-related queries or complaints

### 5.3 Data Minimisation (Article 5(1)(c))

Only the minimum personal data necessary for the examination purpose must be collected:

- **Collected:** PRN, Full Name
- **Not collected:** date of birth, email address, phone number, biometric data, IP address linked to PRN (IP may be logged for security but must not be linked to PRN in any queryable way)

### 5.4 Data Retention & Deletion (Articles 5(1)(e), 17)

| Data Category | Retention Period | Deletion Action |
|---|---|---|
| Active test session data | Duration of session + 24 hours (to allow review) | Auto-purge of interim session state |
| Completed test responses and score | As defined by the institution's academic records policy (e.g., 2 years) | Hard delete or anonymisation after retention period |
| Examiner account credentials | Duration of employment / engagement | Hard delete on account deactivation |
| Audit logs | Minimum 1 year (security requirement); maximum 3 years | Secure deletion after maximum period |
| Anonymised aggregate statistics | Indefinite (no longer personal data once fully anonymised) | N/A |

A scheduled automated job must enforce the defined retention periods. Retention duration for completed tests is **configurable** via `PlatformSettings.retention_days_completed` (default: 730), set by Examiner through `PATCH /api/v1/examiner/settings` (see §9.6.8). Manual erasure is available via the Examiner erasure endpoint (§5.5).

### 5.5 Right to Erasure (Article 17)

The platform must support a Right to Erasure workflow:

- A designated **Examiner** must be able to **permanently delete** an Examinee's personal data via `POST /api/v1/examiner/users/examinees/{userId}/erase` (see §9.6.8). A separate DPO role is out of scope for v1.0; DPO functions are performed by the institution outside the application.
- Upon erasure, the Examinee's PRN and Name in their session and response records must be replaced with an anonymised token (e.g., `ERASED-{uuid}`) — preserving aggregate statistical integrity while removing identifiability
- Erasure must cascade to all related tables: `users`, `test_sessions`, `responses`
- Audit log entries may retain a non-identifying reference to the erased record (e.g., the internal `user_id`) for security accountability

### 5.6 Right of Access (Article 15)

An Examinee must be able to obtain a copy of all personal data held about them via **`GET /api/v1/examinee/me/data-export`** (JSON) after authenticating with PRN + Name. This satisfies Article 15 (access) and Article 20 (data portability) for self-service requests. Examiner-initiated exports for erasure-related workflows use the Examiner endpoints in §9.6.8.

**Processor arrangements:** If a hosting vendor processes data on behalf of the institution, a **DPA** (Article 28) must be in place before production. Sub-processors must be listed in the privacy notice (§5.2).

### 5.7 Data Security (Article 32)

Technical and organisational measures for data security include all controls specified in Section 4 (OWASP) plus:

- Role-based access controls ensuring only authorised personnel access personal data
- Encryption in transit (TLS 1.2+) and at rest (AES-256 or infrastructure-level FDE)
- Regular security assessments and penetration testing (at minimum annually)

### 5.8 Data Breach Notification (Articles 33–34)

- In the event of a personal data breach, the Data Controller must notify the relevant supervisory authority **within 72 hours** of becoming aware of the breach (Article 33)
- If the breach is likely to result in a high risk to the rights and freedoms of affected Examinees, those individuals must also be notified without undue delay (Article 34)
- The platform's logging and monitoring (Section 7) must provide sufficient information to support breach detection and notification obligations

### 5.9 Privacy by Design (Article 25)

The following Privacy by Design principles must be applied throughout development:

- **Default to privacy:** The most privacy-protective settings must be the defaults (e.g., Examinees cannot see each other's data by default)
- **Data minimisation at code level:** ORM queries must select only the fields needed for each operation — no `SELECT *` on tables containing PII
- **Pseudonymisation:** Where feasible (e.g., in logs and analytics), references to Examinees must use internal `user_id` rather than PRN or name
- **Access controls reflect data sensitivity:** PII fields (PRN, Name) must have field-level access controls in the data layer

---

## 6. Accessibility Requirements — WCAG 2.1 AA

The platform must conform to **WCAG 2.1 Level AA** across all pages and user interfaces. Conformance must be verified by automated tooling (e.g., axe-core, Lighthouse) and manual screen reader testing (NVDA + Firefox, VoiceOver + Safari) before each release.

### 6.1 Perceivable

#### 6.1.1 Text Alternatives (WCAG 1.1.1 — Level A)
- All non-text content must have a text alternative. If question content includes images in a future version, `alt` attributes must describe the image's informational content.
- Decorative images must use `alt=""` and `role="presentation"`.

#### 6.1.2 Use of Colour (WCAG 1.4.1 — Level A)
- Colour must **not** be the sole means of conveying information. The progress indicator, answered/unanswered question states, and any status indicators must use colour **plus** a text label or icon shape.
- Example: An answered question in the navigator panel must show a tick symbol in addition to a green colour fill.

#### 6.1.3 Colour Contrast (WCAG 1.4.3 — Level AA)
- Normal text (< 18pt): minimum contrast ratio of **4.5:1** against background
- Large text (≥ 18pt or 14pt bold): minimum contrast ratio of **3:1**
- UI components (radio buttons, button borders, focus rings): minimum contrast ratio of **3:1**
- All colour palette choices must be validated against these ratios using a tool such as WebAIM Contrast Checker before implementation

#### 6.1.4 Resize Text (WCAG 1.4.4 — Level AA)
- Text must be resizable up to 200% without loss of content or functionality. Fixed pixel font sizes (`px`) must not be used for body text — use relative units (`rem`, `em`).

#### 6.1.5 Reflow (WCAG 1.4.10 — Level AA)
- Content must reflow at 320px viewport width (equivalent to 400% zoom on a 1280px screen) without horizontal scrolling or loss of content.

### 6.2 Operable

#### 6.2.1 Keyboard Accessible (WCAG 2.1.1 — Level A)
- **All** functionality must be operable via keyboard alone. This includes:
  - Selecting answer options (radio buttons navigable with arrow keys within the group)
  - Clicking Previous / Next / End Test
  - Interacting with the confirmation modal
  - Examiner add / edit / delete question workflows

#### 6.2.2 No Keyboard Trap (WCAG 2.1.2 — Level A)
- Focus must not become trapped in any component except the confirmation modal (which intentionally traps focus for accessibility — see 3.2.7). Closing the modal must fully restore focus to the triggering element.

#### 6.2.3 Focus Visible (WCAG 2.4.7 — Level AA)
- The keyboard focus indicator must be clearly visible at all times. The default browser outline must not be suppressed without providing an equally visible replacement. Minimum focus ring contrast: **3:1**.

#### 6.2.4 Focus Order (WCAG 2.4.3 — Level A)
- The reading and focus order must be logical and consistent with the visual layout. On question navigation, focus must programmatically move to the question heading.

#### 6.2.5 Skip Navigation (WCAG 2.4.1 — Level A)
- A "Skip to main content" link must be the first focusable element on every page to allow keyboard users to bypass repeated navigation elements.

#### 6.2.6 Page Titled (WCAG 2.4.2 — Level A)
- Each page/view must have a descriptive `<title>` element that includes both the page context and the application name (e.g., *"Question 7 of 50 – MCQ Test Platform"*).

### 6.3 Understandable

#### 6.3.1 Language of Page (WCAG 3.1.1 — Level A)
- The HTML `lang` attribute must be set on the `<html>` element (e.g., `lang="en"`).

#### 6.3.2 Labels and Instructions (WCAG 3.3.2 — Level A)
- All form inputs must have visible, persistent labels. Placeholder text alone is not an acceptable label substitute.
- The registration form must clearly label the PRN and Name fields.
- The question options must use `<fieldset>` + `<legend>` to group and label the radio button set.

#### 6.3.3 Error Identification (WCAG 3.3.1 — Level A)
- Validation errors must be:
  - Identified in text (not colour alone)
  - Associated with the specific input field via `aria-describedby`
  - Announced to screen readers without requiring a page reload (use `aria-live` regions for dynamic updates)

#### 6.3.4 Error Suggestion (WCAG 3.3.3 — Level AA)
- Validation error messages must suggest how the user can correct the issue (e.g., *"PRN must contain only letters and numbers, up to 20 characters"*).

### 6.4 Robust

#### 6.4.1 Markup Quality (WCAG 4.1.1 — superseded in WCAG 2.2)
- HTML must be valid and well-formed. Automated HTML validation must be included in the CI pipeline.
- **Note:** Success Criterion 4.1.1 (Parsing) was removed in WCAG 2.2 as it is adequately covered by 4.1.2. This project targets **WCAG 2.1 AA**; continue to enforce valid markup for robustness, not as a separate conformance claim.

#### 6.4.2 Name, Role, Value (WCAG 4.1.2 — Level A)
- All interactive UI components must expose their name, role, and state to assistive technologies:
  - Buttons: `role="button"` (or native `<button>` element), `aria-label` when the visible label is insufficient
  - Radio buttons: native `<input type="radio">` preferred
  - Modal dialog: `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to the dialog title
  - Progress indicator: `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
  - Disabled navigation buttons: `aria-disabled="true"` (not HTML `disabled` — see 3.2.3)

#### 6.4.3 Status Messages (WCAG 4.1.3 — Level AA)
- System status messages that appear without a focus change (e.g., "Answer saved", "Progress: 32/50") must use `role="status"` or `aria-live="polite"` so screen readers announce them without disrupting the user's current position.

---

## 7. Audit, Logging & Monitoring

A robust audit and logging system is required for security accountability, GDPR breach notification support, and operational monitoring.

### 7.1 Audit Log Requirements

An **immutable audit log** must be maintained. Audit records must not be editable or deletable by any application user, including Examiners. Only a system administrator with direct database access (outside the application) may archive or rotate logs per the retention policy.

**Events that must be audit-logged:**

| Event Category | Event | Data Recorded |
|---|---|---|
| **Authentication** | Examiner login success | `user_id`, timestamp, IP address |
| **Authentication** | Examiner login failure | `username_attempted` (hashed), timestamp, IP address |
| **Authentication** | Account lockout triggered | `user_id`, timestamp, IP address |
| **Authentication** | Logout | `user_id`, timestamp |
| **Authorisation** | Unauthorised access attempt (role violation) | `user_id`, endpoint attempted, timestamp |
| **Question Management** | Question added | `examiner_id`, `question_id`, timestamp |
| **Question Management** | Question edited | `examiner_id`, `question_id`, previous version, new version, timestamp |
| **Question Management** | Question deleted | `examiner_id`, `question_id`, timestamp |
| **Test Session** | Session opened | `session_id`, `user_id` (not PRN), timestamp |
| **Test Session** | Session closed (End Test) | `session_id`, `user_id`, score, timestamp |
| **Data Access** | Examiner views Examinee response detail | `examiner_id`, `session_id` accessed, timestamp |
| **Data Management** | Examinee data erasure request processed | `user_id` (anonymised post-erasure), timestamp, operator |

### 7.2 Log Format & Storage

- Logs must be structured (JSON preferred) for machine-readability
- Each log entry must include: `timestamp` (UTC ISO 8601), `event_type`, `actor_id`, `resource_id`, `outcome` (success/failure), `ip_address`
- **PII must not appear in log entries** — use internal `user_id` only. PRN and Name must never be logged
- Logs must be written to a separate, append-only store (not the same database as application data)
- Log integrity must be protected — consider write-once storage or cryptographic chaining

### 7.3 Monitoring & Alerting

The following conditions must generate real-time alerts to the operations team:

- 5 or more failed Examiner login attempts within 10 minutes (brute force signal)
- Any unauthorised access attempt (role violation 403 response)
- Unexpected spike in test session creation (potential automated abuse)
- Application error rate exceeding 1% of requests over a 5-minute window
- Availability probe failures (uptime monitoring)

**Reference monitoring stack (implementation guidance):**

| Concern | Tool (example) |
|---|---|
| Metrics & alerting | Prometheus + Alertmanager, or cloud-native equivalent (CloudWatch, Azure Monitor) |
| Log aggregation | Structured logs shipped to ELK, Loki, or CloudWatch Logs |
| Uptime | Synthetic probe (e.g., Uptime Kuma, Pingdom) against `/api/v1/health` |
| APM / tracing | OpenTelemetry-compatible collector (optional for v1.0) |

Runbooks for each alert in §7.3 must be documented before production go-live.

---

## 8. Non-Functional Requirements

| REQ ID | Requirement | Priority | Standard Reference |
|---|---|---|---|
| NFR-01 | Each question view must load within 1 second on a standard broadband connection (≥10 Mbps). | High | Performance |
| NFR-02 | The system must support at least **100 concurrent ACTIVE Examinee sessions** with p95 API latency &lt; 500 ms for `GET .../questions/{position}` and `PUT .../responses/{questionId}` under load test (k6 or Locust). Error rate &lt; 0.1%. | High | Scalability |
| NFR-03 | Examinee response data must be persisted to a durable data store on every answer selection (auto-save), not only at End Test. | High | Data Integrity |
| NFR-04 | Examiner passwords must be hashed with bcrypt (cost ≥ 12) or Argon2id. | High | OWASP ASVS 2.4 |
| NFR-05 | The application must function correctly on the latest two major versions of Chrome, Firefox, Safari, and Edge on desktop and mobile. Touch targets ≥ 44×44 CSS px on mobile viewports. | Medium | Compatibility |
| NFR-06 | The UI must be responsive from 320px to 1920px viewport width without content loss or horizontal scrolling. | Medium | WCAG 1.4.10 |
| NFR-07 | System uptime must target 99.5% during active examination periods. | Medium | Availability |
| NFR-08 | All client–server communication must use TLS 1.2 minimum. | High | OWASP A02 |
| NFR-09 | The platform must comply with GDPR for all personal data (PRN, Name, responses). | High | GDPR Article 5 |
| NFR-10 | The platform must conform to WCAG 2.1 Level AA across all interfaces. | High | WCAG 2.1 |
| NFR-11 | All HTTP responses must include the security headers defined in Section 4.5. | High | OWASP A05 |
| NFR-12 | Automated dependency scanning for CVEs must run on every CI build; Critical/High findings must fail the build. | High | OWASP A06 |
| NFR-13 | Database backups must be taken daily, retained for 30 days, and tested for restore integrity monthly. | Medium | Business Continuity |
| NFR-14 | The application must implement graceful degradation — if the auto-save endpoint fails, the Examinee must be informed and allowed to retry before continuing navigation. | Medium | Resilience |
| NFR-15 | Input fields must enforce server-side length limits matching the data model (PRN ≤ 20 chars, Name ≤ 100 chars, question text ≤ 2000 chars, option text ≤ 500 chars). | High | OWASP A03 |
| NFR-16 | **RTO** ≤ 4 hours and **RPO** ≤ 24 hours for production database recovery (validated in monthly restore drill). | Medium | Business Continuity |
| NFR-17 | Production deployment must document **data residency** (EU region if GDPR applies). PII must not be replicated to non-approved regions. | High | GDPR Article 44 |
| NFR-18 | OpenAPI 3.1 specification must be generated from code or maintained in repo and published at `/api/v1/openapi.json`. Contract tests must cover all §9.6 endpoints. | High | API Quality |

### 8.1 Test Strategy

| Layer | Scope | Tooling (example) |
|---|---|---|
| **Unit** | Scoring, validation, versioning, erasure anonymisation | `pytest` |
| **Integration** | API contracts (§9.6), DB transactions, session store | `pytest` + Testcontainers (PostgreSQL, Redis) |
| **E2E** | Full Examinee and Examiner flows, WCAG critical paths | Playwright + axe-core |
| **Security** | OWASP ZAP baseline scan in CI; annual manual penetration test | ZAP, external firm |
| **Load** | 100 concurrent ACTIVE sessions (NFR-02) | k6 or Locust |
| **Contract** | OpenAPI response schema validation | Schemathesis or Dredd |

Seed data for staging: minimum **55** active questions and two Examiner accounts (one for CI, one for manual QA).

---

## 9. System Architecture Overview

### 9.1 Key Components

- **Frontend:** Web-based single-page application (SPA) with role-aware routing; no sensitive logic or data on the client
- **Backend / API:** RESTful API handling authentication, test sessions, scoring (server-side only), and question management
- **Database:** Relational store (recommended) for structured data with foreign-key integrity; PII columns encrypted at rest
- **Authentication Module:** Opaque **server-side sessions** (Redis-backed) via HttpOnly cookies; role and `user_id` bound to session record; validated on every request
- **Cache / rate limiting:** Redis for session store, login lockout counters, and registration rate limits
- **Audit Log Store:** Append-only structured log store, separate from the application database
- **Secrets Manager:** Centralised store for database credentials, session secrets, and environment-specific configuration

### 9.2 Data Model (v2.1)

> **v2.1 additions:** `SessionQuestion` table; `PlatformSettings`; `Response.is_correct` nullable until submit; `TestSession` adds `last_activity_at`, `selection_mode`; Examiner `username` on User.

| Entity | Key Fields |
|---|---|
| **User** | `user_id` (PK UUID), `username` (unique, Examiners only), `prn` (encrypted, unique, Examinees), `name` (encrypted), `role` ENUM('EXAMINER','EXAMINEE'), `password_hash` (Examiners only), `is_active`, `created_at`, `updated_at`, `deleted_at` |
| **Question** | `question_id` (PK UUID), `question_text`, `option_a`–`option_d`, `correct_option` ENUM('A','B','C','D'), `question_version` INT, `created_by` (FK → User), `created_at`, `updated_at`, `is_deleted`, `deleted_at` |
| **QuestionVersion** | `version_id` (PK), `question_id` (FK), `version_number`, snapshot fields, `modified_by` (FK), `modified_at` |
| **TestSession** | `session_id` (PK UUID), `user_id` (FK), `status` ENUM('ACTIVE','COMPLETED','EXPIRED'), `selection_mode`, `start_time`, `end_time`, `last_activity_at`, `score` (nullable until complete), `created_at` |
| **SessionQuestion** | `session_question_id` (PK), `session_id` (FK), `question_id` (FK), `position` INT (1–50, unique per session), `question_version_snapshot` INT, UNIQUE(`session_id`, `position`) |
| **Response** | `response_id` (PK), `session_id` (FK), `question_id` (FK), `selected_option` ENUM('A','B','C','D') NULL, `is_correct` BOOLEAN **NULL until submit**, `answered_at`, `updated_at`, UNIQUE(`session_id`, `question_id`) |
| **PlatformSettings** | `setting_key` (PK), `setting_value` JSON — keys: `retention_days_completed`, `allow_examinee_retake`, `question_selection_mode` |
| **AuditLog** | `log_id` (PK), `event_type`, `actor_id`, `resource_type`, `resource_id`, `outcome`, `ip_address`, `metadata` JSON, `created_at` |

### 9.3 Entity Relationship (v2.1)

```
User (Examinee)                    User (Examiner)
    │                                    │
    └──< TestSession                     │ manages
              │                          ▼
              ├──< SessionQuestion >── Question ──< QuestionVersion
              │
              └──< Response (is_correct NULL until COMPLETED)

AuditLog ── actor_id ──► User
PlatformSettings (singleton row per deployment)
```

### 9.4 API Security Design

- All API routes prefixed with `/api/v1/`; breaking changes require `/api/v2/`
- Role-scoped path prefixes as in §9.6; **authorization enforced in middleware before route handlers**
- CORS: allow only configured frontend origin(s); `credentials: true` for cookie auth
- Authenticated responses: `Cache-Control: no-store`, `Pragma: no-cache`
- **CSRF:** SameSite=Strict cookies plus `X-CSRF-Token` header on state-changing Examinee/Examiner requests (token issued in `GET /api/v1/auth/csrf` or embedded in initial HTML)
- **Idempotency:** `POST .../submit` accepts optional `Idempotency-Key` header; duplicate keys return the original `201` response without re-scoring

### 9.5 Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | React 18+ with TypeScript, Vite build | Mature a11y ecosystem; CSP-friendly static assets; role-based routing |
| **Backend API** | Python 3.12 + **FastAPI** | Auto-generated OpenAPI 3.1; async I/O; aligns with team Python skills |
| **ORM / migrations** | SQLAlchemy 2.x + Alembic | Parameterised queries; schema versioning |
| **Database** | **PostgreSQL** 15+ | FK integrity, transactions, optional `pgcrypto` for column encryption |
| **Session / cache** | **Redis** 7+ | Server-side sessions, rate limits, lockout counters |
| **Reverse proxy** | nginx or Caddy | TLS termination, security headers, request size limits |
| **Audit logs** | Append-only table in separate PostgreSQL schema **or** ship to immutable log store (e.g., CloudWatch Logs with retention lock) |
| **Secrets** | HashiCorp Vault / AWS Secrets Manager / Azure Key Vault | No secrets in VCS |
| **CI/CD** | GitHub Actions | `pytest`, `npm audit`/pip-audit, axe in Playwright E2E, k6 load smoke |
| **Hosting** | Containerised (Docker); EU region if GDPR applies (NFR-17) |

**Explicitly not used for production UI:** Streamlit, Gradio (insufficient WCAG/focus-control for §6).

### 9.6 REST API Contracts

#### 9.6.1 Conventions

| Topic | Standard |
|---|---|
| **Base URL** | `https://{host}/api/v1` |
| **Format** | JSON (`Content-Type: application/json; charset=utf-8`) |
| **Auth** | HttpOnly cookie `session_id` (opaque UUID). No `Authorization: Bearer` in v1.0. |
| **Request IDs** | Server returns `X-Request-Id` (UUID) on every response; clients may send `X-Request-Id` for correlation |
| **Timestamps** | ISO 8601 UTC with `Z` suffix (e.g., `2026-06-03T14:30:00Z`) |
| **UUIDs** | RFC 4122 version 4 for all resource IDs |
| **Pagination** | Cursor-based: `?cursor={opaque}&limit={n}` (default 20, max 100). Response includes `next_cursor` (null if last page). |
| **Sorting** | `?sort=field` or `?sort=-field` (descending prefix `-`) where supported |
| **Errors** | RFC 7807 `application/problem+json` (see §9.7) |
| **Optimistic concurrency** | `PUT` responses include `updated_at`; client sends `If-Unmodified-Since` or `If-Match` with `updated_at` value on subsequent saves |
| **Versioning** | URL path version only in v1.0 |

**Standard success response envelope (where applicable):**

```json
{
  "data": { },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

List endpoints wrap arrays in `data` and include `meta.next_cursor`.

---

#### 9.6.2 Health & Metadata (Public)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Liveness: `{ "status": "ok" }` |
| `GET` | `/ready` | None | Readiness: DB + Redis connectivity |
| `GET` | `/openapi.json` | None | OpenAPI 3.1 document (NFR-18) |

---

#### 9.6.3 Authentication (`/auth/*`)

##### `GET /auth/csrf`

Returns CSRF token for SPA bootstrap.

**Response `200`:**

```json
{
  "data": {
    "csrf_token": "a1b2c3..."
  }
}
```

Sets cookie `session_id` only after login/entry endpoints below.

---

##### `POST /auth/examinee/entry`

Unified Examinee registration, resume, or retake (§3.1.5).

**Headers:** `X-CSRF-Token` (required after first page load)

**Request body:**

```json
{
  "prn": "STU2024001",
  "name": "Jane Doe",
  "privacy_acknowledged": true
}
```

**Validation:** `prn` — `^[A-Za-z0-9]{1,20}$`; `name` — trimmed, 1–100 chars; `privacy_acknowledged` must be `true`.

| Status | When | Response `data` |
|---|---|---|
| `201` | New session created | See **ExamineeSessionResource** |
| `200` | ACTIVE session resumed | See **ExamineeSessionResource** |
| `400` | Validation failure | Problem `VALIDATION_ERROR` + `errors[]` |
| `409` | COMPLETED session, retake disabled | Problem `EXAM_ALREADY_COMPLETED` |
| `403` | Name mismatch for existing PRN | Problem `IDENTITY_MISMATCH` (generic, no leak) |
| `429` | Registration rate limit | Problem `RATE_LIMIT_EXCEEDED` |
| `503` | &lt; 50 active questions | Problem `INSUFFICIENT_QUESTION_BANK` |

**ExamineeSessionResource:**

```json
{
  "session_id": "uuid",
  "status": "ACTIVE",
  "total_questions": 50,
  "answered_count": 0,
  "current_position": 1,
  "started_at": "2026-06-03T10:00:00Z",
  "expires_at": "2026-06-03T14:00:00Z"
}
```

Sets `Set-Cookie: session_id=...; HttpOnly; Secure; SameSite=Strict; Path=/api/v1`

---

##### `POST /auth/examiner/login`

**Request:**

```json
{
  "username": "examiner1",
  "password": "SecurePass123!"
}
```

| Status | When |
|---|---|
| `200` | Success — `{ "data": { "user_id": "uuid", "username": "examiner1", "must_change_password": false } }` |
| `401` | Invalid credentials — Problem `INVALID_CREDENTIALS` (generic message) |
| `423` | Account locked — Problem `ACCOUNT_LOCKED` + `locked_until` |
| `429` | Rate limited |

Invalidates prior Examiner sessions (default). Issues new `session_id` cookie.

---

##### `POST /auth/logout`

**Auth:** Examinee or Examiner session.

**Response `204`** No body. Invalidates server session. Clears cookie.

---

##### `GET /auth/me`

**Response `200`:**

```json
{
  "data": {
    "user_id": "uuid",
    "role": "EXAMINEE",
    "prn": "STU2024001",
    "name": "Jane Doe"
  }
}
```

Examinee: includes `prn`, `name`. Examiner: includes `username` only (no `prn`).

---

#### 9.6.4 Examinee Test API (`/examinee/*`)

All routes require `EXAMINEE` role and `session_id` cookie. Path `sessionId` must equal the caller's ACTIVE/COMPLETED session (IDOR check).

##### `GET /examinee/sessions/current`

Returns the session bound to the current cookie.

**Response `200`:** **ExamineeSessionResource** (extended with `answered_count`, `expires_at`).

**Response `404`:** No active session — Problem `SESSION_NOT_FOUND`.

---

##### `GET /examinee/sessions/{sessionId}/questions/{position}`

`position` integer 1–50.

**Response `200`:**

```json
{
  "data": {
    "position": 7,
    "total": 50,
    "question": {
      "question_id": "uuid",
      "question_text": "What is ...?",
      "options": [
        { "key": "A", "text": "Option A" },
        { "key": "B", "text": "Option B" },
        { "key": "C", "text": "Option C" },
        { "key": "D", "text": "Option D" }
      ]
    },
    "selected_option": "B",
    "answered_count": 32
  }
}
```

**Must NOT include:** `correct_option`, `is_correct`.

| Status | When |
|---|---|
| `403` | Session not owned or not ACTIVE |
| `404` | Invalid position |

---

##### `PUT /examinee/sessions/{sessionId}/responses/{questionId}`

Auto-save selected answer (§3.2.4).

**Headers:** `If-Unmodified-Since: {updated_at}` (optional, recommended)

**Request:**

```json
{
  "selected_option": "C"
}
```

`null` clears selection (unattempted).

**Response `200`:**

```json
{
  "data": {
    "question_id": "uuid",
    "selected_option": "C",
    "updated_at": "2026-06-03T10:15:00Z",
    "answered_count": 33
  }
}
```

| Status | When |
|---|---|
| `400` | Invalid option key |
| `403` | Session COMPLETED or not owned |
| `409` | Stale `If-Unmodified-Since` — Problem `CONFLICT` |
| `503` | DB unavailable — client shows retry per NFR-14 |

---

##### `POST /examinee/sessions/{sessionId}/submit`

Ends test; computes score (§3.2.7).

**Headers:** `Idempotency-Key: {uuid}` (recommended)

**Request:**

```json
{
  "confirm": true
}
```

**Response `201`:**

```json
{
  "data": {
    "session_id": "uuid",
    "status": "COMPLETED",
    "score": 38,
    "max_score": 50,
    "correct_count": 38,
    "incorrect_count": 10,
    "unattempted_count": 2,
    "submitted_at": "2026-06-03T11:00:00Z"
  }
}
```

| Status | When |
|---|---|
| `400` | `confirm` not true |
| `403` | Not ACTIVE or not owned |
| `409` | Already submitted (idempotent replay returns original `201`) |

---

##### `GET /examinee/sessions/{sessionId}/review`

**Auth:** COMPLETED session only.

**Response `200`:**

```json
{
  "data": {
    "items": [
      {
        "position": 1,
        "question_text": "...",
        "options": [ { "key": "A", "text": "..." } ],
        "selected_option": "B",
        "correct_option": "C",
        "is_correct": false
      }
    ]
  }
}
```

---

##### `GET /examinee/me/data-export`

**Response `200`:** `Content-Type: application/json`, `Content-Disposition: attachment; filename="my-data-export.json"`

Includes: user profile, all sessions, all responses, scores, timestamps. Satisfies GDPR Articles 15 and 20.

---

#### 9.6.5 Examiner Question Bank (`/examiner/questions`)

##### `GET /examiner/questions`

**Query:** `?cursor=&limit=&include_deleted=false`

**Response `200`:**

```json
{
  "data": [
    {
      "question_id": "uuid",
      "question_text": "...",
      "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
      "correct_option": "A",
      "question_version": 3,
      "is_deleted": false,
      "updated_at": "2026-06-03T09:00:00Z"
    }
  ],
  "meta": { "next_cursor": null, "active_count": 52 }
}
```

---

##### `POST /examiner/questions`

**Request:**

```json
{
  "question_text": "Sample question?",
  "option_a": "...",
  "option_b": "...",
  "option_c": "...",
  "option_d": "...",
  "correct_option": "B"
}
```

**Response `201`:** Created question resource.

---

##### `PATCH /examiner/questions/{questionId}`

Partial update. Archives prior version to `QuestionVersion`; increments `question_version`.

**Response `200`:** Updated resource.

**Response `409`:** Problem `BANK_BELOW_MINIMUM` if soft-delete would leave &lt; 50 active (for DELETE).

---

##### `DELETE /examiner/questions/{questionId}`

Soft-delete. **Response `204`**.

**Response `409`:** Would reduce active count below 50 — Problem `BANK_BELOW_MINIMUM` with `active_count` in `detail`.

---

#### 9.6.6 Examiner Results (`/examiner/sessions`)

##### `GET /examiner/sessions`

**Query:** `?cursor=&limit=&prn=&submitted_from=&submitted_to=`

**Response `200`:**

```json
{
  "data": [
    {
      "session_id": "uuid",
      "prn": "STU2024001",
      "name": "Jane Doe",
      "score": 38,
      "submitted_at": "2026-06-03T11:00:00Z",
      "status": "COMPLETED"
    }
  ],
  "meta": { "next_cursor": "..." }
}
```

Access to list and detail is audit-logged.

---

##### `GET /examiner/sessions/{sessionId}`

Full drill-down including per-question responses with `correct_option` and `is_correct`.

---

##### `GET /examiner/sessions/export`

**Query:** `?format=csv&submitted_from=&submitted_to=&anonymised=false`

**Response `200`:** `text/csv; charset=utf-8` with BOM. Audit-logged.

---

#### 9.6.7 Examiner Administration (`/examiner/users`, `/examiner/settings`)

##### `POST /examiner/users/examiners`

Creates Examiner account.

**Request:** `{ "username": "...", "password": "...", "force_password_change": true }`

**Response `201`**

---

##### `POST /examiner/users/examinees/{userId}/erase`

GDPR erasure (§5.5). **Response `202`** Accepted — async job replaces PII with `ERASED-{uuid}`.

---

##### `GET /examiner/settings`

**Response `200`:**

```json
{
  "data": {
    "retention_days_completed": 730,
    "allow_examinee_retake": false,
    "question_selection_mode": "FIXED_ORDER"
  }
}
```

##### `PATCH /examiner/settings`

Partial update of institution configuration. Audit-logged.

---

### 9.7 API Error Catalogue

All error responses use **RFC 7807** `application/problem+json`:

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "One or more fields failed validation.",
  "instance": "/api/v1/auth/examinee/entry",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "errors": [
    { "field": "prn", "message": "PRN must contain only letters and numbers, up to 20 characters." }
  ]
}
```

| HTTP | Problem `type` suffix | When |
|---|---|---|
| `400` | `validation-error` | Request body/query invalid |
| `401` | `unauthenticated` | Missing or expired session cookie |
| `403` | `forbidden` | Authenticated but wrong role or IDOR |
| `404` | `not-found` | Resource does not exist |
| `409` | `conflict` | Stale concurrency, duplicate submit, exam completed, bank minimum |
| `423` | `locked` | Examiner account lockout |
| `429` | `rate-limit-exceeded` | Rate limit (includes `Retry-After` header) |
| `500` | `internal-error` | Unexpected server error (generic detail in production) |
| `503` | `service-unavailable` | Insufficient question bank, dependency down |

**Security note:** `403` vs `404` for cross-tenant access: use `404` for Examinee accessing another's `sessionId` to avoid enumeration (configurable policy; default **404**).

---


## 10. User Flows

### 10.1 Examinee Test Flow

```
[Open Platform]
      │
      ▼
[Select: Login as Examinee]
      │
      ▼
[Enter PRN + Full Name + Acknowledge Privacy Notice]
      │
      ├── Validation Fails ──► [Show accessible inline error (aria-live)]
      ├── Already COMPLETED (retake off) ──► [409 — generic error message]
      │
      ▼ Validation Passes (new or resume ACTIVE)
[POST /auth/examinee/entry → 50 SessionQuestions created or resumed]
[HttpOnly session cookie issued]
      │
      ▼
[Load Question 1 of 50]
(Focus moves to question heading — WCAG 2.4.3)
      │
      ▼
[Read Question → Select Option A/B/C/D]
(Radio group in <fieldset>/<legend>; auto-save response to server)
      │
      ├── [Click / Keyboard: Next] ──► [Load Question N+1; focus to heading]
      │
      ├── [Click / Keyboard: Previous] ──► [Load Question N-1; focus to heading]
      │        (aria-disabled="true" on Q1 — remains focusable)
      │
      └── [Click / Keyboard: End Test]
                │
                ▼
      [Modal Dialog opens; focus trapped inside]
      [aria-live announces "X of 50 answered. Confirm end test?"]
                │
         ┌──────┴──────┐
      [Cancel / Esc]  [Confirm]
         │                │
         ▼                ▼
   [Modal closes;   [Server closes session;
   focus returns    computes score server-side]
   to End Test btn]       │
                          ▼
               [Display Score Summary]
               (aria-live="assertive" announces score)
                          │
                          ▼
               [Optional: Review Responses (read-only)]
```

### 10.2 Examiner Management Flow

```
[Open Platform]
      │
      ▼
[Select: Login as Examiner]
      │
      ▼
[Enter Username + Password]
      │
      ├── Auth Fails ──► [Generic error: "Invalid username or password"]
      │                  [Increment failed attempt counter; lock after 5]
      │
      ▼ Auth Passes
[Server issues new session token (session fixation prevention)]
[Audit log: login success]
      │
      ▼
[Examiner Dashboard]
      │
      ├── [View Question Bank]
      │         │
      │         ├── [Add Question]
      │         │       ──► [Fill Form (sanitised server-side on save)]
      │         │       ──► [Save] ──► [Question Added; audit logged]
      │         │
      │         ├── [Edit Question]
      │         │       ──► [Modify Fields]
      │         │       ──► [Save] ──► [Version archived; audit logged]
      │         │
      │         └── [Delete Question]
      │                 ──► [Confirm Dialog]
      │                 ──► [Soft-delete; audit logged]
      │                 ──► [Warn if bank < 50 active questions]
      │
      └── [View Results]
                │
                └── [Select Examinee Record]
                        ──► [View Response Detail; access audit logged]
```

---

## 11. Assumptions & Constraints

### 11.1 Assumptions

- Each Examinee takes the test **once per PRN** by default; retakes require `allow_examinee_retake: true` in PlatformSettings (§3.1.5).
- The system **enforces** a minimum of 50 active questions before session creation (§3.6.5); Examiners are warned on delete when count would fall below 50.
- Question order follows `question_selection_mode`: default **FIXED_ORDER** (same 50 questions and order for all Examinees when the bank has exactly 50+ active questions sorted by ID); **RANDOM_SAMPLE** is optional per institution.
- There is **no per-question or overall exam timer** in v1.0; only session **inactivity** (4 hours) and **absolute** (24 hours) expiry apply (§3.6.2).
- The platform operator is the **Data Controller** under GDPR and is responsible for the privacy notice, **LIA**, and **DPIA** (if required) before production.
- Retention days for completed tests are configurable (default 730) and communicated in the privacy notice.
- Examinee identity (PRN + Name) is accepted as sufficient for v1.0 with documented risk acceptance (§3.1.5).
- Environments: **development**, **staging** (production-like, anonymised data), and **production**; staging must not use production PII.

### 11.2 Constraints

- The test must consist of **exactly 50 questions** per attempt.
- Each question must have **exactly four options** with **exactly one correct answer** designated.
- No negative marking in v1.0.
- Role boundaries are strictly enforced server-side — client-side checks are advisory only.
- Real-time answer feedback during the test is **explicitly out of scope**.
- PRN and Name must never appear in application logs.
- Score computation must never be delegated to the client.

---

## 12. Out of Scope (v1.0)

The following features are acknowledged but deferred to future versions:

- Timed examinations / countdown timer *(Note: if added in v2, WCAG 2.2.1 timing adjustable must be implemented)*
- Multiple correct answers per question (multi-select MCQ)
- Automatic proctoring or anti-cheating measures
- Email notifications or automated result sharing
- Integration with external LMS (Learning Management Systems)
- Bulk question import via CSV / Excel *(Note: if added, file upload security controls — OWASP file upload guidelines — must be applied)*
- Detailed analytics or performance dashboards
- Mobile native application (iOS / Android)
- Password reset / account recovery flow for Examiners
- Multi-Factor Authentication (MFA) for Examiner login *(strongly recommended for v2)*
- CAPTCHA on login / registration endpoints *(recommended for v2)*

### 12.1 Pre-Production Compliance Gates (Mandatory)

The following are **not** optional deferrals — they must be completed before production go-live:

| Gate | Owner | Evidence |
|---|---|---|
| **DPIA** (if high-risk processing) | Data Controller | Signed DPIA document |
| **LIA** (if lawful basis is legitimate interests) | Data Controller | Signed LIA document |
| **DPA** with hosting vendor (if applicable) | Data Controller | Executed agreement |
| **Penetration test** | Security lead | Report with no open Critical/High issues |
| **Load test** (NFR-02) | Engineering | k6/Locust report meeting p95 targets |

---

## 13. Acceptance Criteria

### 13.1 Test-Taking (Functional)

- [ ] An Examinee can register with PRN and Name after acknowledging the privacy notice
- [ ] No correct/incorrect indicator appears at any point during an active test session
- [ ] The `correct_option` field is absent from all API responses during an active session
- [ ] Previous button is keyboard-focusable and announces `aria-disabled` on Question 1; Next on Question 50
- [ ] Previous and Next buttons navigate correctly; focus moves to the question heading on each navigation
- [ ] Answers auto-save to the server on selection; no answer is lost if the user navigates away
- [ ] Answers can be changed freely before End Test is clicked
- [ ] End Test opens a modal dialog; focus is trapped within the modal; Escape closes it
- [ ] On confirmation, score is computed server-side and matches the actual correct answer count
- [ ] `POST /auth/examinee/entry` resumes ACTIVE session; returns `409` when COMPLETED and retake disabled
- [ ] Session creation fails with `503` when active question bank &lt; 50
- [ ] `Response.is_correct` is NULL during ACTIVE session; populated only after submit
- [ ] Auto-save failure shows retry UI; successful retry persists answer (NFR-14)
- [ ] Concurrent tab updates resolve via `If-Unmodified-Since` without data loss

### 13.2 Scoring & Results

- [ ] Score screen correctly shows total score, correct count, incorrect count, and unattempted count
- [ ] Score cannot be manipulated by altering client-side requests
- [ ] Unanswered questions do not penalise the Examinee

### 13.3 Data Persistence

- [ ] All 50 response records (including nulls for unanswered) are stored after session close
- [ ] 50 `SessionQuestion` rows exist per session with frozen `question_version_snapshot`
- [ ] Each response links to a `SessionQuestion` question_id
- [ ] The Examinee can review only their own responses post-submission (IDOR verified)
- [ ] The Examiner can view any past test attempt; access is audit-logged

### 13.4 Question Management

- [ ] Examiner can add a question; it appears in the bank immediately
- [ ] Examiner can edit a question; a version archive record is created; audit log entry written
- [ ] Examiner can soft-delete a question with confirmation; it does not appear in new sessions
- [ ] System warns Examiner if active question count would fall below 50
- [ ] `DELETE /examiner/questions/{id}` returns `409` when active count would fall below 50

### 13.5 Security (OWASP)

- [ ] Examiner login returns a generic error on invalid credentials (does not differentiate username vs. password)
- [ ] Examiner account is locked for 15 minutes after 5 consecutive failed attempts
- [ ] All authenticated API routes return 401/403 when called without a valid session token
- [ ] An Examinee session cannot access `/api/v1/examiner/*` endpoints (returns 403)
- [ ] An Examiner session cannot access another Examinee's session data (IDOR check)
- [ ] Session token is issued as HttpOnly, Secure, SameSite=Strict cookie
- [ ] A new session token is issued on login (session fixation prevention)
- [ ] All responses include required security headers (CSP, HSTS, X-Frame-Options, etc.)
- [ ] TLS 1.0 and 1.1 are disabled; TLS 1.2+ enforced
- [ ] Dependency scan passes with no Critical or High CVEs
- [ ] HTML output is entity-encoded; no stored XSS via question text
- [ ] SQL injection attempt on login and registration inputs is rejected

### 13.6 Privacy (GDPR)

- [ ] Privacy notice is displayed and must be acknowledged before registration proceeds
- [ ] PRN and Name do not appear in any application log entry
- [ ] A designated administrator can process a Right to Erasure request; PRN and Name are replaced with an anonymised token
- [ ] Examinee can self-export via `GET /examinee/me/data-export` (JSON)
- [ ] Examiner erasure endpoint returns `202` and anonymises PRN/Name in stored records
- [ ] Configurable `retention_days_completed` is enforced by scheduled job

### 13.7 Accessibility (WCAG 2.1 AA)

- [ ] Automated accessibility scan (axe-core) reports **zero critical or serious** violations; minor/documented exceptions listed in release notes
- [ ] All interactive elements are reachable and operable via keyboard alone
- [ ] All text meets the 4.5:1 colour contrast ratio (3:1 for large text and UI components)
- [ ] Radio button groups are wrapped in `<fieldset>` + `<legend>`
- [ ] Modal dialog traps focus correctly; Escape dismisses it and returns focus to the trigger
- [ ] Screen reader test (NVDA + Firefox) confirms question text, options, progress, and score are all announced correctly
- [ ] Page title updates on each question navigation (e.g., "Question 7 of 50 – MCQ Test Platform")
- [ ] "Skip to main content" link is the first focusable element on all pages
- [ ] Content reflows correctly at 320px viewport width
- [ ] Status messages (auto-save confirmation, progress updates) are announced via `aria-live`

### 13.8 Audit & Logging

- [ ] Login success and failure events are recorded in the audit log with `user_id`, timestamp, and IP
- [ ] Question add, edit, and delete events are recorded with actor identity
- [ ] Examiner access to Examinee response detail is recorded in the audit log
- [ ] Audit log entries cannot be modified or deleted via any application interface

### 13.9 API & Operations

- [ ] OpenAPI 3.1 spec at `/api/v1/openapi.json` matches implemented §9.6 endpoints
- [ ] All error responses use RFC 7807 `application/problem+json` with `request_id`
- [ ] Contract/integration tests pass for auth, test flow, submit idempotency, and IDOR cases
- [ ] Load test: 100 concurrent sessions meet NFR-02 p95 and error-rate targets
- [ ] Monthly backup restore drill documented (NFR-13, NFR-16)

---

## 14. Revision History

| Version | Date | Changes | Author |
|---|---|---|---|
| 1.0 | June 3, 2026 | Initial draft | Product Team |
| 2.0 | June 3, 2026 | Full architect review: added OWASP Top 10 security controls, GDPR privacy requirements, WCAG 2.1 AA accessibility requirements, audit/logging section, revised data model with versioning and soft-delete, corrected IDOR vulnerabilities, added session management spec, updated acceptance criteria | Software Architect |
| 2.1 | June 3, 2026 | Gap closure: exam session rules (§3.6), unified Examinee entry/resume/retake, SessionQuestion model, is_correct policy, technology stack (§9.5), REST API contracts (§9.6–9.7), server-side sessions, GDPR/LIA/DPA gates, NFR-16–18, expanded acceptance criteria | Senior API Architect |

---

*— End of Document — v2.1*
