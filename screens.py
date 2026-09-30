from kivy.app import App
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen

from supabase_client import supabase

import webbrowser


class LoginScreen(Screen):
    saved_email = StringProperty("")

    # Untuk Show / Hide password login
    password_visible = BooleanProperty(False)

    def on_pre_enter(self):
        app = App.get_running_app()

        # Ambil email terakhir jika tersedia
        if not self.saved_email:
            self.saved_email = getattr(app, "last_vaultx_email", "")

        try:
            session = supabase.auth.get_session()

            if session and session.user:
                app.prepare_crypto_key(session.user.id)
                app.root.current = "dashboard"

                dashboard = app.root.get_screen("dashboard")
                dashboard.load_accounts()

        except Exception as e:
            print("Session check error:", e)

    # ========================================================
    # SHOW / HIDE PASSWORD LOGIN
    # ========================================================

    def toggle_password_visibility(self):
        self.password_visible = not self.password_visible

    # ========================================================
    # LOGIN VAULTX
    # ========================================================

    def login_vaultx(self, password):
        password = password.strip()

        if not password:
            self.ids.login_status.text = "Masukkan password."
            return

        email = self.saved_email.strip()

        if not email:
            self.ids.login_status.text = (
                "Belum ada akun VaultX. Buat akun terlebih dahulu."
            )
            return

        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response.user:
                app = App.get_running_app()

                app.last_vaultx_email = email

                # Siapkan encryption key untuk user
                app.prepare_crypto_key(response.user.id)

                # Simpan session lokal
                app.save_current_session()

                print("VaultX login berhasil.")

                self.ids.login_status.text = ""

                app.root.current = "dashboard"

                dashboard = app.root.get_screen("dashboard")
                dashboard.load_accounts()

            else:
                self.ids.login_status.text = "Login gagal."

        except Exception as e:
            print("VaultX login error:", e)

            self.ids.login_status.text = (
                "Password salah atau login gagal."
            )

    # ========================================================
    # GOOGLE LOGIN
    # ========================================================

    def login_google(self):
        try:
            response = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": "http://127.0.0.1:8765/callback"
                }
            })

            print("Google OAuth:", response)

            if response and response.url:
                webbrowser.open(response.url)

        except Exception as e:
            print("Google login error:", e)

            self.ids.login_status.text = (
                "Google Login gagal."
            )

    # ========================================================
    # KE REGISTER
    # ========================================================

    def create_account(self):
        app = App.get_running_app()
        app.root.current = "register"


class RegisterScreen(Screen):
    # ========================================================
    # SHOW / HIDE PASSWORD REGISTER
    # ========================================================

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

    # ========================================================
    # REGISTER
    # ========================================================

    def register_vaultx(
        self,
        email,
        password,
        confirm_password
    ):
        email = email.strip()
        password = password.strip()
        confirm_password = confirm_password.strip()

        if not email or not password or not confirm_password:
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
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if response.user:

                app = App.get_running_app()

                app.last_vaultx_email = email

                login = app.root.get_screen("login")
                login.saved_email = email

                # Kalau email confirmation dimatikan,
                # Supabase langsung memberikan session.
                if response.session:

                    app.prepare_crypto_key(
                        response.user.id
                    )

                    app.save_current_session()

                    app.root.current = "dashboard"

                    dashboard = app.root.get_screen(
                        "dashboard"
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

        except Exception as e:
            print("Register error:", e)

            self.ids.register_status.text = (
                "Gagal membuat akun. "
                "Email mungkin sudah digunakan."
            )

    # ========================================================
    # KEMBALI KE LOGIN
    # ========================================================

    def back_to_login(self):
        app = App.get_running_app()
        app.root.current = "login"