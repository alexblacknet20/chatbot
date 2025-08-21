import flet as ft
from database import create_session, Chat, Message
from gemini_client import GeminiClient
from settings_modal import SettingsModal


class ChatApp:
    """
    A feature-rich AI chat application with a Flet GUI, Gemini API integration,
    and SQLite database persistence.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Zenatra - AI Chat"
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.db_session = create_session()
        self.gemini_client = GeminiClient()
        self.chats = self.load_chats()
        self.current_chat = self.chats[0] if self.chats else self.create_new_chat()

        # UI Components
        self.chat_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.user_input = ft.TextField(hint_text="Type a message...", expand=True)
        self.send_button = ft.IconButton(icon=ft.Icons.SEND, on_click=self.send_message)
        self.sidebar = ft.NavigationDrawer(
            controls=[
                ft.Container(height=12),
                ft.Text("Chats", size=20, weight=ft.FontWeight.BOLD),
            ]
            + [self.create_chat_tile(chat) for chat in self.chats]
        )
        self.page.drawer = self.sidebar

        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.Icons.MENU, on_click=lambda _: self.page.open(self.sidebar)
            ),
            title=ft.Text("Zenatra AI"),
            actions=[
                ft.IconButton(
                    icon=ft.Icons.WB_SUNNY_OUTLINED, on_click=self.toggle_theme
                ),
                ft.IconButton(icon=ft.Icons.ADD, on_click=self.new_chat_clicked),
                ft.IconButton(icon=ft.Icons.SETTINGS, on_click=self.open_settings),
            ],
        )

        self.page.add(
            ft.Column(
                [
                    self.chat_history,
                    ft.Row(
                        [self.user_input, self.send_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                expand=True,
            )
        )
        self.load_chat_history()

    def load_chats(self):
        """Loads all chat sessions from the database."""
        return self.db_session.query(Chat).all()

    def create_new_chat(self):
        """Creates a new chat session and saves it to the database."""
        new_chat = Chat()
        self.db_session.add(new_chat)
        self.db_session.commit()
        self.chats.append(new_chat)
        return new_chat

    def create_chat_tile(self, chat):
        """Creates a ListTile for a chat session in the sidebar."""
        return ft.ListTile(
            title=ft.Text(chat.name),
            on_click=lambda _: self.switch_chat(chat),
            trailing=ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(
                        text="Rename", on_click=lambda _: self.rename_chat(chat)
                    ),
                    ft.PopupMenuItem(
                        text="Delete", on_click=lambda _: self.delete_chat(chat)
                    ),
                ]
            ),
        )

    def new_chat_clicked(self, e):
        self.current_chat = self.create_new_chat()
        self.sidebar.controls.append(self.create_chat_tile(self.current_chat))
        self.load_chat_history()
        self.page.update()

    def switch_chat(self, chat):
        self.current_chat = chat
        self.load_chat_history()
        self.page.close(self.sidebar)
        self.page.update()

    def rename_chat(self, chat):
        self.rename_input = ft.TextField(value=chat.name)
        self.page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Rename Chat"),
            content=self.rename_input,
            actions=[
                ft.TextButton("Save", on_click=lambda _: self.save_chat_name(chat)),
                ft.TextButton("Close", on_click=lambda _: self.close_dialog()),
            ],
        )
        self.page.dialog.open = True
        self.page.update()

    def save_chat_name(self, chat):
        chat.name = self.rename_input.value
        self.db_session.commit()
        self.sidebar.controls = [
            ft.Container(height=12),
            ft.Text("Chats", size=20, weight=ft.FontWeight.BOLD),
        ] + [self.create_chat_tile(c) for c in self.chats]
        self.close_dialog()

    def delete_chat(self, chat):
        self.db_session.delete(chat)
        self.db_session.commit()
        self.chats.remove(chat)
        self.sidebar.controls = [
            ft.Container(height=12),
            ft.Text("Chats", size=20, weight=ft.FontWeight.BOLD),
        ] + [self.create_chat_tile(c) for c in self.chats]
        if self.current_chat == chat:
            self.current_chat = self.chats[0] if self.chats else self.create_new_chat()
            self.load_chat_history()
        self.page.update()

    def load_chat_history(self):
        self.chat_history.controls.clear()
        if self.current_chat:
            for msg in self.current_chat.messages:
                self.add_message_to_history(msg.content, msg.is_user)
        self.page.update()

    def add_message_to_history(self, content, is_user):
        align = (
            ft.CrossAxisAlignment.START if not is_user else ft.CrossAxisAlignment.END
        )
        self.chat_history.controls.append(ft.Row([ft.Text(content)], alignment=align))

    async def send_message(self, e):
        user_message_content = self.user_input.value
        if not user_message_content:
            return

        self.user_input.value = ""
        self.add_message_to_history(user_message_content, True)

        user_message = Message(
            chat_id=self.current_chat.id, content=user_message_content, is_user=True
        )
        self.db_session.add(user_message)
        self.db_session.commit()

        if user_message_content.lower().startswith("/research"):
            parts = user_message_content.split(" ", 1)
            if len(parts) == 2:
                topic = parts[1]
                response_content = await self.gemini_client.scrape_and_summarize(topic)
            else:
                response_content = "Usage: /research <topic>"
        else:
            response_content = await self.gemini_client.generate_content(
                user_message_content
            )

        self.add_message_to_history(response_content, False)
        ai_message = Message(
            chat_id=self.current_chat.id, content=response_content, is_user=False
        )
        self.db_session.add(ai_message)
        self.db_session.commit()
        self.page.update()

    def open_settings(self, e):


        settings_modal = SettingsModal(self.page, self.gemini_client)
        self.page.dialog = settings_modal
        settings_modal.open = True

        self.page.update()

    def close_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
            self.page.dialog = None

    def toggle_theme(self, e):
        self.page.theme_mode = (
            ft.ThemeMode.DARK
            if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        self.page.update()


def main(page: ft.Page):
    ChatApp(page)


if __name__ == "__main__":
    ft.app(target=main)
