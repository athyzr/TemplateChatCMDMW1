"""
parser.py
Turns the pasted schedule table (markdown / HTML / spreadsheet paste)
into a list of ParsedSession objects. Nothing here talks to Streamlit -
it's plain, testable Python.
"""

import re
import csv
import io
from dataclasses import dataclass, field
from typing import List, Optional

from utils import (
    is_url,
    normalize_day,
    extract_day_mentions,
    parse_date_str,
    parse_time_str,
    is_empty_marker,
)

EXPECTED_COLUMNS = 5
HEADER_HINTS = ("mentor", "session", "materi", "pelengkap", "pretest")


@dataclass
class ParsedSession:
    row_number: int
    mentor_name: Optional[str]
    mentor_status: str  # "confirmed" | "hold" | "none"
    day: str
    date_str: str
    time_str: Optional[str]
    materi: str

    pg_link: Optional[str] = None
    ag_link: Optional[str] = None
    cm_link: Optional[str] = None
    student_link: Optional[str] = None

    pretest_cm: Optional[str] = None
    pretest_student: Optional[str] = None
    pretest_single: Optional[str] = None

    extra_resources: List[str] = field(default_factory=list)

    # internal, used only to propagate a shared AG link across rows
    _ag_applies_to: List[str] = field(default_factory=list)

    # sort keys (may be None if unparseable - session still shown, just sorts last)
    sort_date = None
    sort_time = None


class TableFormatError(Exception):
    pass


# ---------------------------------------------------------------------------
# Step 1: turn raw pasted text into rows of 5 raw cell strings
# ---------------------------------------------------------------------------

def _split_br(text: str) -> str:
    """Replace <br>, <br/>, <br /> with real newlines."""
    return re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)


def _looks_like_markdown_table(text: str) -> bool:
    for line in text.strip().splitlines():
        if line.strip().startswith("|"):
            return True
    return False


def _looks_like_html_table(text: str) -> bool:
    return "<table" in text.lower()


def _is_markdown_separator_row(cells) -> bool:
    # a row like | --- | :--- | ---: |
    return all(re.match(r"^:?-+:?$", c.strip()) for c in cells if c.strip() != "")


def _extract_rows_markdown(text: str):
    rows = []
    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        line = _split_br(line)
        # strip leading/trailing pipe, split on single pipes
        inner = line.strip()
        if inner.startswith("|"):
            inner = inner[1:]
        if inner.endswith("|"):
            inner = inner[:-1]
        cells = [c.strip() for c in inner.split("|")]
        if _is_markdown_separator_row(cells):
            continue
        rows.append(cells)
    return rows


def _extract_rows_html(text: str):
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise TableFormatError(
            "Paket 'beautifulsoup4' belum terinstall. Jalankan: pip install beautifulsoup4"
        ) from e

    soup = BeautifulSoup(text, "html.parser")
    table = soup.find("table")
    if table is None:
        raise TableFormatError("Tag <table> ditemukan tapi tidak bisa diparse.")
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        row = [c.get_text(separator="\n").strip() for c in cells]
        rows.append(row)
    return rows


def _extract_rows_delimited(text: str):
    """Handles TSV paste from Google Sheets / Excel. Falls back to
    splitting on runs of 2+ spaces if there are no tab characters at all
    (some clipboards / terminals collapse tabs to spaces)."""
    stripped = text.strip("\n")
    if "\t" in stripped:
        reader = csv.reader(io.StringIO(stripped), delimiter="\t")
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    else:
        rows = []
        for line in stripped.splitlines():
            if not line.strip():
                continue
            cells = re.split(r"\s{2,}", line.strip())
            rows.append(cells)
    return rows


