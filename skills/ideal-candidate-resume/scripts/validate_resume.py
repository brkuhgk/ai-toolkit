#!/usr/bin/env python3
"""Validate an ideal-candidate resume (Markdown) against JD keywords and hard constraints.

Only the text between <!-- RESUME:START --> and <!-- RESUME:END --> is checked, so the
evidence report can never satisfy a keyword on its own.

Keyword status (the best location wins):
  DEMONSTRATED  found in PROFESSIONAL EXPERIENCE / PROJECTS (role headers or bullets)
  CREDENTIAL    found in EDUCATION / CERTIFICATIONS
  MENTIONED     found only in the header, summary, or another section
  LISTED        found only in the skills section (weak evidence)
  MISSING       not found

Exit codes: 0 = every check passed, 1 = at least one check failed, 2 = usage/input error.

Example:
  python validate_resume.py Ideal_Candidate_Resume_Citi_FSE.md --keywords kw.txt
      --min-years 5 --max-years 8 --earliest-start 2017-06 --latest-end present
      --require-company "Capital One" --exclude-company "Citi" --max-roles 4 --as-of 2026-10
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

RESUME_START = "<!-- RESUME:START -->"
RESUME_END = "<!-- RESUME:END -->"
PRESENT_WORDS = {"present", "current", "now", "today"}
DASH = "-\u2013\u2014"  # hyphen, en dash, em dash (keep first inside [] classes)

_MONTH_NAMES = ("january", "february", "march", "april", "may", "june", "july",
                "august", "september", "october", "november", "december")
MONTHS = {}
for _index, _name in enumerate(_MONTH_NAMES, start=1):
    MONTHS[_name] = _index
    MONTHS[_name[:3]] = _index
MONTHS["sept"] = 9

DATE_RANGE = re.compile(
    r"\b([A-Za-z]{3,9})\.?\s+(\d{4})\s*(?:[" + DASH + r"]+|to)\s*"
    r"(?:([A-Za-z]{3,9})\.?\s+(\d{4})|(present|current|now|today))\b",
    re.IGNORECASE,
)
YEAR_RANGE = re.compile(
    r"\b((?:19|20)\d{2})\s*(?:[" + DASH + r"]+|to)\s*((?:19|20)\d{2}|present|current|now|today)\b",
    re.IGNORECASE,
)
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
COMPANY_LINE = re.compile(r"^\*\*(.+?)\*\*")
LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
PLACEHOLDER = re.compile(r"\{\{[^{}]*\}\}")
TERM_SEPARATOR = re.compile("[" + DASH + r"\s]+")
TERM_JOINER = "[" + DASH + r"\s]+"
YEAR_TOKEN = re.compile(r"\b(?:19|20)\d{2}\b")
# Version-like tokens ("Java 21", "Oracle 19c", "HTML5", "OAuth2", "S3") are not metrics.
VERSION_TOKEN = re.compile(
    r"\b(?:Java|JDK|J2EE|Spring(?:\s+Boot)?|React|Angular|Vue|Node(?:\.js)?|Python|Oracle|ES|"
    r"ECMAScript|HTML|CSS|OAuth|JUnit|Gradle|Maven|Kafka|Jenkins|Windows|iOS|Android|TLS|HTTP|"
    r"IPv|WCAG|ISO|SOC|Top|Log4j|Hibernate|Bootstrap|Webpack|PostgreSQL|MySQL|Redis|MongoDB|"
    r"Kubernetes|OpenShift|Terraform|Kotlin|Scala|PHP|Ruby|Rails|Django|Next\.js|TypeScript|"
    r"Struts|Tomcat|WebSphere|WebLogic|Selenium|Cypress|Playwright|Jest|Mockito|(?-i:NET)|Rust|Swift|"
    r"RHEL|Ubuntu|DB|Level|Tier|Phase|"
    r"Release|Version|Section|SHA|AES|EC|S|C|K|L|P|v)"
    r"[\s/-]*\d+(?:\.\d+)*(?:[a-z]{1,2})?(?:/\d+(?:\.\d+)*)*\b",
    re.IGNORECASE,
)
METRIC_WORDS = re.compile(r"\b(?:zero|doubled|tripled|halved)\b", re.IGNORECASE)
SECTION_ABBR = {"experience": "exp", "credentials": "cred", "skills": "skills",
                "summary": "summary", "header": "header", "other": "other"}


@dataclass
class Keyword:
    priority: str
    terms: list
    patterns: list


@dataclass
class Role:
    title: str
    header: list = field(default_factory=list)
    bullets: list = field(default_factory=list)
    company: str = ""
    start: int = -1
    end: int = -1
    present: bool = False

    @property
    def dated(self) -> bool:
        return self.start >= 0 and self.end >= 0


class Checks:
    def __init__(self) -> None:
        self.rows = []

    def add(self, status: str, message: str) -> None:
        self.rows.append((status, message))

    def count(self, status: str) -> int:
        return sum(1 for s, _ in self.rows if s == status)


def month_index(year: int, month: int) -> int:
    return year * 12 + (month - 1)


def fmt(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def parse_ym(value: str) -> int:
    match = re.fullmatch(r"(\d{4})-(\d{1,2})", value.strip())
    if not match or not 1 <= int(match.group(2)) <= 12:
        raise ValueError(f"expected YYYY-MM, got '{value}'")
    return month_index(int(match.group(1)), int(match.group(2)))


def clean_md(text: str) -> str:
    text = LINK.sub(r"\1", text)
    text = text.replace("\\|", "|")
    return re.sub(r"[*`]", "", text)


def term_pattern(term: str) -> re.Pattern:
    words = [w for w in TERM_SEPARATOR.split(term.strip()) if w]
    body = TERM_JOINER.join(re.escape(w) for w in words) if words else re.escape(term.strip())
    return re.compile(r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])", re.IGNORECASE)


def classify(heading: str) -> str:
    h = heading.upper()
    if any(k in h for k in ("EXPERIENCE", "EMPLOYMENT", "WORK HISTORY", "PROJECT")):
        return "experience"
    if any(k in h for k in ("SKILL", "TECHNOLOG", "TOOLS")):
        return "skills"
    if any(k in h for k in ("SUMMARY", "PROFILE", "OBJECTIVE", "ABOUT")):
        return "summary"
    if any(k in h for k in ("EDUCATION", "CERTIF", "LICENSE", "TRAINING")):
        return "credentials"
    return "other"


def load_keywords(path: Path) -> list:
    keywords = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        priority = "R"
        if len(parts) > 1 and parts[0].upper() in {"R", "REQ", "REQUIRED", "P", "PREF", "PREFERRED"}:
            priority = "P" if parts[0].upper().startswith("P") else "R"
            parts = parts[1:]
        if not parts:
            raise ValueError(f"{path}:{line_no}: no keyword on this line")
        keywords.append(Keyword(priority, parts, [term_pattern(t) for t in parts]))
    return keywords


def extract_resume_block(text: str):
    start = text.find(RESUME_START)
    end = text.find(RESUME_END)
    if start == -1 or end == -1 or end < start:
        return text, False
    return text[start + len(RESUME_START):end], True


def parse_resume(block: str):
    sections = {k: [] for k in ("header", "summary", "skills", "experience", "credentials", "other")}
    roles = []
    current = "header"
    role = None
    in_comment = False
    for raw in block.splitlines():
        stripped = raw.strip()
        if in_comment:
            in_comment = "-->" not in stripped
            continue
        if stripped.startswith("<!--"):
            in_comment = "-->" not in stripped
            continue
        if not stripped:
            continue
        heading = HEADING.match(stripped)
        if heading:
            level, content = len(heading.group(1)), heading.group(2).strip()
            if level == 2:
                current = classify(content)
                role = None
            elif level >= 3 and current == "experience":
                title = clean_md(content).strip()
                if " | " in title and re.search(r"\d{4}|present|current", title.rsplit(" | ", 1)[1], re.I):
                    title = title.rsplit(" | ", 1)[0].strip()
                role = Role(title=title)
                role.header.append(content)
                roles.append(role)
                sections[current].append(content)
            else:
                sections[current].append(content)
            continue
        sections[current].append(stripped)
        if role is None:
            continue
        bullet = BULLET.match(raw)
        if bullet:
            role.bullets.append(bullet.group(1).strip())
            continue
        if not role.company:
            company = COMPANY_LINE.match(stripped)
            if company:
                role.company = clean_md(company.group(1)).strip()
        role.header.append(stripped)
    return sections, roles


def find_date_range(text: str, as_of: int):
    for match in DATE_RANGE.finditer(text):
        start_month = MONTHS.get(match.group(1).lower())
        if not start_month:
            continue
        start = month_index(int(match.group(2)), start_month)
        if match.group(5):
            return start, as_of, True
        end_month = MONTHS.get(match.group(3).lower())
        if not end_month:
            continue
        return start, month_index(int(match.group(4)), end_month), False
    match = YEAR_RANGE.search(text)
    if match:
        start = month_index(int(match.group(1)), 1)
        if match.group(2).isdigit():
            return start, month_index(int(match.group(2)), 12), False
        return start, as_of, True
    return None


def assign_dates(roles: list, as_of: int) -> None:
    for role in roles:
        found = find_date_range(clean_md(" ".join(role.header)), as_of)
        if found:
            role.start, role.end, role.present = found
        if not role.company:
            for separator in (" at ", " @ "):
                if separator in role.title:
                    role.company = role.title.split(separator, 1)[1].strip()
                    break


def merge_intervals(intervals: list) -> list:
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def has_metric(text: str) -> bool:
    cleaned = YEAR_TOKEN.sub(" ", VERSION_TOKEN.sub(" ", clean_md(text)))
    return bool(re.search(r"\d", cleaned) or METRIC_WORDS.search(cleaned))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validate an ideal-candidate resume against JD keywords and hard constraints.")
    p.add_argument("resume", help="Markdown file with <!-- RESUME:START/END --> markers")
    p.add_argument("--keywords", help="Keyword file (see references/evidence-report.md#keyword-file-format)")
    p.add_argument("--as-of", help="YYYY-MM used for 'Present' (default: current month)")
    p.add_argument("--min-years", type=float, help="Minimum total years of experience")
    p.add_argument("--max-years", type=float, help="Maximum total years of experience")
    p.add_argument("--earliest-start", help="YYYY-MM; no role may start before this")
    p.add_argument("--latest-end", help="YYYY-MM or 'present'; no role may end after this")
    p.add_argument("--require-company", action="append", default=[], metavar="NAME",
                   help="Employer that must appear in a role header (repeatable)")
    p.add_argument("--exclude-company", action="append", default=[], metavar="NAME",
                   help="Name that must not appear anywhere in the resume block (repeatable)")
    p.add_argument("--max-roles", type=int, help="Maximum number of roles")
    p.add_argument("--max-gap-months", type=int, help="Maximum gap between roles, in months")
    p.add_argument("--max-bullets-per-role", type=int, help="Maximum bullets in any role")
    p.add_argument("--min-metric-ratio", type=float, default=0.7,
                   help="Share of experience bullets that must contain a metric, 0-1 (default 0.7; 0 disables)")
    p.add_argument("--max-pages", type=float, help="Warn when the estimated page count is higher")
    p.add_argument("--strict", action="store_true",
                   help="Fail required keywords that are only MENTIONED and preferred keywords that are MISSING")
    return p


def check_keywords(keywords: list, sections: dict, strict: bool):
    texts = {k: clean_md("\n".join(v)) for k, v in sections.items()}
    rows = []
    for kw in keywords:
        counts = {k: sum(len(p.findall(texts[k])) for p in kw.patterns) for k in texts}
        if counts["experience"]:
            status = "DEMONSTRATED"
        elif counts["credentials"]:
            status = "CREDENTIAL"
        elif counts["header"] + counts["summary"] + counts["other"]:
            status = "MENTIONED"
        elif counts["skills"]:
            status = "LISTED"
        else:
            status = "MISSING"
        if status in ("DEMONSTRATED", "CREDENTIAL"):
            verdict = "PASS"
        elif kw.priority == "R":
            verdict = "FAIL" if status in ("LISTED", "MISSING") or strict else "WARN"
        else:
            verdict = "FAIL" if strict and status == "MISSING" else "WARN"
        where = " ".join(f"{SECTION_ABBR[k]}:{n}" for k, n in counts.items() if n) or "-"
        rows.append((verdict, kw, status, where))
    return rows


def check_timeline(args, roles: list, as_of: int, earliest, latest, checks: Checks) -> float:
    if not roles:
        checks.add("FAIL", "No roles found: use '### Title' under a PROFESSIONAL EXPERIENCE heading")
        return 0.0
    dated = [r for r in roles if r.dated]
    for n, role in enumerate(roles, start=1):
        name = f"Role {n} ({role.title})"
        if not role.dated:
            checks.add("FAIL", f"{name}: no date range like 'Mon YYYY - Mon YYYY' or 'Mon YYYY - Present'")
        elif role.start > role.end:
            checks.add("FAIL", f"{name}: starts {fmt(role.start)} after it ends {fmt(role.end)}")
        elif role.end > as_of:
            checks.add("FAIL", f"{name}: ends {fmt(role.end)}, after --as-of {fmt(as_of)}")
        if not role.bullets:
            checks.add("WARN", f"{name}: has no bullets")

    if earliest is not None:
        bad = [(n, r) for n, r in enumerate(roles, 1) if r.dated and r.start < earliest]
        for n, r in bad:
            checks.add("FAIL", f"Role {n} starts {fmt(r.start)}, before earliest allowed {fmt(earliest)}")
        if not bad:
            checks.add("PASS", f"All roles start on or after {fmt(earliest)}")
    if latest is not None:
        bad = [(n, r) for n, r in enumerate(roles, 1) if r.dated and r.end > latest]
        for n, r in bad:
            end_label = "Present" if r.present else fmt(r.end)
            checks.add("FAIL", f"Role {n} ends {end_label}, after latest allowed {fmt(latest)}")
        if not bad:
            checks.add("PASS", f"All roles end on or before {fmt(latest)}")

    if args.max_roles is not None:
        status = "PASS" if len(roles) <= args.max_roles else "FAIL"
        checks.add(status, f"{len(roles)} roles (max {args.max_roles})")
    if args.max_bullets_per_role is not None:
        bad = [(n, r) for n, r in enumerate(roles, 1) if len(r.bullets) > args.max_bullets_per_role]
        for n, r in bad:
            checks.add("FAIL", f"Role {n} has {len(r.bullets)} bullets (max {args.max_bullets_per_role})")
        if not bad:
            checks.add("PASS", f"Every role has at most {args.max_bullets_per_role} bullets")

    starts = [r.start for r in dated]
    if any(starts[k] < starts[k + 1] for k in range(len(starts) - 1)):
        checks.add("WARN", "Roles are not listed in reverse-chronological order")

    intervals = merge_intervals([(r.start, r.end) for r in dated if r.start <= r.end])
    months = sum(end - start + 1 for start, end in intervals)
    years = round(months / 12, 1)
    if args.min_years is not None:
        status = "PASS" if years >= args.min_years else "FAIL"
        checks.add(status, f"Total experience {years} yrs (min {args.min_years:g})")
    if args.max_years is not None:
        status = "PASS" if years <= args.max_years else "FAIL"
        checks.add(status, f"Total experience {years} yrs (max {args.max_years:g})")
    if args.max_gap_months is not None and intervals:
        bad = []
        for k in range(len(intervals) - 1):
            gap = intervals[k + 1][0] - intervals[k][1] - 1
            if gap > args.max_gap_months:
                bad.append((intervals[k][1], intervals[k + 1][0], gap))
        for end, start, gap in bad:
            checks.add("FAIL", f"Gap of {gap} months between {fmt(end)} and {fmt(start)} "
                               f"(max {args.max_gap_months})")
        if not bad:
            checks.add("PASS", f"No gap longer than {args.max_gap_months} months between roles")
        if latest is None:
            trailing = as_of - intervals[-1][1]
            if trailing > args.max_gap_months:
                checks.add("WARN", f"Latest role ended {fmt(intervals[-1][1])}, {trailing} months before "
                                   f"{fmt(as_of)}: the candidate looks unemployed")
    return years


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)

    path = Path(args.resume)
    if not path.is_file():
        print(f"ERROR: resume file not found: {path}")
        return 2
    try:
        today = date.today()
        as_of = parse_ym(args.as_of) if args.as_of else month_index(today.year, today.month)
        earliest = parse_ym(args.earliest_start) if args.earliest_start else None
        latest = None
        if args.latest_end and args.latest_end.strip().lower() not in PRESENT_WORDS:
            latest = parse_ym(args.latest_end)
        keywords = load_keywords(Path(args.keywords)) if args.keywords else []
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 2

    block, has_markers = extract_resume_block(path.read_text(encoding="utf-8-sig"))
    sections, roles = parse_resume(block)
    assign_dates(roles, as_of)
    checks = Checks()

    print("Ideal-candidate resume validation")
    print(f"  File:     {path}")
    print(f"  As of:    {fmt(as_of)}")
    if not has_markers:
        checks.add("WARN", "RESUME:START/END markers not found: validated the whole file "
                           "(evidence text can inflate coverage)")

    keyword_rows = []
    if keywords:
        keyword_rows = check_keywords(keywords, sections, args.strict)
        required = sum(1 for k in keywords if k.priority == "R")
        print(f"  Keywords: {args.keywords} ({required} required, {len(keywords) - required} preferred)")
        print()
        print("[1] KEYWORD COVERAGE (resume block only)")
        width = min(max(len(row[1].terms[0]) for row in keyword_rows), 40)
        print(f"  {'RESULT':<6} PRI {'KEYWORD':<{width}}  {'STATUS':<12}  WHERE")
        for verdict, kw, status, where in keyword_rows:
            label = kw.terms[0] if len(kw.terms[0]) <= width else kw.terms[0][:width - 3] + "..."
            print(f"  {verdict:<6} {kw.priority:<3} {label:<{width}}  {status:<12}  {where}")
    else:
        print("  Keywords: (none given; keyword coverage skipped)")

    print()
    print("[2] EXPERIENCE TIMELINE")
    for n, role in enumerate(roles, start=1):
        if role.dated:
            span = f"{fmt(role.start)} -> {'Present' if role.present else fmt(role.end)}"
            span += f" ({role.end - role.start + 1} mo)"
        else:
            span = "dates not found"
        print(f"  {n}. {role.title} | {role.company or '(company not found)'} | {span} | "
              f"{len(role.bullets)} bullets")
    years = check_timeline(args, roles, as_of, earliest, latest, checks)
    print(f"  Total experience (overlaps merged): {years} years")

    full_text = clean_md(block)
    for company in args.require_company:
        pattern = term_pattern(company)
        hits = [str(n) for n, r in enumerate(roles, 1) if pattern.search(clean_md(" ".join(r.header)))]
        if hits:
            checks.add("PASS", f"Required company '{company}' is an employer (role {', '.join(hits)})")
        elif pattern.search(full_text):
            checks.add("FAIL", f"Required company '{company}' appears, but not as an employer in a role header")
        else:
            checks.add("FAIL", f"Required company '{company}' not found")
    for company in args.exclude_company:
        hits = len(term_pattern(company).findall(full_text))
        if hits:
            checks.add("FAIL", f"Excluded name '{company}' appears {hits} time(s) in the resume block")
        else:
            checks.add("PASS", f"Excluded name '{company}' does not appear")

    bullets = [b for r in roles for b in r.bullets]
    if bullets and args.min_metric_ratio > 0:
        with_metric = sum(1 for b in bullets if has_metric(b))
        ratio = with_metric / len(bullets)
        status = "PASS" if ratio >= args.min_metric_ratio else "FAIL"
        checks.add(status, f"{with_metric}/{len(bullets)} experience bullets ({ratio:.0%}) contain a metric "
                           f"(min {args.min_metric_ratio:.0%})")

    placeholders = PLACEHOLDER.findall(block)
    if placeholders:
        examples = ", ".join(placeholders[:3])
        checks.add("FAIL", "%d unfilled template placeholder(s), e.g. %s" % (len(placeholders), examples))
    else:
        checks.add("PASS", "No unfilled template placeholders")

    if args.max_pages:
        words = len(re.findall(r"\b\w+\b", full_text))
        pages = words / 650
        status = "PASS" if pages <= args.max_pages else "WARN"
        checks.add(status, f"About {words} words (~{pages:.1f} pages at ~650 words/page; max {args.max_pages:g})")

    print()
    print("[3] CONSTRAINT AND QUALITY CHECKS")
    for status, message in checks.rows:
        print(f"  {status:<5} {message}")

    keyword_fail = sum(1 for row in keyword_rows if row[0] == "FAIL")
    keyword_warn = sum(1 for row in keyword_rows if row[0] == "WARN")
    failures = keyword_fail + checks.count("FAIL")
    warnings = keyword_warn + checks.count("WARN")

    print()
    print("SUMMARY")
    for priority, label in (("R", "Required"), ("P", "Preferred")):
        subset = [row for row in keyword_rows if row[1].priority == priority]
        if not subset:
            continue
        tally = {s: sum(1 for row in subset if row[2] == s)
                 for s in ("DEMONSTRATED", "CREDENTIAL", "MENTIONED", "LISTED", "MISSING")}
        print(f"  {label} keywords ({len(subset)}): " + ", ".join(f"{n} {s.lower()}" for s, n in tally.items()))
    print(f"  Checks: {len(checks.rows) - checks.count('FAIL') - checks.count('WARN')} passed, "
          f"{checks.count('WARN')} warnings, {checks.count('FAIL')} failed")
    print(f"RESULT: {'FAIL' if failures else 'PASS'} ({failures} failure(s), {warnings} warning(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
