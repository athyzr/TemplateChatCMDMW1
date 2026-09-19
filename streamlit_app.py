"""
streamlit_app.py
CM Broadcast Generator - local Streamlit UI.

Run with: streamlit run streamlit_app.py
"""

import html

import streamlit as st
import streamlit.components.v1 as components

from parser import parse_input, group_by_mentor, sort_key, TableFormatError
from templates import (
    render_mentor_broadcast,
    render_mentor_daily_broadcast,
    render_student_broadcast,
    render_student_daily_broadcast,
    sessions_for_date,
)

st.set_page_config(page_title="CM Broadcast Generator", page_icon="📋", layout="wide")


def copy_box(text: str, height: int) -> None:
    escaped_text = html.escape(text)
    components.html(
        f"""
        <style>
            * {{ box-sizing: border-box; }}
            body {{ margin: 0; background: transparent; }}
            .copy-box {{ position: relative; width: 100%; height: {height}px; }}
            textarea {{ width: 100%; height: 100%; resize: none; padding: 12px 48px 12px 12px; border: 1px solid #c9cdd3; border-radius: 6px; background: #fff; color: #202124; font: 14px/1.5 sans-serif; outline: none; }}
            textarea:focus {{ border-color: #ff4b4b; box-shadow: 0 0 0 1px #ff4b4b; }}
            button {{ position: absolute; top: 8px; right: 8px; width: 32px; height: 32px; border: 1px solid #d5d8dc; border-radius: 5px; background: #fff; cursor: pointer; font-size: 17px; line-height: 1; }}
            button:hover {{ background: #f1f3f4; }}
        </style>
        <div class="copy-box">
            <textarea id="copy-text" readonly>{escaped_text}</textarea>
            <button id="copy-button" type="button" title="Copy ke clipboard" aria-label="Copy ke clipboard">📋</button>
        </div>
        <script>
            const textarea = document.getElementById("copy-text");
            const button = document.getElementById("copy-button");
            button.addEventListener("click", async () => {{
                try {{ await navigator.clipboard.writeText(textarea.value); }}
                catch (error) {{ textarea.select(); document.execCommand("copy"); }}
                button.textContent = "✓";
                setTimeout(() => button.textContent = "📋", 1200);
            }});
        </script>
        """,
        height=height,
        scrolling=False,
    )


st.title("📋 CM Broadcast Generator")
st.caption("Paste tabel jadwal pekan ini → Generate → copy broadcast mentor & student.")

with st.form("input_form"):
    raw_table = st.text_area("Paste tabel jadwal pekan ini di bawah:", height=320, placeholder="Paste tabel dari Google Sheets, Excel, atau Markdown di sini...")
    batch_name = st.text_input("Nama kelas/batch (opsional, untuk kalimat pembuka mentor)", placeholder="mis. Digital Marketing Wave 1")
    submitted = st.form_submit_button("🚀 Generate Broadcast", type="primary")

if submitted:
    if not raw_table.strip():
        st.warning("Tabel masih kosong. Paste tabel jadwal terlebih dahulu.")
    else:
        try:
            sessions, row_warnings = parse_input(raw_table)
            st.session_state["sessions"] = sessions
            st.session_state["batch_name"] = batch_name
            st.session_state["row_warnings"] = row_warnings
        except TableFormatError as error:
            st.session_state.pop("sessions", None)
            st.error(str(error))

if "sessions" in st.session_state and st.session_state["sessions"]:
    sessions = st.session_state["sessions"]
    batch_name = st.session_state.get("batch_name", "")
    for warning in st.session_state.get("row_warnings", []):
        st.warning(warning)

    order, groups = group_by_mentor(sessions)
    unassigned = [session for session in sessions if not session.mentor_name]
    all_broadcasts = []

    st.divider()
    st.header("Mentor Broadcast")
    if not order:
        st.info("Tidak ada session dengan mentor terisi pada tabel ini.")
    for mentor_name in order:
        status, mentor_sessions = groups[mentor_name]
        text = render_mentor_broadcast(mentor_name, status, mentor_sessions, batch_name)
        all_broadcasts.append((mentor_name, text))
        label = mentor_name + ("  •  🟡 HOLD" if status == "hold" else "")
        st.subheader(label)
        copy_box(text, min(60 + 40 * text.count("\n"), 400))

    if unassigned:
        with st.expander(f"ℹ️ {len(unassigned)} session tanpa mentor (tidak masuk broadcast mentor)"):
            for session in sorted(unassigned, key=sort_key):
                st.write(f"- {session.day} — {session.materi} ({session.date_str})")

    st.divider()
    st.header("Student Broadcast")
    student_text = render_student_broadcast(sessions, batch_name)
    all_broadcasts.append(("Student", student_text))
    copy_box(student_text, min(60 + 40 * student_text.count("\n"), 500))

    today_sessions = sessions_for_date(sessions)
    st.divider()
    st.header("Broadcast Kelas Hari Ini")
    if not today_sessions:
        st.info("Tidak ada kelas yang tanggalnya sama dengan hari ini pada tabel.")
    else:
        st.subheader("Student - Hari Ini")
        for index, session in enumerate(today_sessions):
            text = render_student_daily_broadcast(session)
            all_broadcasts.append((f"Student hari ini {index + 1}", text))
            copy_box(text, min(60 + 40 * text.count("\n"), 400))

        mentor_today = [session for session in today_sessions if session.mentor_name]
        st.subheader("Mentor - Hari Ini")
        if not mentor_today:
            st.info("Tidak ada mentor terisi untuk kelas hari ini.")
        for index, session in enumerate(mentor_today):
            text = render_mentor_daily_broadcast(session)
            all_broadcasts.append((f"Mentor hari ini {index + 1}", text))
            copy_box(text, min(60 + 40 * text.count("\n"), 400))

    st.divider()
    combined = "\n\n---\n\n".join(text for _, text in all_broadcasts)
    st.subheader("📎 Copy All")
    st.caption("Semua broadcast di atas, digabung berurutan (mentor lalu student).")
    copy_box(combined, 200)
