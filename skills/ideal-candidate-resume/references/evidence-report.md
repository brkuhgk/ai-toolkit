# Evidence Report: Format, Grading, and Gate

The evidence report sits between `<!-- EVIDENCE:START -->` and `<!-- EVIDENCE:END -->`
in the output Markdown. It must prove the fit with **quotes from the resume block**. A
general claim like "the candidate has strong Java skills" is not evidence.

## Keyword File Format

Plain text, one JD item per line. Used by `scripts/validate_resume.py`.

```text
# Lines that start with # are comments. Blank lines are ignored.
# PRIORITY | primary term (exact JD wording) | synonym | synonym ...
R | Java
R | React | React.js | ReactJS
R | Spring Boot
R | Oracle
R | PL/SQL
R | end-to-end tests | E2E tests | end-to-end testing
P | AWS | Amazon Web Services
GitHub Enterprise
```

- `R` = required (it fails if missing or only listed in skills). `P` = preferred (only a
  warning if missing).
- A line with no priority field means **required**.
- Matching ignores case. Spaces and hyphens are interchangeable
  (`event-driven` = `event driven`), and terms must sit on word boundaries
  (`Java` does not match `JavaScript`).
- One technology per line. Put soft skills and responsibilities in as short phrases
  (`root cause analysis`, `pair programming`, `acceptance criteria`).

## Strength Grading

| Grade | Definition |
|---|---|
| **Strong** | In an experience bullet, using the JD's wording, with a concrete action **and** a metric or a clear scope (scale, users, volume) |
| **Adequate** | In an experience bullet without a metric, **or** shown in the summary/credentials with clear context |
| **Weak** | Only in the TECHNICAL SKILLS list, or only implied |
| **Missing** | Not present in the resume block |

## Evidence Gate

The resume is done only when **all** of these are true:

1. No `REQ` item is `Missing` or `Weak`.
2. Every `RESP` item is `Strong`.
3. Every `PREF` item is at least `Adequate`, unless a documented constraint conflict prevents it.
4. Every hard constraint shows `PASS` in the Constraint Compliance table.
5. `validate_resume.py` exits with `0` (or the manual equivalent is documented).
6. The JD's core stack (the first 3–5 named technologies) appears in the **most recent role**.
7. At least about 70% of experience bullets contain a metric.
8. Temporal plausibility passes for every dated claim.
9. The recruiter knockout screen passes, or each risk is mitigated.
10. Each remaining gap is listed under Constraint Conflicts with its mitigation.

## Report Sections (in this order)

### 1. Verdict

One paragraph: hire recommendation, overall coverage
(`REQ x/x Strong`, `RESP x/x Strong`, `PREF x/x`), iteration count, and conflicts.

### 2. Why This Candidate Gets Hired

The 5–7 strongest reasons. Each reason ties a hiring-manager concern to a resume quote:

| # | Hiring-manager concern | Evidence (resume quote) | JD items |
|---|---|---|---|
| 1 | "Can they ship on our exact stack?" | "...Java 21, Spring Boot 3, React 18/TypeScript, and Oracle 19c..." | REQ-1..4 |

### 3. Recruiter Knockout Screen

| Screen question | Answer from the resume | Result |
|---|---|---|
| Meets the minimum years? | 7 yrs (JD: 3+) | PASS |
| Required degree? | B.S. Computer Science | PASS |
| Location / work model? | Irving, TX; on-site | PASS |
| Work authorization? | Authorized, no sponsorship (profile) | PASS |
| Core tech in recent role? | Yes, current role | PASS |

### 4. Constraint Compliance

| Constraint | Required | Actual | Result |
|---|---|---|---|
| Years of experience | 3–5 | 4.8 | PASS |
| Required company | Capital One | Role 2 | PASS |
| Date window | 2018-01 → present | Jun 2019 → present | PASS |

### 5. Requirements Evidence Matrix

| ID | JD wording | Resume evidence (exact quote) | Location | Strength |
|---|---|---|---|---|
| REQ-1 | Java | "Built Java 21 / Spring Boot 3 services..." | Role 1, bullet 1 | Strong |

### 6. Responsibilities Evidence Matrix

The same columns, with `RESP-n` items.

### 7. Preferred and Signals

The same columns, with `PREF-n` and `SIG-n` items (domain, scale, culture, location).

### 8. Keyword Validator Summary

Paste the summary lines from `validate_resume.py` (counts by status, constraint results,
and the final RESULT line). Don't paste the full listing unless something failed.

### 9. Temporal Plausibility

| Claim | Role / date claimed | Release / availability | Result |
|---|---|---|---|
| Spring Boot 3 | Mar 2023 – Present | Nov 2022 | PASS |

### 10. Constraint Conflicts and Mitigations

| JD item | Constraint that blocks it | Mitigation used | Residual risk |
|---|---|---|---|
| "5+ years" | `max_years: 4` | Dense scope, CKAD + OCP certs, lead-level ownership | Medium |

Write "None" if there are no conflicts.

### 11. Iteration Log

| Iteration | Validator | Gate failures | Changes made |
|---|---|---|---|
| 1 | FAIL (2) | REQ-12 GraphQL only LISTED; 61% metrics | Added GraphQL gateway bullet to Role 1; added metrics to 4 bullets |
| 2 | PASS | — | — |

## Temporal Plausibility

Never claim a technology, version, or certification before it was publicly available.
Allow about 6 months of adoption lag for enterprise use of a brand-new major version.
Reference dates:

| Technology | Available |
|---|---|
| Java 8 / 11 / 17 / 21 | Mar 2014 / Sep 2018 / Sep 2021 / Sep 2023 |
| Spring Boot 2.0 / 3.0 | Mar 2018 / Nov 2022 |
| Spring for GraphQL 1.0 | May 2022 |
| React (open source) / Hooks (16.8) / React 18 | May 2013 / Feb 2019 / Mar 2022 |
| Angular (2+) | Sep 2016 |
| TypeScript | Oct 2012 |
| Next.js | Oct 2016 |
| Docker | Mar 2013 |
| Kubernetes 1.0 | Jul 2015 |
| Red Hat OpenShift 4 | mid-2019 |
| AWS Lambda / Amazon EKS GA | Nov 2014 / Jun 2018 |
| GraphQL (public release) | 2015 |
| Apache Kafka 1.0 | Nov 2017 (open source since 2011) |
| JUnit 5 | Sep 2017 |
| Playwright | Jan 2020 |
| GitHub Actions GA | Nov 2019 |
| GitHub Copilot: preview / GA / Business / Enterprise | Jun 2021 / Jun 2022 / Feb 2023 / Feb 2024 |
| ChatGPT / GPT-4 | Nov 2022 / Mar 2023 |
| Azure OpenAI Service GA / Amazon Bedrock GA | Jan 2023 / Sep 2023 |
| LangChain | Oct 2022 |
| Model Context Protocol (MCP) | Nov 2024 |
| Oracle Database 19c / 23ai | 2019 / 2024 |

For anything not listed, check the release date before claiming it, or claim it only in
the most recent role.
