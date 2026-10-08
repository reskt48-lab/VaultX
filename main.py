import threading
import webbrowser
import urllib.parse

from http.server import BaseHTTPRequestHandler, HTTPServer

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager

from screens import LoginScreen, RegisterScreen
from dashboard import DashboardScreen

from supabase_client import supabase

from crypto_utils import (
    get_or_create_vault_key,
    save_session,
    load_session,
    clear_session,
)


# =========================================================
# GOOGLE OAUTH
# =========================================================

OAUTH_HOST = "127.0.0.1"
OAUTH_PORT = 8765

OAUTH_REDIRECT = (
    f"http://{OAUTH_HOST}:{OAUTH_PORT}/callback"
)


class OAuthCallbackHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Jangan tampilkan log HTTP bawaan
        pass

    def do_GET(self):

        try:
            parsed = urllib.parse.urlparse(
                self.path
            )

            params = urllib.parse.parse_qs(
                parsed.query
            )

            code = params.get(
                "code",
                [None]
            )[0]

            error = params.get(
                "error",
                [None]
            )[0]

            # =================================================
            # GOOGLE ERROR
            # =================================================

            if error:

                print(
                    "Google OAuth error:",
                    error
                )

                self.send_response(400)

                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )

                self.end_headers()

                self.wfile.write(
                    b"""
                    <html>
                    <body>
                        <h2>Google Login gagal.</h2>
                        <p>Silakan kembali ke VaultX.</p>
                    </body>
                    </html>
                    """
                )

                return

            # =================================================
            # CODE TIDAK ADA
            # =================================================

            if not code:

                print(
                    "OAuth code tidak ditemukan."
                )

                self.send_response(400)

                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )

                self.end_headers()

                self.wfile.write(
                    b"""
                    <html>
                    <body>
                        <h2>OAuth code tidak ditemukan.</h2>
                        <p>Silakan kembali ke VaultX.</p>
                    </body>
                    </html>
                    """
                )

                return

            print(
                "OAuth callback diterima."
            )

            app = App.get_running_app()

            # =================================================
            # TUKAR CODE MENJADI SESSION
            # =================================================

            supabase.auth.exchange_code_for_session({
                "auth_code": code
            })

            print(
                "OAuth code berhasil ditukar menjadi session."
            )

            # =================================================
            # RESPONSE KE BROWSER
            # =================================================

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.end_headers()

            self.wfile.write(
                b"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>VaultX</title>
                </head>

                <body>
                    <h2>Google Login berhasil.</h2>
                    <p>Silakan kembali ke aplikasi VaultX.</p>

                    <script>
                        setTimeout(function() {
                            window.close();
                        }, 1000);
                    </script>
                </body>
                </html>
                """
            )

            # =================================================
            # KEMBALI KE THREAD UTAMA KIVY
            # =================================================

            Clock.schedule_once(
                lambda dt: app.google_login_success(),
                0
            )

        except Exception as e:

            print(
                "OAuth callback error:",
                repr(e)
            )

            try:

                self.send_response(500)

                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )

                self.end_headers()

                self.wfile.write(
                    b"""
                    <!DOCTYPE html>
                    <html>
                    <body>
                        <h2>Google Login gagal.</h2>
                        <p>Terjadi kesalahan saat memproses login.</p>
                        <p>Silakan kembali ke VaultX.</p>
                    </body>
                    </html>
                    """
                )

            except Exception:
                pass


# =========================================================
# OAUTH SERVER
# =========================================================

def start_oauth_server():

    try:

        server = HTTPServer(
            (
                OAUTH_HOST,
                OAUTH_PORT
            ),
            OAuthCallbackHandler
        )

        print(
            "OAuth server berjalan di:",
            OAUTH_REDIRECT
        )

        server.serve_forever()

    except OSError as e:

        print(
            "OAuth server gagal dijalankan:",
            repr(e)
        )

    except Exception as e:

        print(
            "OAuth server error:",
            repr(e)
        )


# =========================================================
# VAULTX APP
# =========================================================

class VaultXApp(App):

    title = "VaultX"

    crypto_key = None

    current_user_id = ""
    current_user_email = ""
    last_vaultx_email = ""

    oauth_server_started = False

    # =====================================================
    # BUILD
    # =====================================================

    def build(self):

        manager = ScreenManager()

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        login = LoginScreen(
            name="login"
        )

        login.app = self

        # -------------------------------------------------
        # REGISTER
        # -------------------------------------------------

        register = RegisterScreen(
            name="register"
        )

        register.app = self

        # -------------------------------------------------
        # DASHBOARD
        # -------------------------------------------------

        dashboard = DashboardScreen(
            name="dashboard"
        )

        dashboard.app = self

        # -------------------------------------------------
        # ADD SCREEN
        # -------------------------------------------------

        manager.add_widget(login)
        manager.add_widget(register)
        manager.add_widget(dashboard)

        # =================================================
        # START OAUTH SERVER
        # =================================================

        if not self.oauth_server_started:

            self.oauth_server_started = True

            threading.Thread(
                target=start_oauth_server,
                daemon=True
            ).start()

        # =================================================
        # RESTORE SESSION
        # =================================================

        Clock.schedule_once(
            lambda dt: self.restore_session(),
            0.2
        )

        return manager

    # =====================================================
    # GOOGLE LOGIN
    # =====================================================

    def start_google_login(self):

        try:

            print(
                "Memulai Google OAuth..."
            )

            response = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": OAUTH_REDIRECT
                }
            })

            oauth_url = None

            # Supabase-py response
            if hasattr(
                response,
                "url"
            ):

                oauth_url = response.url

            # Jika response berupa dictionary
            elif isinstance(
                response,
                dict
            ):

                oauth_url = response.get(
                    "url"
                )

            if not oauth_url:

                raise RuntimeError(
                    "URL Google OAuth tidak ditemukan."
                )

            print(
                "Membuka Google OAuth..."
            )

            print(
                "OAuth URL:",
                oauth_url
            )

            webbrowser.open(
                oauth_url
            )

        except Exception as e:

            print(
                "Start Google Login error:",
                repr(e)
            )

            try:

                login = self.root.get_screen(
                    "login"
                )

                login.ids.login_status.text = (
                    "Google Login gagal dibuka."
                )

            except Exception:
                pass

    # =====================================================
    # GOOGLE LOGIN SUCCESS
    # =====================================================

    def google_login_success(self):

        try:

            print(
                "Memproses session Google..."
            )

            session = supabase.auth.get_session()

            if not session:

                raise RuntimeError(
                    "Session Google tidak ditemukan."
                )

            if not session.user:

                raise RuntimeError(
                    "User Google tidak ditemukan."
                )

            # =================================================
            # USER ID
            # =================================================

            user_id = str(
                session.user.id
            )

            # =================================================
            # EMAIL
            # =================================================

            user_email = (
                getattr(
                    session.user,
                    "email",
                    ""
                )
                or ""
            )

            self.current_user_id = user_id

            self.current_user_email = user_email

            self.last_vaultx_email = user_email

            # =================================================
            # CRYPTO KEY
            # =================================================

            self.prepare_crypto_key(
                user_id
            )

            # =================================================
            # SAVE SESSION
            # =================================================

            self.save_current_session()

            # =================================================
            # LOAD DASHBOARD
            # =================================================

            dashboard = self.root.get_screen(
                "dashboard"
            )

            dashboard.load_accounts()

            # =================================================
            # PINDAH KE DASHBOARD
            # =================================================

            self.root.current = "dashboard"

            print(
                "Google Login VaultX berhasil."
            )

        except Exception as e:

            print(
                "Google login success error:",
                repr(e)
            )

            try:

                login = self.root.get_screen(
                    "login"
                )

                login.ids.login_status.text = (
                    "Google Login gagal diproses."
                )

            except Exception:
                pass

    # =====================================================
    # CRYPTO KEY
    # =====================================================

    def prepare_crypto_key(
        self,
        user_id
    ):

        user_id = str(
            user_id
        ).strip()

        if not user_id:

            raise ValueError(
                "User ID kosong."
            )

        self.current_user_id = user_id

        self.crypto_key = get_or_create_vault_key(
            user_id
        )

        print(
            "VaultX crypto key siap."
        )

    # =====================================================
    # SAVE SESSION
    # =====================================================

    def save_current_session(self):

        try:

            session = supabase.auth.get_session()

            if not session:

                print(
                    "Tidak ada session untuk disimpan."
                )

                return False

            access_token = getattr(
                session,
                "access_token",
                None
            )

            refresh_token = getattr(
                session,
                "refresh_token",
                None
            )

            if (
                not access_token
                or not refresh_token
            ):

                print(
                    "Token session tidak lengkap."
                )

                return False

            save_session(
                access_token,
                refresh_token
            )

            print(
                "Session VaultX disimpan."
            )

            return True

        except Exception as error:

            print(
                "Save session error:",
                repr(error)
            )

            return False

    # =====================================================
    # RESTORE SESSION
    # =====================================================

    def restore_session(self):

        try:

            stored = load_session()

            if not stored:

                print(
                    "Tidak ada session VaultX tersimpan."
                )

                return

            print(
                "Mencoba memulihkan session VaultX..."
            )

            supabase.auth.set_session(
                stored["access_token"],
                stored["refresh_token"]
            )

            session = supabase.auth.get_session()

            if (
                not session
                or not session.user
            ):

                raise RuntimeError(
                    "Session berhasil dipulihkan "
                    "tetapi user tidak ditemukan."
                )

            user_id = str(
                session.user.id
            )

            user_email = (
                getattr(
                    session.user,
                    "email",
                    ""
                )
                or ""
            )

            self.current_user_email = user_email

            self.last_vaultx_email = user_email

            self.prepare_crypto_key(
                user_id
            )

            self.save_current_session()

            dashboard = self.root.get_screen(
                "dashboard"
            )

            dashboard.load_accounts()

            self.root.current = "dashboard"

            print(
                "Session VaultX berhasil dipulihkan."
            )

        except Exception as error:

            print(
                "Restore session gagal:",
                repr(error)
            )

            clear_session()

            self.crypto_key = None

            self.current_user_id = ""

            self.current_user_email = ""

    # =====================================================
    # LOGOUT
    # =====================================================

    def logout(self):

        try:

            supabase.auth.sign_out()

            print(
                "Supabase logout berhasil."
            )

        except Exception as error:

            print(
                "Logout error:",
                repr(error)
            )

        # Hanya hapus session login
        # Data vault tetap ada

        clear_session()

        self.crypto_key = None

        self.current_user_id = ""

        self.current_user_email = ""

        self.root.current = "login"

        try:

            login = self.root.get_screen(
                "login"
            )

            if "login_password" in login.ids:

                login.ids.login_password.text = ""

        except Exception as error:

            print(
                "Reset login form error:",
                repr(error)
            )

        print(
            "Logout selesai."
        )

        print(
            "Data password tetap tersimpan."
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    VaultXApp().run()