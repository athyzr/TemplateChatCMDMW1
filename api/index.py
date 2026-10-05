import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit

# Tambahkan direktori root ke path agar modul lokal terbaca
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from parser import TableFormatError, group_by_mentor, parse_input
from templates import (
    render_mentor_broadcast,
    render_mentor_daily_broadcast,
    render_student_broadcast,
    render_student_daily_broadcast,
    sessions_for_date,
)
from template_manager import DEFAULT_TEMPLATES, TemplateManager, get_manager


def session_to_dict(session):
    return {
        "day": session.day,
        "date_str": session.date_str,
        "time_str": session.time_str,
        "materi": session.materi,
        "mentor_name": session.mentor_name,
        "sort_date": session.sort_date.isoformat() if session.sort_date else None,
    }


def generate_broadcasts(payload):
    sessions, warnings = parse_input(payload.get("raw_table", ""))
    batch_name = payload.get("batch_name", "")
    template_manager = TemplateManager()
    overrides = payload.get("templates", {})
    if isinstance(overrides, dict):
        for template_name, fields in overrides.items():
            if template_name not in DEFAULT_TEMPLATES or not isinstance(fields, dict):
                continue
            template = template_manager.get_template(template_name).copy()
            for field_name in template:
                value = fields.get(field_name)
                if isinstance(value, str):
                    template[field_name] = value
            template_manager.templates[template_name] = template

    order, groups = group_by_mentor(sessions)

    broadcasts = []
    for mentor_name in order:
        status, mentor_sessions = groups[mentor_name]
        broadcasts.append({
            "type": "Mentor - Pekan Ini",
            "title": mentor_name,
            "status": status,
            "text": render_mentor_broadcast(
                mentor_name, status, mentor_sessions, batch_name, template_manager
            ),
        })

    broadcasts.append({
        "type": "Student - Pekan Ini",
        "title": "Jadwal Student",
        "text": render_student_broadcast(sessions, batch_name, template_manager),
    })

    today_sessions = sessions_for_date(sessions)
    for session in today_sessions:
        broadcasts.append({
            "type": "Student - Hari Ini",
            "title": session.materi,
            "text": render_student_daily_broadcast(session, template_manager),
        })
    for session in today_sessions:
        if session.mentor_name:
            broadcasts.append({
                "type": "Mentor - Hari Ini",
                "title": session.mentor_name,
                "text": render_mentor_daily_broadcast(session, template_manager),
            })

    return {
        "broadcasts": broadcasts,
        "warnings": warnings,
        "sessions": [session_to_dict(session) for session in sessions],
    }


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        request_url = urlsplit(self.path)
        if parse_qs(request_url.query).get("resource") == ["templates"]:
            self._send_json(200, {
                "templates": get_manager().templates,
                "defaults": DEFAULT_TEMPLATES,
            })
            return

        # Menyajikan index.html saat web dibuka via browser
        html_path = os.path.join(BASE_DIR, "index.html")
        if os.path.exists(html_path):
            with open(html_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self._send_json(404, {"error": "File index.html tidak ditemukan di root folder"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            self._send_json(200, generate_broadcasts(payload))
        except TableFormatError as error:
            self._send_json(400, {"error": str(error)})
        except Exception as error:
            self._send_json(500, {"error": f"Terjadi kesalahan: {error}"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()