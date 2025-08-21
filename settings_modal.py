import flet as ft
from database import SessionLocal


class SettingsModal(ft.AlertDialog):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.title = ft.Text("Settings")
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

    @property
    def api_key_field(self):
        return ft.TextField(
            label="API Key",
            password=True,
            can_reveal_password=True,
            value=self.get_api_key(),
            width=300,
        )

    def get_api_key(self):
        # TODO: Implement secure API key retrieval
        return ""

    def save_settings(self, e):
        # TODO: Implement secure API key storage
        self.page.snack_bar = ft.SnackBar(
            ft.Text("Settings saved successfully!"), open=True
        )
        self.page.update()
        self.open = False
        self.page.update()
