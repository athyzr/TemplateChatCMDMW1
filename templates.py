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
        f"Izin menginformasikan jadwal kelas {mentor_name} untuk pekan ini yaa, berikut detailnya :",
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
        "📚 KELAS PEKAN INI",
        ""
        "Halo, teman-teman! 👋"
        "Berikut jadwal kelas dan kegiatan kita untuk pekan ini. Jangan lupa dicatat dan dipersiapkan, yaa! ✨"

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
        "Persiapkan dirimu untuk kelas malam ini yaaa, berikut detail kelasnya! 👇"
        "",
        f"📆 *{session.date_str}*",
        f"⏰ *{session.time_str}*" if session.time_str else "",
        f"📖 *Materi: {session.materi}*",
    ]


def render_student_daily_broadcast(session: ParsedSession) -> str:
    parts = _render_daily_header(session, "student")
    
    # Tambahkan PG / AG jika tersedia
    if session.pg_link:
        parts.extend(["", f"PG: {session.pg_link}"])
    if session.ag_link:
        parts.extend(["", f"AG: {session.ag_link}"])

    pretest = session.pretest_student or session.pretest_single
    if pretest:
        parts.extend(["", f"📝 *Pre-test:* {pretest}"])
        
    if session.student_link:
        parts.extend(["", f"Link: {session.student_link}"])

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
            "💻 *Zoom:*",
            ZOOM_LINK,
            "",
            "Mohon hadir tepat waktu ya, Kak. Terima kasih 🙏",
        ]
    )
    return "\n".join(line for line in parts if line != "").strip()


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