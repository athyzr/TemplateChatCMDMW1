"""
templates.py
Turns ParsedSession objects into WhatsApp-ready broadcast text.
Casual Bahasa Indonesia, single-asterisk emphasis, no invented content -
if the table didn't say it, it doesn't appear here.
"""

import datetime
from typing import List
from parser import ParsedSession, sort_key


ZOOM_LINK = "https://zoom.us/j/94645699192?pwd=8rxbJHGvzMoY4x3tuGpQIbnsbNm5MT.1"


def _session_block_header(s: ParsedSession) -> str:
    lines = [f"*{s.day} — {s.materi}*"]
    if s.date_str:
        lines.append(s.date_str)
    if s.time_str:
        lines.append(s.time_str)
    return "\n".join(lines)


def render_mentor_broadcast(mentor_name: str, status: str, sessions: List[ParsedSession], batch_name: str = "") -> str:
    sessions = sorted(sessions, key=sort_key)
    cm_label = f" {batch_name}" if batch_name.strip() else ""

    parts = [
        f"Halo {mentor_name} 👋",
        f"Saya Athiya, selaku CM{cm_label}.",
        "Izin menginformasikan jadwal kelas {mentor_name} untuk pekan ini yaa, berikut detailnya :",
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

    # if status == "hold":
    #     parts.append("Status jadwal Kakak masih *hold* ya, mohon infokan kalau ada update dari sisi Kakak 🙏")
    #     parts.append("")

    parts.append("Terima kasih banyak, Mba! Semangat dan sampai ketemu di kelas! ✨")
    return "\n".join(parts).strip()


def render_student_broadcast(sessions: List[ParsedSession], batch_name: str = "") -> str:
    sessions = sorted(sessions, key=sort_key)

    parts = [
        "Halo, teman-teman! 👋",
        "Berikut jadwal pembelajaran untuk pekan ini:",
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

    parts.append("Jangan lupa disiapkan ya, teman-teman. Kalau ada pertanyaan langsung chat di sini aja 🙌")
    return "\n".join(parts).strip()


def _render_daily_header(session: ParsedSession, audience: str) -> list[str]:
    title = "Student" if audience == "student" else audience
    return [
        f"🌟 *D-Day: {session.materi}* 🌟",
        "",
        f"Halo, {title}! 👋✨",
        "",
        f"📆 *{session.date_str}*",
        f"⏰ *{session.time_str}*" if session.time_str else "",
        f"📖 *Materi: {session.materi}*",
    ]


def render_student_daily_broadcast(session: ParsedSession) -> str:
    parts = _render_daily_header(session, "student")
    pretest = session.pretest_student or session.pretest_single
    if pretest:
        parts.extend(["", f"📝 *Pre-test:* {pretest}"])
    parts.extend(
        [
            "",
            "💻 *Zoom:*",
            ZOOM_LINK,
            "",
            "Jangan lupa hadir tepat waktu dan siapkan diri untuk kelas hari ini yaa! 📚✨",
            "",
            "Terima kasih, tetap semangat, dan *see you tonight!* 👋😁",
        ]
    )
    return "\n".join(line for line in parts if line != "").strip()


def render_mentor_daily_broadcast(session: ParsedSession) -> str:
    parts = _render_daily_header(session, f"Kak {session.mentor_name or 'Mentor'}")
    parts.extend(
        [
            "",
            "💻 *Zoom:*",
            ZOOM_LINK,
            "",
            "Mohon hadir tepat waktu ya, Kak. Terima kasih 🙏",
        ]
    )
    return "\n".join(line for line in parts if line != "").strip()


def sessions_for_date(sessions: List[ParsedSession], target_date: datetime.date | None = None) -> List[ParsedSession]:
    target_date = target_date or datetime.date.today()
    return sorted(
        [session for session in sessions if session.sort_date == target_date],
        key=sort_key,
    )