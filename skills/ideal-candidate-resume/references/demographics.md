# Demographics: Consume or Assume

Here, "demographics" means **job-relevant candidate attributes** only: things an
employer can legitimately weigh. Use what the user provides. Assume everything else, using
the defaults below, and record every value in the **Assumed Candidate Profile** table.

## 1. Consume (when provided)

| Attribute | Where it is used | Example input |
|---|---|---|
| Location / metro | Contact line, employer locations, on-site fit | "Dallas–Fort Worth", "Jersey City" |
| Relocation willingness | Profile table; a "Relocating to <city>" line if not local | "Open to relocate to Tampa" |
| Work authorization | Profile table only (not on the resume unless the JD asks) | "US citizen", "Green card", "H-1B" |
| Total years of experience | Career arc, summary sentence | "6 years" |
| Career level | Titles and scope | "Mid-level", "Senior", "Lead" |
| Education | EDUCATION section | "M.S. Computer Science" |
| Industry / domain background | Employer choice, bullet context | "Banking", "Healthcare" |
| Security clearance | Header line / profile | "Active Secret" |
| Languages spoken | Optional LANGUAGES line if the JD values it | "Spanish (fluent)" |
| Work-model availability | Profile table; header note when relevant | "On-site 5 days" |
| Career-change / non-traditional path | Arc design (bootcamp, prior field) | "Former Data analyst" |

## 2. Assume (when not provided)

| Attribute | Default assumption | Rationale to record |
|---|---|---|
| Location | The JD's **primary** location (or the first one listed) | No relocation risk; fits an on-site or hybrid schedule |
| Work authorization | Authorized to work in the JD's country; no sponsorship needed | Removes a common screening knockout |
| Years of experience | JD minimum **+2 to 4 years** (e.g. "3+" becomes 5–7), within constraints | Clears the bar with headroom without looking overqualified |
| Career level | At, or one step above, the level the JD implies | Ready on day one, and fits the pay band |
| Education | The degree the JD requires, in the most relevant major, from a credible school near the location | Meets the knockout; local ties |
| Graduation year | Consistent with the career arc (usually the start of the first role minus 0–3 months) | Timeline plausibility |
| Domain | The hiring company's industry for at least one role (more recent roles are better) | Shorter ramp-up; knows the regulatory context |
| Employers | Credible fictional names with a descriptor, e.g. "(Tier-1 U.S. Companies)" |Feel free to use real companies |
| Certifications | 2–3 real certifications that map to the JD stack and existed when earned | Third-party proof of key skills |
| Languages | English, professional fluency | Default for U.S. roles |
| Clearance | None, unless the JD requires one | Don't add unneeded claims |
| Work model | Available for exactly the JD's model | Removes a logistics objection |
| Salary expectations | Never stated | Not a resume field |

## 3. Record every value

Add one row per attribute to the profile table at the top of the output:

| Attribute | Value | Source | Rationale |
|---|---|---|---|
| Location | Irving, TX | Assumed | JD primary location; the role is On-Site/Resident |
| Years of experience | 4 | Constraint | `max_years: 4` (JD asks 3+) |
| Domain | Banking | Provided | User: "candidate is from banking" |

`Source` is one of `Provided`, `Assumed`, or `Constraint`.

## 4. Resolving conflicts

- **Provided vs. constraint**: the constraint wins. Log it under Constraint Conflicts.
- **Provided vs. JD** (e.g. location is Chicago, but the role is on-site in Irving): keep
  the provided value, then mitigate. Add "Relocating to Irving, TX (available
  <month>)" to the header and note the risk in the evidence report.
- **Assumed vs. constraint**: adjust the assumption silently and record the constraint as
  the source.

## 5. Never use (protected characteristics)

Do **not** include, infer, or optimize for any of these, even if the user supplies them:
age or date of birth, gender or gender identity, race, ethnicity, color, religion,
national origin or citizenship country (only work-authorization *status* is allowed),
marital or family status, pregnancy, disability or health, sexual orientation, genetic
information, veteran or military status (unless the JD explicitly targets a veteran
program and the user asks), photo, height or weight.

If any of these are supplied, say in one line that they were left out because hiring
decisions must not depend on them. Do not use graduation year as a proxy for age. Set it
only from the career timeline.