def extract_rows(raw_text: str):
    """
    Returns a list of rows, each a list of raw cell strings (padded/
    truncated to EXPECTED_COLUMNS). Raises TableFormatError if nothing
    usable is found.
    """
    if not raw_text or not raw_text.strip():
        raise TableFormatError("Input kosong.")

    if _looks_like_html_table(raw_text):
        rows = _extract_rows_html(raw_text)
    elif _looks_like_markdown_table(raw_text):
        rows = _extract_rows_markdown(raw_text)
    else:
        rows = _extract_rows_delimited(raw_text)

    if not rows:
        raise TableFormatError("Tidak ada baris yang bisa dibaca dari tabel.")

    # if not a single row shows real column structure (>1 cell), this
    # almost certainly isn't the schedule table - fail with a clear message
    # instead of quietly producing garbage output
    if not any(len(row) > 1 for row in rows):
        raise TableFormatError(
            "Format tabel belum dapat dibaca. Pastikan tabel memiliki 5 kolom: "
            "Mentor, Session, Materi, Pelengkap Kelas, dan Link Pretest."
        )

    # drop a header row if it mentions the expected column names
    first_row_text = " ".join(rows[0]).lower()
    if sum(1 for h in HEADER_HINTS if h in first_row_text) >= 2:
        rows = rows[1:]

    if not rows:
        raise TableFormatError("Tabel hanya berisi header, tidak ada data.")

    # normalize column count: pad short rows, keep first 5 of long rows
    normalized = []
    for row in rows:
        cells = list(row)
        if len(cells) < EXPECTED_COLUMNS:
            cells = cells + [""] * (EXPECTED_COLUMNS - len(cells))
        elif len(cells) > EXPECTED_COLUMNS:
            cells = cells[:EXPECTED_COLUMNS]
        normalized.append(cells)

    return normalized


# ---------------------------------------------------------------------------
# Step 2: parse each column
# ---------------------------------------------------------------------------

