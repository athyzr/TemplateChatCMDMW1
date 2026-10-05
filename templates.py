"""
templates.py
Turns ParsedSession objects into WhatsApp-ready broadcast text.
Casual Bahasa Indonesia, single-asterisk emphasis, no invented content -
if the table didn't say it, it doesn't appear here.
"""

import datetime
from typing import List
from parser import ParsedSession, sort_key
from template_manager import get_manager


def _session_block_header(s: ParsedSession) -> str:
    lines = [f"*{s.day} — {s.materi}*"]
    if s.date_str:
        lines.append(s.date_str)
    if s.time_str:
        lines.append(s.time_str)
    return "\n".join(lines)


def render_mentor_broadcast(
    mentor_name: str,
    status: str,
    sessions: List[ParsedSession],
    batch_name: str = "",
    template_manager=None,
) -> str:
    sessions = sorted(sessions, key=sort_key)
    template = (template_manager or get_manager()).get_template("mentor_broadcast")
    
    parts = [
        template["greeting"].format(mentor_name=mentor_name),
        template["intro"].format(mentor_name=mentor_name),
        "",
    ]

    for s in sessions:
        block = [_session_block_header(s)]
        if s.pg_link:
            block.append(f"PG: {s.pg_link}")
        if s.ag_link:
            block.append(f"AG: {s.ag_link}")
        if s.cm_link:
            block.append(f"Link CM: {s.cm_link}")
        for extra in s.extra_resources:
            block.append(extra)
        parts.append("\n".join(block))
        parts.append("")

    if status == "hold" and template.get("hold_note"):
        parts.append(template["hold_note"])
        parts.append("")

    parts.append(template["closing"])
    return "\n".join(parts).strip()


def render_student_broadcast(
    sessions: List[ParsedSession], batch_name: str = "", template_manager=None
) -> str:
    sessions = sorted(sessions, key=sort_key)
    template = (template_manager or get_manager()).get_template("student_broadcast")

    parts = [
        template["title"],
        "",
        template["greeting"],
        template["intro"],
        "",
    ]

    for s in sessions:
        block = [_session_block_header(s)]
        if s.pg_link:
            block.append(f"PG: {s.pg_link}")
        if s.ag_link:
            block.append(f"AG: {s.ag_link}")
        pretest_for_student = s.pretest_student or s.pretest_single
        if pretest_for_student:
            block.append(f"Pretest: {pretest_for_student}")
        if s.student_link:
            block.append(f"Link: {s.student_link}")
        for extra in s.extra_resources:
            block.append(f"Info tambahan: {extra}")
        parts.append("\n".join(block))
        parts.append("")

    parts.append(template["closing"])
    return "\n".join(parts).strip()


def _render_daily_header(session: ParsedSession, template: dict, mentor_name: str = "") -> list[str]:
    # Extract day number dari format "Day 42" atau "day 42"
    import re
    day_match = re.search(r'day\s*(\d+)', session.day, re.IGNORECASE)
    day_number = day_match.group(1) if day_match else session.day
    
    title_text = template["title"].format(day=day_number, materi=session.materi)
    greeting = template["greeting"].format(mentor_name=mentor_name) if mentor_name else template["greeting"]
    
    parts = [
        title_text,
        "",
        greeting,
        template["intro"],
        "",
        template["date_format"].format(date_str=session.date_str),
    ]
    
    if session.time_str:
        parts.append(template["time_format"].format(time_str=session.time_str))
    
    parts.append(template["materi_format"].format(materi=session.materi))
    
    return parts


def render_student_daily_broadcast(session: ParsedSession, template_manager=None) -> str:
    template = (template_manager or get_manager()).get_template("student_daily")
    parts = _render_daily_header(session, template)
    
    # Tambahkan PG / AG jika tersedia
    if session.pg_link:
        parts.extend(["", f"PG: {session.pg_link}"])
    if session.ag_link:
        parts.extend(["", f"AG: {session.ag_link}"])

    pretest = session.pretest_student or session.pretest_single
    if pretest:
        parts.extend(["", template["pretest_format"].format(pretest=pretest)])
        
    if session.student_link:
        parts.extend(["", f"Link: {session.student_link}"])

    parts.extend(
        [
            "",
            template["zoom_label"],
            template["zoom_link"],
            "",
            template["closing"],
        ]
    )
    return "\n".join(parts).strip()


def render_mentor_daily_broadcast(session: ParsedSession, template_manager=None) -> str:
    template = (template_manager or get_manager()).get_template("mentor_daily")
    mentor_name = session.mentor_name if session.mentor_name else "Mentor"
    parts = _render_daily_header(session, template, mentor_name)
    
    # Tambahkan PG / AG / CM Link jika tersedia
    if session.pg_link:
        parts.extend(["", f"PG: {session.pg_link}"])
    if session.ag_link:
        parts.extend(["", f"AG: {session.ag_link}"])
    if session.cm_link:
        parts.extend(["", f"Link CM: {session.cm_link}"])

    parts.extend(
        [
            "",
            template["zoom_label"],
            template["zoom_link"],
            "",
            template["closing"],
        ]
    )
    return "\n".join(parts).strip()


def sessions_for_date(sessions: List[ParsedSession], target_date: datetime.date | None = None) -> List[ParsedSession]:
    # Jika target_date tidak diberikan, gunakan tanggal hari ini waktu Indonesia (WIB / UTC+7)
    if target_date is None:
        tz_wib = datetime.timezone(datetime.timedelta(hours=7))
        target_date = datetime.datetime.now(tz_wib).date()
    
    matched = [session for session in sessions if session.sort_date == target_date]

    # JIKA TIDAK ADA JADWAL HARI INI:
    # Otomatis ambil sesi hari pertama/terdekat yang ada di tabel agar template "Hari Ini" tetap ter-generate
    if not matched and sessions:
        valid_sessions = [s for s in sessions if s.sort_date is not None]
        if valid_sessions:
            first_date = sorted(valid_sessions, key=sort_key)[0].sort_date
            matched = [s for s in valid_sessions if s.sort_date == first_date]
        else:
            # Jika tanggal gagal diparse sama sekali, ambil row pertama
            matched = [sessions[0]]

    return sorted(matched, key=sort_key)