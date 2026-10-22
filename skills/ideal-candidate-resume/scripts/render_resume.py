#!/usr/bin/env python3
"""Render an ideal-candidate resume (Markdown) to DOCX and/or PDF.

By default only the resume block (between <!-- RESUME:START --> and <!-- RESUME:END -->)
is rendered, so the output is ready to share. --include-evidence appends the profile,
constraints, and evidence report after a page break.

Layout: single column, ATS-safe, Letter size. The name is centered; the header lines
below it are centered; section headings have a bottom rule; each role shows the title
with right-aligned dates, then the employer line in italics; bullets use Word list styles.

Requires: pip install python-docx
PDF:      pip install docx2pdf   (uses Microsoft Word)   or LibreOffice (soffice)

Examples:
  python render_resume.py Ideal_Candidate_Resume_Citi_FSE.md --formats docx
  python render_resume.py Ideal_Candidate_Resume_Citi_FSE.md --formats docx,pdf --include-evidence
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt
except ImportError:  # pragma: no cover
    sys.exit("python-docx is required: pip install python-docx")

RESUME_START = "<!-- RESUME:START -->"
RESUME_END = "<!-- RESUME:END -->"
EVIDENCE_START = "<!-- EVIDENCE:START -->"
EVIDENCE_END = "<!-- EVIDENCE:END -->"

HYPERLINK_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
LINK_COLOR = "0563C1"
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0
SIDE_MARGIN_IN = 0.6
TOP_MARGIN_IN = 0.5
RIGHT_TAB = Inches(PAGE_WIDTH_IN - 2 * SIDE_MARGIN_IN)

INLINE = re.compile(
    r"(\*\*.+?\*\*|__.+?__|\[[^\]]+\]\([^)\s]+\)|`[^`]+`|\*[^*\s][^*]*?\*"
    r"|(?<![A-Za-z0-9])_[^_\s][^_]*?_(?![A-Za-z0-9]))"
)
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET = re.compile(r"^(\s*)[-*+]\s+(.*)$")
NUMBERED = re.compile(r"^\s*\d+[.)]\s+(.*)$")
HRULE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")
# "**Employer** (descriptor) - City, ST | *Mon YYYY - Present*"
ENTRY = re.compile(r"^\*\*(.+?)\*\*(.*?)\|\s*\*([^*]+)\*\s*$")
DATE_HINT = re.compile(r"\d{4}|present|current", re.IGNORECASE)
# Elements that may follow w:pBdr inside w:pPr (OOXML schema order).
PPR_AFTER_PBDR = (
    "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct",
    "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi", "w:adjustRightInd",
    "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents",
    "w:suppressOverlap", "w:jc", "w:textDirection", "w:textAlignment", "w:textboxTightWrap",
    "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
)


# ---------------------------------------------------------------- markdown helpers

def strip_md(text: str) -> str:
    text = LINK.sub(r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"(?<![A-Za-z0-9])\*(?=\S)|(?<=\S)\*(?![A-Za-z0-9])", "", text)
    return unescape(text).strip()


def unescape(text: str) -> str:
    return re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>])", r"\1", text)


def split_blocks(text: str):
    """Return (resume, appendix, has_markers)."""
    start, end = text.find(RESUME_START), text.find(RESUME_END)
    if start == -1 or end == -1 or end < start:
        return text, "", False
    resume = text[start + len(RESUME_START):end]
    preamble = text[:start]
    ev_start, ev_end = text.find(EVIDENCE_START), text.find(EVIDENCE_END)
    if ev_start != -1 and ev_end > ev_start:
        evidence = text[ev_start + len(EVIDENCE_START):ev_end]
    else:
        evidence = text[end + len(RESUME_END):]
    return resume, preamble.rstrip() + "\n\n" + evidence.strip() + "\n", True


def split_row(line: str) -> list:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def is_separator(cells: list) -> bool:
    filled = [c.replace(" ", "") for c in cells if c.strip()]
    return bool(filled) and all(re.fullmatch(r":?-{2,}:?", c) for c in filled)


# ---------------------------------------------------------------- docx helpers

def set_base_style(doc, font: str, size: float) -> None:
    style = doc.styles["Normal"]
    style.font.name = font
    style.font.size = Pt(size)
    r_fonts = style.element.get_or_add_rPr().find(qn("w:rFonts"))
    if r_fonts is not None:
        r_fonts.set(qn("w:eastAsia"), font)
    fmt = style.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    fmt.line_spacing = 1.0


def set_page(doc) -> None:
    for section in doc.sections:
        section.page_width = Inches(PAGE_WIDTH_IN)
        section.page_height = Inches(PAGE_HEIGHT_IN)
        section.top_margin = section.bottom_margin = Inches(TOP_MARGIN_IN)
        section.left_margin = section.right_margin = Inches(SIDE_MARGIN_IN)


def add_bottom_border(paragraph) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    p_bdr.append(bottom)
    p_pr.insert_element_before(p_bdr, *PPR_AFTER_PBDR)


def add_run(paragraph, text: str, bold=False, italic=False, size=None):
    run = paragraph.add_run(text)
    if bold:
        run.bold = True
    if italic:
        run.italic = True
    if size:
        run.font.size = Pt(size)
    return run


def add_hyperlink(paragraph, text: str, url: str, bold=False, italic=False, size=None) -> None:
    r_id = paragraph.part.relate_to(url, HYPERLINK_REL, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    if bold:
        r_pr.append(OxmlElement("w:b"))
    if italic:
        r_pr.append(OxmlElement("w:i"))
    color = OxmlElement("w:color")
    color.set(qn("w:val"), LINK_COLOR)
    r_pr.append(color)
    if size:
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(int(round(size * 2))))
        r_pr.append(sz)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)
    run.append(r_pr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    run.append(t)
    link.append(run)
    paragraph._p.append(link)


def add_inline(paragraph, text: str, bold=False, italic=False, size=None) -> None:
    """Render **bold**, *italic*, `code`, and [links](url) into runs."""
    for piece in INLINE.split(text):
        if not piece:
            continue
        if not INLINE.fullmatch(piece):
            add_run(paragraph, unescape(piece), bold, italic, size)
        elif piece.startswith(("**", "__")):
            add_inline(paragraph, piece[2:-2], True, italic, size)
        elif piece.startswith("["):
            label, url = LINK.fullmatch(piece).groups()
            if re.match(r"^(https?://|mailto:)", url, re.IGNORECASE):
                add_hyperlink(paragraph, unescape(label), url, bold, italic, size)
            else:
                add_run(paragraph, unescape(label), bold, italic, size)
        elif piece.startswith("`"):
            add_run(paragraph, piece[1:-1], bold, italic, size)
        else:
            add_inline(paragraph, piece[1:-1], bold, True, size)


def tight(paragraph, before=0.0, after=1.0):
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    return paragraph


def add_name(doc, text: str) -> None:
    p = tight(doc.add_paragraph(), after=2)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(p, strip_md(text), bold=True, size=18)


def section_heading(doc, text: str) -> None:
    p = tight(doc.add_paragraph(), before=8, after=2)
    p.paragraph_format.keep_with_next = True
    add_run(p, strip_md(text).upper(), bold=True, size=11)
    add_bottom_border(p)


def entry_line(doc, left_md: str, right: str) -> None:
    """Bold title on the left, dates right-aligned on the same line."""
    p = tight(doc.add_paragraph(), before=6, after=1)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.tab_stops.add_tab_stop(RIGHT_TAB, WD_TAB_ALIGNMENT.RIGHT)
    add_inline(p, left_md)
    if right:
        add_run(p, "\t" + strip_md(right), bold=True)


def employer_line(doc, employer: str, rest: str) -> None:
    p = tight(doc.add_paragraph(), after=1)
    p.paragraph_format.keep_with_next = True
    add_run(p, strip_md(employer), bold=True, italic=True)
    rest = rest.strip()
    if rest:
        add_inline(p, " " + rest, italic=True)


def split_title_dates(content: str):
    if " | " in content:
        left, right = content.rsplit(" | ", 1)
        if DATE_HINT.search(right):
            return strip_md(left), strip_md(right)
    return strip_md(content), ""


def render_table(doc, rows: list, has_header: bool, mode: str, font_size: float) -> None:
    if not rows:
        return
    if mode == "resume":
        # Tables are not ATS-safe: flatten to "Label: values" lines.
        for cells in rows[1:] if has_header else rows:
            cells = [c for c in cells if c]
            if not cells:
                continue
            p = tight(doc.add_paragraph())
            if len(cells) == 1:
                add_inline(p, cells[0])
            else:
                add_inline(p, "**" + strip_md(cells[0]).rstrip(":") + ":** " + " | ".join(cells[1:]))
        return
    columns = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=columns)
    try:
        table.style = "Table Grid"
    except (KeyError, ValueError):
        pass
    for r_index, cells in enumerate(rows):
        for c_index in range(columns):
            text = cells[c_index] if c_index < len(cells) else ""
            add_inline(table.cell(r_index, c_index).paragraphs[0], text,
                       bold=has_header and r_index == 0, size=max(font_size - 1.5, 7))
    tight(doc.add_paragraph(), after=2)


def render_block(doc, text: str, mode: str, font_size: float) -> None:
    """mode='resume' uses resume layout; mode='appendix' uses Word headings and real tables."""
    lines = text.splitlines()
    in_header = mode == "resume"
    in_comment = False
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if in_comment:
            in_comment = "-->" not in line
            i += 1
            continue
        if line.startswith("<!--"):
            in_comment = "-->" not in line
            i += 1
            continue
        if not line or HRULE.fullmatch(line):
            i += 1
            continue

        if line.startswith("|"):
            raw_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                raw_rows.append(split_row(lines[i]))
                i += 1
            has_header = len(raw_rows) > 1 and is_separator(raw_rows[1])
            rows = [r for r in raw_rows if not is_separator(r)]
            render_table(doc, rows, has_header, mode, font_size)
            continue

        heading = HEADING.match(line)
        if heading:
            level, content = len(heading.group(1)), heading.group(2).strip()
            if mode != "resume":
                add_inline(doc.add_heading(level=min(level, 4)), content)
            elif level == 1:
                add_name(doc, content)
            elif level == 2:
                in_header = False
                section_heading(doc, content)
            else:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                entry = ENTRY.match(lines[j].strip()) if j < len(lines) else None
                if entry:
                    entry_line(doc, "**" + strip_md(content) + "**", entry.group(3))
                    employer_line(doc, entry.group(1), entry.group(2))
                    i = j + 1
                    continue
                title, dates = split_title_dates(content)
                entry_line(doc, "**" + title + "**", dates)
            i += 1
            continue

        bullet = BULLET.match(raw)
        if bullet:
            indent = len(bullet.group(1).replace("\t", "    "))
            p = tight(doc.add_paragraph(style="List Bullet 2" if indent >= 2 else "List Bullet"))
            add_inline(p, bullet.group(2).strip())
            i += 1
            continue

        numbered = NUMBERED.match(raw)
        if numbered:
            p = tight(doc.add_paragraph(style="List Number"))
            add_inline(p, numbered.group(1).strip())
            i += 1
            continue

        if line.startswith(">"):
            p = tight(doc.add_paragraph(), after=3)
            add_inline(p, line.lstrip(">").strip(), italic=True)
            i += 1
            continue

        entry = ENTRY.match(line) if mode == "resume" and not in_header else None
        if entry:
            entry_line(doc, "**" + entry.group(1) + "**" + entry.group(2).rstrip(), entry.group(3))
            i += 1
            continue

        p = tight(doc.add_paragraph(), after=1 if mode == "resume" else 3)
        if in_header:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_inline(p, line)
        i += 1


def find_name(resume: str) -> str:
    for line in resume.splitlines():
        match = re.match(r"^#\s+(.*)$", line.strip())
        if match:
            return strip_md(match.group(1))
    return "Candidate"


def build_document(resume: str, appendix: str, include_evidence: bool, font: str, font_size: float):
    doc = Document()
    set_base_style(doc, font, font_size)
    set_page(doc)
    render_block(doc, resume, "resume", font_size)
    if include_evidence and appendix.strip():
        doc.add_page_break()
        render_block(doc, appendix, "appendix", font_size)
    name = find_name(resume)
    props = doc.core_properties
    props.title = f"{name} - Resume"
    props.author = name
    props.subject = "Ideal candidate benchmark resume (fictional)"
    props.comments = "Generated by the ideal-candidate-resume skill"
    return doc


# ---------------------------------------------------------------- pdf conversion

def find_soffice():
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    for candidate in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                      r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                      "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if Path(candidate).exists():
            return candidate
    return None


def docx_to_pdf(docx_path: Path, pdf_path: Path) -> str:
    errors = []
    try:
        from docx2pdf import convert  # Microsoft Word (Windows/macOS)

        convert(str(docx_path), str(pdf_path))
        if pdf_path.exists():
            return "Microsoft Word (docx2pdf)"
        errors.append("docx2pdf: no PDF produced")
    except ImportError:
        errors.append("docx2pdf not installed (pip install docx2pdf; needs Microsoft Word)")
    except Exception as exc:  # Word automation errors vary widely
        errors.append(f"docx2pdf failed: {exc}")

    soffice = find_soffice()
    if soffice:
        try:
            subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir",
                            str(docx_path.parent), str(docx_path)],
                           check=True, capture_output=True, timeout=300)
            produced = docx_path.with_suffix(".pdf")
            if produced.exists() and produced.resolve() != pdf_path.resolve():
                shutil.move(str(produced), str(pdf_path))
            if pdf_path.exists():
                return "LibreOffice"
            errors.append("LibreOffice: no PDF produced")
        except (subprocess.SubprocessError, OSError) as exc:
            errors.append(f"LibreOffice failed: {exc}")
    else:
        errors.append("LibreOffice (soffice) not found")
    raise RuntimeError("PDF conversion failed:\n  - " + "\n  - ".join(errors))


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Render an ideal-candidate resume Markdown file to DOCX/PDF.")
    parser.add_argument("input", help="Markdown file produced by the ideal-candidate-resume skill")
    parser.add_argument("--formats", default="docx", help="Comma list of md, docx, pdf (default: docx)")
    parser.add_argument("--out-dir", help="Output folder (default: the input file's folder)")
    parser.add_argument("--basename", help="Output file name without extension (default: input name)")
    parser.add_argument("--include-evidence", action="store_true",
                        help="Append profile, constraints, and evidence report after a page break")
    parser.add_argument("--font", default="Times New Roman", help="Body font (default: Times New Roman)")
    parser.add_argument("--font-size", type=float, default=10.5, help="Body font size in pt (default: 10.5)")
    args = parser.parse_args(argv)

    formats = {f.strip().lower().lstrip(".") for f in args.formats.split(",") if f.strip()}
    unknown = formats - {"md", "docx", "pdf"}
    if unknown or not formats:
        print(f"ERROR: unsupported format(s): {', '.join(sorted(unknown)) or '(none)'}; use md, docx, pdf")
        return 2
    source = Path(args.input).resolve()
    if not source.is_file():
        print(f"ERROR: input file not found: {source}")
        return 2
    out_dir = Path(args.out_dir).resolve() if args.out_dir else source.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    base = args.basename or source.stem

    text = source.read_text(encoding="utf-8-sig")
    resume, appendix, has_markers = split_blocks(text)
    if not has_markers:
        print("WARNING: RESUME:START/END markers not found; rendering the whole file as the resume.")

    written = []
    if "md" in formats:
        md_path = out_dir / f"{base}.md"
        if md_path.resolve() != source:
            shutil.copyfile(source, md_path)
        written.append((md_path, "source Markdown"))

    if formats & {"docx", "pdf"}:
        doc = build_document(resume, appendix, args.include_evidence, args.font, args.font_size)
        try:
            if "docx" in formats:
                docx_path = out_dir / f"{base}.docx"
                doc.save(str(docx_path))
                written.append((docx_path, "python-docx"))
                if "pdf" in formats:
                    pdf_path = out_dir / f"{base}.pdf"
                    written.append((pdf_path, docx_to_pdf(docx_path, pdf_path)))
            else:
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_docx = Path(tmp) / f"{base}.docx"
                    doc.save(str(tmp_docx))
                    pdf_path = out_dir / f"{base}.pdf"
                    written.append((pdf_path, docx_to_pdf(tmp_docx, pdf_path)))
        except PermissionError as exc:
            print(f"ERROR: cannot write {exc.filename}: close it in Word and retry.")
            return 1
        except RuntimeError as exc:
            for path, how in written:
                print(f"Wrote {path}  [{how}]")
            print(f"ERROR: {exc}")
            print("The DOCX is still usable. Open it in Word and use File > Save As > PDF.")
            return 1

    for path, how in written:
        print(f"Wrote {path}  [{how}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
