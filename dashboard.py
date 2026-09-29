from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout


class PasswordCard(BoxLayout):

    website = StringProperty("")
    username = StringProperty("")
    password = StringProperty("")

    password_visible = BooleanProperty(False)

    def toggle_password(self):
        self.password_visible = not self.password_visible

    @property
    def password_display(self):
        if self.password_visible:
            return f"Password: {self.password}"

        return "Password: ••••••••"

    @property
    def show_button_text(self):
        return "HIDE" if self.password_visible else "SHOW"


class DashboardScreen(BoxLayout):

    app = ObjectProperty(None)

    accounts = [
        {
            "website": "Example.com",
            "username": "user@example.com",
            "password": "Password123!",
        },
        {
            "website": "GitHub",
            "username": "vaultx-user",
            "password": "Github123!",
        },
    ]

    def on_kv_post(self, base_widget):
        self.refresh_accounts()

    def refresh_accounts(self, accounts=None):
        account_list = self.ids.account_list
        account_list.clear_widgets()

        data = accounts if accounts is not None else self.accounts

        for account in data:
            card = PasswordCard(
                website=account["website"],
                username=account["username"],
                password=account["password"],
            )

            account_list.add_widget(card)

    def filter_accounts(self, keyword):
        keyword = keyword.lower().strip()

        if not keyword:
            self.refresh_accounts()
            return

        filtered = [
            account
            for account in self.accounts
            if keyword in account["website"].lower()
            or keyword in account["username"].lower()
        ]

        self.refresh_accounts(filtered)

    def add_password(self):
        self.app.show_message(
            "Form tambah password akan dibuat di tahap berikutnya."
        )

    def logout(self):
        self.app.show_login()