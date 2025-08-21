import json
import os

import flet as ft

SETTINGS_FILE = "settings.json"


def load_api_key():
    """Read API key from local settings file if available."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("GEMINI_API_KEY", "")
        except Exception:
            return ""
    return ""


class SettingsModal(ft.AlertDialog):
    def __init__(self, page, gemini_client):
        super().__init__()
        self.page = page
        self.gemini_client = gemini_client
        self.title = ft.Text("Settings")
        self.api_key_field = ft.TextField(
            label="API Key",
            password=True,
            can_reveal_password=True,
            value=load_api_key(),
            width=300,
        )
        self.content = ft.Column(
            controls=[
                ft.Text("Gemini API Key:", weight=ft.FontWeight.BOLD),
                self.api_key_field,
                ft.ElevatedButton("Save", on_click=self.save_settings),
            ],
            tight=True,
        )
        self.actions_alignment = ft.MainAxisAlignment.END
        self.modal = True

    def save_settings(self, e):
        api_key = self.api_key_field.value
        self.gemini_client.set_api_key(api_key)
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"GEMINI_API_KEY": api_key}, f)
        except Exception:
            pass
        self.page.snack_bar = ft.SnackBar(ft.Text("Settings saved successfully!"), open=True)
        self.page.update()
        self.open = False
        self.page.update()
