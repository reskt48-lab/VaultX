from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout


class LoginScreen(BoxLayout):

    app = ObjectProperty(None)

    def login(self):
        email = self.ids.email.text.strip()
        password = self.ids.password.text

        if not email or not password:
            self.ids.message.text = "Email dan password wajib diisi."
            return

        self.ids.message.text = "Login berhasil."
        self.app.show_dashboard()

    def register(self):
        self.app.show_register()


class RegisterScreen(BoxLayout):

    app = ObjectProperty(None)

    def create_account(self):
        name = self.ids.name.text.strip()
        email = self.ids.email.text.strip()
        password = self.ids.password.text

        if not name or not email or not password:
            self.ids.message.text = "Semua data wajib diisi."
            return

        self.ids.message.text = "Registrasi berhasil."

    def back_to_login(self):
        self.app.show_login()