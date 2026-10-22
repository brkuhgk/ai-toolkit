---
name: ideal-candidate-resume
description: 'Build a fictional benchmark "ideal candidate" resume for a job description: the profile that would get hired. Covers 100% of the JD keywords while obeying hard constraints (limited years of experience, specific companies, date ranges), uses the job-relevant demographics provided or assumes them, and iterates until an evidence report proves the fit. Outputs Markdown by default; DOCX or PDF on request. Use when: ideal resume, ideal candidate, who would get hired, benchmark resume, perfect candidate profile, winning resume for a JD, hiring bar, or comparing a real resume against the ideal.'
argument-hint: 'Paste the JD; optional: demographics, constraints (years / companies / date range), output format (md | docx | pdf)'
---

# Ideal Candidate Resume (Benchmark)

Create a **fictional, hire-ready benchmark resume** for a job description (JD), with an
**evidence report** that proves, item by item, why this candidate would be hired. The
resume must meet every hard constraint and still cover every JD keyword.

> Tailoring the user's **real** resume to a JD is a different job. Use the
> `tailor-resume` skill for that. This skill invents a benchmark profile. Never present
> it as a real person.

## When to Use

- "Create the ideal resume / ideal candidate for this job."
- "Who would get hired for this JD?" / "What does the hiring bar look like?"
- Building a benchmark to compare a real resume against (gap analysis).
- The same request, but with limits: "only 4 years of experience", "must have worked at
  X", "career between 2015 and 2022", "output as PDF".

## Inputs