def parse_mentor(raw: str):
    text = raw.strip()
    if is_empty_marker(text):
        return None, "none"
    m = re.match(r"^(.*?)\s*[-–]\s*hold\s*$", text, flags=re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        return (name if name else None), "hold"
    return text, "confirmed"


def parse_session_cell(raw: str):
    lines = [l.strip() for l in _split_br(raw).splitlines() if l.strip() != ""]
    day = lines[0] if len(lines) > 0 else ""
    date_str = lines[1] if len(lines) > 1 else ""
    time_str = lines[2] if len(lines) > 2 else None
    if time_str is not None:
        t = time_str.strip()
        if t in ("-", "- WIB", "-WIB") or is_empty_marker(t.replace("WIB", "").strip()):
            time_str = None
    return day, date_str, time_str


LINE_PG = re.compile(r"^PG\s*[:\-]?\s*(.+)$", re.IGNORECASE)
LINE_AG_ANNOTATION = re.compile(r"^AG\s+untuk\s+(.+)$", re.IGNORECASE)
LINE_AG = re.compile(r"^AG\s*[:\-]?\s*(.+)$", re.IGNORECASE)
LINE_CM = re.compile(r"^untuk\s+cm\s*[:\-]\s*(.+)$", re.IGNORECASE)
LINE_STUDENT = re.compile(r"^untuk\s+student\s*[:\-]\s*(.+)$", re.IGNORECASE)


def parse_pelengkap(raw: str):
    """
    Returns (pg, ag, cm_link, student_link, ag_applies_to, extra_resources)
    Nothing recognized is ever dropped - it goes into extra_resources.
    """
    pg = ag = cm_link = student_link = None
    ag_applies_to = []
    extra = []

    lines = [l.strip() for l in _split_br(raw).splitlines() if l.strip() != ""]
    for line in lines:
        if is_empty_marker(line):
            continue

        m = LINE_AG_ANNOTATION.match(line)
        if m:
            ag_applies_to.extend(extract_day_mentions(m.group(1)))
            continue

        m = LINE_PG.match(line)
        if m and is_url(m.group(1).strip()):
            pg = m.group(1).strip()
            continue

        m = LINE_AG.match(line)
        if m and is_url(m.group(1).strip()):
            ag = m.group(1).strip()
            continue

        m = LINE_CM.match(line)
        if m:
            cm_link = m.group(1).strip()
            continue

        m = LINE_STUDENT.match(line)
        if m:
            student_link = m.group(1).strip()
            continue

        # unrecognized - keep it, never invent, never discard
        extra.append(line)

    return pg, ag, cm_link, student_link, ag_applies_to, extra


def parse_pretest(raw: str):
    """Returns (pretest_cm, pretest_student, pretest_single)."""
    text = raw.strip()
    if is_empty_marker(text):
        return None, None, None

    lines = [l.strip() for l in _split_br(text).splitlines() if l.strip() != ""]
    cm = student = None
    found_split = False
    for line in lines:
        m = LINE_CM.match(line)
        if m:
            cm = m.group(1).strip()
            found_split = True
            continue
        m = LINE_STUDENT.match(line)
        if m:
            student = m.group(1).strip()
            found_split = True
            continue

    if found_split:
        return cm, student, None

    # no CM/Student split - treat as one link used in context
    return None, None, " / ".join(lines)


# ---------------------------------------------------------------------------
# Step 3: assemble + AG propagation + sorting
# ---------------------------------------------------------------------------

def parse_row(row_number: int, cells) -> ParsedSession:
    mentor_raw, session_raw, materi_raw, pelengkap_raw, pretest_raw = cells

    mentor_name, mentor_status = parse_mentor(mentor_raw)
    day, date_str, time_str = parse_session_cell(session_raw)
    materi = materi_raw.strip()
    pg, ag, cm_link, student_link, ag_applies_to, extra = parse_pelengkap(pelengkap_raw)
    pretest_cm, pretest_student, pretest_single = parse_pretest(pretest_raw)

    session = ParsedSession(
        row_number=row_number,
        mentor_name=mentor_name,
        mentor_status=mentor_status,
        day=day,
        date_str=date_str,
        time_str=time_str,
        materi=materi,
        pg_link=pg,
        ag_link=ag,
        cm_link=cm_link,
        student_link=student_link,
        pretest_cm=pretest_cm,
        pretest_student=pretest_student,
        pretest_single=pretest_single,
        extra_resources=extra,
    )
    session._ag_applies_to = ag_applies_to
    session.sort_date = parse_date_str(date_str)
    session.sort_time = parse_time_str(time_str)
    return session


def _propagate_ag(sessions: List[ParsedSession]):
    """A cell can say 'AG untuk Day 35, Day 36, Day 37' alongside its own
    AG link; that link then applies to those other days too, without the
    user repeating it."""
    by_day = {}
    for s in sessions:
        by_day.setdefault(normalize_day(s.day), []).append(s)

    for s in sessions:
        if not s._ag_applies_to or not s.ag_link:
            continue
        for target_day in s._ag_applies_to:
            for target in by_day.get(target_day, []):
                if target is not s and not target.ag_link:
                    target.ag_link = s.ag_link


def parse_input(raw_text: str):
    """
    Main entry point. Returns (sessions, warnings).
    Raises TableFormatError if the input can't be read at all.
    Per-row problems are collected as warnings, not fatal.
    """
    rows = extract_rows(raw_text)

    sessions = []
    warnings = []
    for i, row in enumerate(rows, start=1):
        try:
            sessions.append(parse_row(i, row))
        except Exception:
            warnings.append(f"⚠️ Row {i} memiliki data yang tidak dapat dikenali.")

    _propagate_ag(sessions)
    return sessions, warnings


def sort_key(session: ParsedSession):
    """Sessions without a parseable date sort last, not crash."""
    import datetime as _dt
    date_part = session.sort_date or _dt.date.max
    time_part = session.sort_time or _dt.time.min
    return (date_part, time_part, session.row_number)


def group_by_mentor(sessions: List[ParsedSession]):
    """
    Groups sessions by mentor name (sessions with mentor 'Tidak Ada' are
    excluded from mentor broadcasts entirely, per spec). Returns
    (ordered_list_of_mentor_names, {mentor_name: (status, [sessions])}).
    Status is 'hold' if ANY session for that mentor is on hold.
    """
    order = []
    groups = {}
    for s in sessions:
        if not s.mentor_name:
            continue
        if s.mentor_name not in groups:
            groups[s.mentor_name] = ["confirmed", []]
            order.append(s.mentor_name)
        groups[s.mentor_name][1].append(s)
        if s.mentor_status == "hold":
            groups[s.mentor_name][0] = "hold"

    # sort each mentor's own sessions chronologically
    for name in order:
        groups[name][1].sort(key=sort_key)

    return order, groups