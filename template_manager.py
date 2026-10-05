"""
template_manager.py
Manages custom broadcast templates with variable substitution.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

TEMPLATES_FILE = Path(__file__).parent / "custom_templates.json"

# Default templates dengan variable placeholders
DEFAULT_TEMPLATES = {
    "mentor_broadcast": {
        "greeting": "Halo {mentor_name} 👋",
        "intro": "Izin menginformasikan jadwal kelas {mentor_name} untuk pekan ini yaa, berikut detailnya :",
        "session_format": "{session_header}\n{pg_link}\n{ag_link}\n{cm_link}\n{extra_resources}",
        "closing": "Terima kasih banyak, Mba! Semangat dan sampai ketemu di kelas! ✨",
        "hold_note": ""  # Kosongkan jika tidak ingin hold message
    },
    "student_broadcast": {
        "title": "📚 KELAS PEKAN INI",
        "greeting": "Halo, teman-teman! 👋",
        "intro": "Berikut jadwal kelas dan kegiatan kita untuk pekan ini. Jangan lupa dicatat dan dipersiapkan, yaa! ✨",
        "session_format": "{session_header}\n{pg_link}\n{ag_link}\n{pretest}\n{student_link}\n{extra_resources}",
        "closing": "Jangan lupa disiapkan ya, teman-teman. Kalau ada pertanyaan langsung chat di sini aja 🙌"
    },
    "student_daily": {
        "title": "🌟 *D-Day {day} : {materi}* 🌟",
        "greeting": "Halo, Student! 👋✨",
        "intro": "Persiapkan dirimu untuk kelas malam ini yaaa, berikut detail kelasnya! 👇",
        "date_format": "📆 *{date_str}*",
        "time_format": "⏰ *{time_str}*",
        "materi_format": "📖 *Materi: {materi}*",
        "pretest_format": "📝 *Pre-test:* {pretest}",
        "zoom_label": "💻 *Zoom:*",
        "zoom_link": "https://zoom.us/j/94645699192?pwd=8rxbJHGvzMoY4x3tuGpQIbnsbNm5MT.1",
        "closing": "Jangan lupa hadir tepat waktu dan siapkan diri untuk kelas hari ini yaa! 📚✨\n\nTerima kasih, tetap semangat, dan *see you tonight!* 👋😁"
    },
    "mentor_daily": {
        "title": "🌟 *D-Day {day} : {materi}* 🌟",
        "greeting": "Halo, {mentor_name}! 👋✨",
        "intro": "Persiapkan dirimu untuk kelas malam ini yaaa, berikut detail kelasnya! 👇",
        "date_format": "📆 *{date_str}*",
        "time_format": "⏰ *{time_str}*",
        "materi_format": "📖 *Materi: {materi}*",
        "zoom_label": "💻 *Zoom:*",
        "zoom_link": "https://zoom.us/j/94645699192?pwd=8rxbJHGvzMoY4x3tuGpQIbnsbNm5MT.1",
        "closing": "Mohon hadir tepat waktu ya. Terima kasih 🙏"
    }
}


class TemplateManager:
    def __init__(self):
        self.templates = self.load_templates()

    def load_templates(self) -> Dict[str, Any]:
        """Load templates from file, or create default if not exists."""
        if TEMPLATES_FILE.exists():
            try:
                with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return DEFAULT_TEMPLATES.copy()
        return DEFAULT_TEMPLATES.copy()

    def save_templates(self) -> None:
        """Save current templates to file."""
        with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.templates, f, indent=2, ensure_ascii=False)

    def get_template(self, template_name: str) -> Dict[str, str]:
        """Get a specific template."""
        return self.templates.get(template_name, DEFAULT_TEMPLATES.get(template_name, {}))

    def update_template(self, template_name: str, template_data: Dict[str, str]) -> None:
        """Update a template."""
        self.templates[template_name] = template_data
        self.save_templates()

    def reset_template(self, template_name: str) -> None:
        """Reset a template to default."""
        if template_name in DEFAULT_TEMPLATES:
            self.templates[template_name] = DEFAULT_TEMPLATES[template_name].copy()
            self.save_templates()

    def reset_all(self) -> None:
        """Reset all templates to default."""
        self.templates = DEFAULT_TEMPLATES.copy()
        self.save_templates()


# Global instance
_manager = None


def get_manager() -> TemplateManager:
    """Get singleton template manager instance."""
    global _manager
    if _manager is None:
        _manager = TemplateManager()
    return _manager