| Input | Required | Default when missing |
|---|---|---|
| Job description (text, file, or URL) | **Yes**: ask if it is missing | — |
| Demographics (job-relevant attributes) | No | Assume them with [demographics.md](./references/demographics.md) |
| Constraints (years, companies, dates, etc.) | No | The [defaults block](#constraints-edit-defaults-here) below |
| Output format: `md`, `docx`, `pdf` (any combination) | No | `md` only |
| Output name / folder | No | `Ideal_Candidate_Resume_<Company>_<Role>` in the workspace root |
| "As-of" date | No | JD posted date if shown, otherwise today. Used for "Present". |

Constraints in the user's message **override** the defaults block for that run. If the
user asks to change a default permanently, edit the YAML block below.

## Constraints (edit defaults here)

Hard constraints are **never broken**. `null` means "derive from the JD".

```yaml
experience:
  min_years: null          # e.g. 3. null = JD minimum
  max_years: null          # e.g. 5. null = JD minimum + 4 (avoid looking overqualified)
companies:
  required: []             # employers that MUST appear, e.g. ["Capital One"]
  excluded: []             # employers that must NEVER appear, e.g. ["Citi"]
  allow_real_names: false  # false = credible fictional employers, e.g. "Lone Star Financial (Tier-1 U.S. bank)"
  employer_profile: null   # e.g. "Fortune 500 financial services", "Big 4 consulting"
timeline:
  earliest_start: null     # YYYY-MM. No experience may start before this date
  latest_end: present      # YYYY-MM or present. No experience may end after this date
  max_roles: 4             # max number of positions in PROFESSIONAL EXPERIENCE
  max_gap_months: 3        # max gap between consecutive roles
education:
  degree: null             # null = degree the JD requires, in the most relevant major
  graduation_year: null    # null = consistent with the timeline
certifications:
  required: []             # e.g. ["AWS Certified Developer - Associate"]
  max: 4
resume:
  max_pages: 2
  max_bullets_per_role: 8
  candidate_name: null     # null = placeholder name such as "Alex Morgan"
```

### Precedence (when goals collide)

1. **Hard constraints**: the block above plus the user's per-request constraints.
2. **JD requirements** (`REQ`): must-have skills, tools, years, degree.
3. **JD responsibilities** (`RESP`).
4. **JD preferred / "nice to have" items** (`PREF`), e.g. "AWS is a significant advantage".
5. **Differentiators** (`SIG`): domain, culture, and company-specific signals.

Rules for satisfying the JD *inside* the constraints:

- **Fit every keyword into the allowed window.** If years are capped, pack more JD scope
  into each role (wider ownership, more modern stack) instead of adding roles or years.
- **Required companies** become real employers on the resume. Bullets there stay generic
  and believable. Never invent confidential facts, internal system names, or claims that
  sound like news about a real company.
- **Excluded companies** must not appear anywhere in the resume block, including as
  clients or partners.
- **Date range**: every role, certification, and education date must fit the window.
  Respect [temporal plausibility](./references/evidence-report.md#temporal-plausibility):
  never claim a tool or version before it existed.
- **Impossible combinations** (e.g. JD asks for 5+ years but `max_years: 3`): do **not**
  break the constraint. Record a **Constraint Conflict** in the evidence report with the
  strongest legal mitigation (e.g. depth/intensity of experience, certifications,
  internships or projects, if the timeline allows). Then keep going.

## Procedure

Work through every step. Steps 6 to 8 repeat until the evidence gate passes.

### 1. Intake

- Read the JD. Capture company, role title, Req ID, locations, work model, posted date.
- Merge the constraints: user's message > YAML defaults. List the final constraints.
- Collect any demographics the user gave. Note the requested output formats.
- Ask the user **only** if the JD is missing. Otherwise assume and document.

### 2. JD inventory (the checklist)

Pull out every item and give it an ID:

- `REQ-n`: requirements and qualifications, **one technology or skill per item**.
  Split compound lines: "Maven, Gradle, Docker, Jenkins, OpenShift" becomes 5 items.
- `RESP-n`: each responsibility or duty.
- `PREF-n`: preferred, "a plus", "significant advantage".
- `SIG-n`: implicit signals: industry, regulation, scale, culture words, company
  products, location/work model, seniority level.

Write a keyword file in the
[keyword file format](./references/evidence-report.md#keyword-file-format) to
`<basename>.keywords.txt` next to the output. Include synonyms (`React | React.js`).
Use the JD's **exact wording** as the first term on each line.

### 3. Resolve the candidate profile

Follow [demographics.md](./references/demographics.md). For every attribute, record its
value, its source (`Provided` / `Assumed` / `Constraint`), and the rationale. **Never use
protected characteristics**, even if the user supplies them.

### 4. Plan the career arc (before writing bullets)

- Decide the roles (count ≤ `max_roles`), titles, employers, locations, and dates.
  Check them against the constraints now; fixing dates later is expensive.
- Show a believable progression (e.g. Engineer → Engineer II → Senior), ending at or
  just above the target level.
- **Assign every `REQ`, `RESP`, and `PREF` item to at least one role.** The JD's core
  stack goes in the **most recent role**. Repeat the most important items across roles.
- Put at least one role in the hiring company's industry (`SIG`) unless constraints
  prevent it.

### 5. Draft the Markdown

Copy [the resume template](./assets/resume-template.md) and fill it in. Keep the
`<!-- RESUME:START/END -->` and `<!-- EVIDENCE:START/END -->` markers. The scripts
depend on them.

Bullet formula: **action verb + JD wording + technology + measurable result**.
For example: "Built **high-performance RESTful APIs** with **Spring Boot 3** and Oracle 19c,
cutting p95 latency from 820 ms to 210 ms."

- Every `REQ` technology appears in an **experience bullet**, not only in the skills list.
- Use the JD's literal phrases, e.g. "Root Cause Analysis", "Event-Driven Services".
- Name skills categories after the JD's requirement headings.
- At least about 70% of bullets carry a metric (%, $, time, volume, count, SLA).
  Keep metrics believable for the level and company size.
- Keep the resume block ATS-safe: a single column, standard headings, no tables,
  text boxes, images, or emoji.
- Respect `max_bullets_per_role` and `max_pages` (a 2-page resume is roughly 900–1,100 words).

### 6. Validate (deterministic)

Run [validate_resume.py](./scripts/validate_resume.py) on the resume block. Pass the
constraints you actually used. `<SKILL_DIR>` is the absolute path of the folder that holds
this SKILL.md (e.g. `<repo>/.github/skills/ideal-candidate-resume` for a project install,
`~/.copilot/skills/ideal-candidate-resume` for a personal install, or the plugin cache
folder when the skill comes from a plugin):

```powershell
python <SKILL_DIR>/scripts/validate_resume.py <basename>.md `
  --keywords <basename>.keywords.txt --as-of 2026-10 `
  --min-years 5 --max-years 8 --earliest-start 2017-06 --latest-end present `
  --require-company "Capital One" --exclude-company "Citi" `
  --max-roles 4 --max-gap-months 3 --max-bullets-per-role 8
```

The validator reports each keyword as `DEMONSTRATED` (in experience), `CREDENTIAL`
(education/certifications), `MENTIONED` (summary/header only), `LISTED` (skills only), or
`MISSING`. It also checks dates, total years, gaps, role count, companies, metric ratio,
and leftover `{{placeholders}}`. Exit code `0` means everything passed.

If Python can't run, do the same checks by hand with text search and state that in the report.

### 7. Evidence audit (judgment)

Fill in the evidence block using [evidence-report.md](./references/evidence-report.md):

- Every `REQ`, `RESP`, and `PREF` gets an **exact quote** from the resume, where it is,
  and a strength grade (`Strong` / `Adequate` / `Weak` / `Missing`).
- Constraint compliance, temporal plausibility, the recruiter knockout screen,
  "Why this candidate gets hired", and any constraint conflicts.

### 8. Iterate until the evidence gate passes

Check the [evidence gate](./references/evidence-report.md#evidence-gate). If any item
fails:

1. Fix the resume: rewrite or add bullets, move items into the most recent role, add
   metrics, or adjust dates within the constraints.
2. Re-run step 6 and update step 7.
3. Add a row to the **Iteration Log** (what failed → what changed).

Do not stop while a gate item fails. The only exception is a documented Constraint
Conflict. If the same item still fails after 5 iterations, it is a Constraint Conflict:
document it and move on.

### 9. Render the requested formats

The Markdown file is always the source of truth and is always delivered. For DOCX/PDF, run
[render_resume.py](./scripts/render_resume.py):

```powershell
python <SKILL_DIR>/scripts/render_resume.py <basename>.md --formats docx,pdf
# Options: --out-dir DIR --basename NAME --include-evidence --font "Calibri" --font-size 10.5
```

- By default the DOCX/PDF contains **only the resume block** (ready to share). Add
  `--include-evidence` to append the profile, constraints, and evidence report after a
  page break.
- PDF uses Microsoft Word (via `pip install docx2pdf`) or LibreOffice. If neither is
  available, deliver the DOCX and tell the user how to enable PDF export.
- Requires `pip install python-docx`.

### 10. Report to the user

Keep it short:

- Output file paths. Final gate status and iteration count.
- The 3–5 strongest pieces of evidence ("why hired").
- Key assumptions (location, years, domain) and any Constraint Conflicts with their mitigation.
- Delete `<basename>.keywords.txt` unless the user wants to keep it.

## Output Files

| File | When |
|---|---|
| `<basename>.md`: profile, constraints, resume, evidence report | Always |
| `<basename>.docx` | `docx` requested |
| `<basename>.pdf` | `pdf` requested (built from a temporary DOCX when `docx` is not also requested) |

`<basename>` defaults to `Ideal_Candidate_Resume_<Company>_<Role>` (no spaces).

## Guardrails

- Label the document as a **fictional benchmark** at the top. Use a placeholder name and
  contact details: `(555) 010-xxxx`, `@example.com`, and `-example` profile URLs.
- Use **job-relevant attributes only**. Never include or rely on age or date of birth,
  gender, race, ethnicity, religion, national origin, marital/family status, pregnancy,
  disability, sexual orientation, veteran status, or a photo, even if the user supplies
  them. Explain briefly why they were left out.
- Real employer names only when `companies.required` or `allow_real_names` asks for them.
  Keep the claims generic.
- No invented credentials that don't exist. Certifications must be real programs that
  existed by the date claimed.
- Metrics must be believable for the role level and company size. No "10x everything".
