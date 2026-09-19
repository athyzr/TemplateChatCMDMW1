"""
utils.py
Helper functions shared by parser.py and templates.py.
No external state, no I/O side effects.
"""

import re
import datetime


URL_RE = re.compile(r"^(https?://|www\.)\S+$", re.IGNORECASE)


def is_url(text: str) -> bool:
    """True if the string looks like a URL."""
    if not text:
        return False
    return bool(URL_RE.match(text.strip()))


def normalize_day(raw: str) -> str:
    """
    Normalize a day label so different spellings match each other.
    "Day-35", "Day 35", "day35" -> "Day-35"
    "Day-VL", "Day VL"          -> "Day-VL"
    """
    if raw is None:
        return ""
    s = raw.strip()
    s = re.sub(r"^day[\s\-]*", "", s, flags=re.IGNORECASE)
    s = s.strip()
    return f"Day-{s}"


DAY_MENTION_RE = re.compile(r"day[\s\-]*([A-Za-z0-9]+)", re.IGNORECASE)


def extract_day_mentions(text: str):
    """
    From a string like "AG untuk Day 35, Day 36, Day 37" or
    "berlaku untuk Day-35, Day-36" return normalized day labels
    ["Day-35", "Day-36", "Day-37"].
    """
    return [f"Day-{m}" for m in DAY_MENTION_RE.findall(text)]


_MONTHS_ID_TO_EN = {
    "januari": "January", "februari": "February", "maret": "March",
    "april": "April", "mei": "May", "juni": "June", "juli": "July",
    "agustus": "August", "september": "September", "oktober": "October",
    "november": "November", "desember": "December",
}

_WEEKDAYS_ID_TO_EN = {
    "senin": "Monday", "selasa": "Tuesday", "rabu": "Wednesday",
    "kamis": "Thursday", "jumat": "Friday", "sabtu": "Saturday",
    "minggu": "Sunday",
}


def _translate_indonesian_month(date_str: str) -> str:
    """Best-effort: translate an Indonesian month name to English so
    datetime.strptime (which uses the C/English locale) can parse it."""
    out = date_str
    for id_name, en_name in _MONTHS_ID_TO_EN.items():
        out = re.sub(id_name, en_name, out, flags=re.IGNORECASE)
    return out


def _translate_indonesian_date(date_str: str) -> str:
    out = date_str
    for id_name, en_name in _WEEKDAYS_ID_TO_EN.items():
        out = re.sub(rf"^{id_name}(?=,?\s)", en_name, out, flags=re.IGNORECASE)
    return _translate_indonesian_month(out)


def parse_date_str(date_str: str):
    """
    Parse "Monday, 21 September 2026" (or the Indonesian-month variant,
    or without a weekday) into a datetime.date. Returns None if it can't
    be parsed - callers should treat that gracefully, never crash.
    """
    if not date_str:
        return None
    candidate = _translate_indonesian_date(date_str.strip())
    formats = ["%A, %d %B %Y", "%d %B %Y", "%A %d %B %Y"]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    return None


TIME_RE = re.compile(r"(\d{1,2})[.:](\d{2})")


def parse_time_str(time_str: str):
    """
    Parse the *start* time out of "19.00 - 21.30 WIB" into a
    datetime.time. Returns None if no time is present/parseable.
    """
    if not time_str:
        return None
    m = TIME_RE.search(time_str)
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2))
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return datetime.time(hour, minute)
    return None


def is_empty_marker(text: str) -> bool:
    """True for cells that mean 'no value': 'Tidak Ada', '-', '', etc."""
    if text is None:
        return True
    t = text.strip().lower()
    return t in ("", "-", "tidak ada", "tidak ada.", "n/a", "none")