from kivy.app import App
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen

from supabase_client import supabase


class LoginScreen(Screen):

    saved_email = StringProperty("")

    password_visible = BooleanProperty(False)

    def on_pre_enter(self):

        app = App.get_running_app()

        if not self.saved_email:

            self.saved_email = getattr(
                app,
                "last_vaultx_email",
                ""
            )

        try:

            session = (
                supabase.auth.get_session()
            )

            if session and session.user:

                app.prepare_crypto_key(
                    session.user.id
                )

                app.root.current = "dashboard"

                dashboard = (
                    app.root.get_screen(
                        "dashboard"
                    )
                )

                dashboard.load_accounts()

        except Exception as error:

            print(
                "Session check error:",
                repr(error)
            )

    def toggle_password_visibility(self):

        self.password_visible = (
            not self.password_visible
        )

    def login_vaultx(
        self,
        password
    ):

        password = password.strip()

        if not password:

            self.ids.login_status.text = (
                "Masukkan password."
            )

            return

        email = self.saved_email.strip()

        if not email:

            self.ids.login_status.text = (
                "Belum ada akun VaultX. "
                "Buat akun terlebih dahulu."
            )

            return

        try:

            response = (
                supabase.auth.sign_in_with_password(
                    {
                        "email": email,
                        "password": password
                    }
                )
            )

            if response.user:

                app = App.get_running_app()

                app.last_vaultx_email = email

                app.prepare_crypto_key(
                    response.user.id
                )

                app.save_current_session()

                self.ids.login_status.text = ""

                app.root.current = "dashboard"

                dashboard = (
                    app.root.get_screen(
                        "dashboard"
                    )
                )

                dashboard.load_accounts()

            else:

                self.ids.login_status.text = (
                    "Login gagal."
                )

        except Exception as error:

            print(
                "VaultX login error:",
                repr(error)
            )

            self.ids.login_status.text = (
                "Password salah atau login gagal."
            )

    def login_google(self):

        app = App.get_running_app()

        try:

            self.ids.login_status.text = (
                "Membuka Google Login..."
            )

            app.start_google_login()

        except Exception as error:

            print(
                "Google Login error:",
                repr(error)
            )

            self.ids.login_status.text = (
                "Google Login gagal dibuka."
            )

    def create_account(self):

        app = App.get_running_app()

        app.root.current = "register"


class RegisterScreen(Screen):

    register_password_visible = BooleanProperty(False)

    register_confirm_visible = BooleanProperty(False)

    def toggle_register_password(self):

        self.register_password_visible = (
            not self.register_password_visible
        )

    def toggle_register_confirm(self):

        self.register_confirm_visible = (
            not self.register_confirm_visible
        )

    def register_vaultx(
        self,
        email,
        password,
        confirm_password
    ):

        email = email.strip()

        password = password.strip()

        confirm_password = (
            confirm_password.strip()
        )

        if (
            not email
            or not password
            or not confirm_password
        ):

            self.ids.register_status.text = (
                "Semua kolom harus diisi."
            )

            return

        if password != confirm_password:

            self.ids.register_status.text = (
                "Password tidak sama."
            )

            return

        if len(password) < 8:

            self.ids.register_status.text = (
                "Password minimal 8 karakter."
            )

            return

        try:

            response = (
                supabase.auth.sign_up(
                    {
                        "email": email,
                        "password": password
                    }
                )
            )

            if response.user:

                app = App.get_running_app()

                app.last_vaultx_email = email

                login = (
                    app.root.get_screen(
                        "login"
                    )
                )

                login.saved_email = email

                if response.session:

                    app.prepare_crypto_key(
                        response.user.id
                    )

                    app.save_current_session()

                    app.root.current = "dashboard"

                    dashboard = (
                        app.root.get_screen(
                            "dashboard"
                        )
                    )

                    dashboard.load_accounts()

                else:

                    self.ids.register_status.text = (
                        "Akun berhasil dibuat. "
                        "Silakan cek email untuk verifikasi."
                    )

            else:

                self.ids.register_status.text = (
                    "Gagal membuat akun."
                )

        except Exception as error:

            print(
                "Register error:",
                repr(error)
            )

            self.ids.register_status.text = (
                "Gagal membuat akun. "
                "Email mungkin sudah digunakan."
            )

    def back_to_login(self):

        app = App.get_running_app()

        app.root.current = "login"