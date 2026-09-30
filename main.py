import threading
import urllib.parse
import webbrowser

from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer,
)

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager

from screens import (
    LoginScreen,
    RegisterScreen,
)

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


# =========================================================
# GOOGLE CALLBACK HANDLER
# =========================================================

class OAuthCallbackHandler(
    BaseHTTPRequestHandler
):

    def do_GET(self):

        parsed = urllib.parse.urlparse(
            self.path
        )

        # -------------------------------------------------
        # CALLBACK CHECK
        # -------------------------------------------------

        if parsed.path != "/callback":

            self.send_response(404)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )

            self.end_headers()

            self.wfile.write(
                b"""
                <h2>VaultX</h2>
                <p>Callback tidak ditemukan.</p>
                """
            )

            return

        query = urllib.parse.parse_qs(
            parsed.query
        )

        # -------------------------------------------------
        # OAUTH ERROR
        # -------------------------------------------------

        error = query.get(
            "error",
            [None]
        )[0]

        error_description = query.get(
            "error_description",
            [None]
        )[0]

        if error:

            print(
                "Google OAuth error:",
                error
            )

            print(
                "Description:",
                error_description
            )

            self.send_response(400)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )

            self.end_headers()

            html = f"""
            <!DOCTYPE html>

            <html>

            <head>
                <meta charset="UTF-8">
                <title>VaultX</title>
            </head>

            <body>

                <h2>VaultX</h2>

                <p>
                    Login Google dibatalkan
                    atau gagal.
                </p>

                <p>
                    {error_description or error}
                </p>

                <p>
                    Silakan kembali ke
                    aplikasi VaultX.
                </p>

            </body>

            </html>
            """

            self.wfile.write(
                html.encode("utf-8")
            )

            return

        # -------------------------------------------------
        # AUTH CODE
        # -------------------------------------------------

        code = query.get(
            "code",
            [None]
        )[0]

        if not code:

            self.send_response(400)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )

            self.end_headers()

            self.wfile.write(
                b"""
                <h2>VaultX</h2>
                <p>
                    Authorization code
                    tidak ditemukan.
                </p>
                """
            )

            return

        print(
            "Google OAuth callback diterima."
        )

        # -------------------------------------------------
        # EXCHANGE CODE -> SESSION
        # -------------------------------------------------

        try:

            response = (
                supabase.auth.exchange_code_for_session(
                    {
                        "auth_code": code
                    }
                )
            )

            print(
                "Google OAuth code berhasil "
                "ditukar menjadi session."
            )

            # -------------------------------------------------
            # AMBIL APP
            # -------------------------------------------------

            app = App.get_running_app()

            if app:

                Clock.schedule_once(
                    lambda dt: (
                        app.google_login_success()
                    ),
                    0
                )

            # -------------------------------------------------
            # BROWSER RESPONSE
            # -------------------------------------------------

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )

            self.end_headers()

            html = """
            <!DOCTYPE html>

            <html>

            <head>

                <meta charset="UTF-8">

                <title>
                    VaultX
                </title>

                <style>

                    body {
                        font-family: Arial;
                        text-align: center;
                        padding-top: 100px;
                        background: #111318;
                        color: white;
                    }

                    h2 {
                        color: #4d9cff;
                    }

                </style>

            </head>

            <body>

                <h2>
                    VaultX
                </h2>

                <p>
                    Google Login berhasil.
                </p>

                <p>
                    Kamu bisa kembali ke
                    aplikasi VaultX.
                </p>

                <script>

                    setTimeout(
                        function() {
                            window.close();
                        },
                        1500
                    );

                </script>

            </body>

            </html>
            """

            self.wfile.write(
                html.encode("utf-8")
            )

        except Exception as error:

            print(
                "OAuth exchange error:",
                repr(error)
            )

            self.send_response(500)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )

            self.end_headers()

            self.wfile.write(
                b"""
                <h2>VaultX</h2>
                <p>Google Login gagal.</p>
                <p>
                    Silakan kembali ke
                    aplikasi VaultX.
                </p>
                """
            )

    def log_message(
        self,
        format,
        *args
    ):

        # Jangan tampilkan log HTTP
        # terlalu banyak di terminal.

        return


# =========================================================
# START OAUTH SERVER
# =========================================================

def start_oauth_server():

    try:

        server = HTTPServer(
            (
                OAUTH_HOST,
                OAUTH_PORT,
            ),
            OAuthCallbackHandler,
        )

        print(
            "=" * 55
        )

        print(
            "VaultX Google OAuth "
            "callback server aktif"
        )

        print(
            f"Callback: {OAUTH_REDIRECT}"
        )

        print(
            "=" * 55
        )

        server.serve_forever()

    except OSError as error:

        print(
            "OAuth callback server "
            "gagal dijalankan:"
        )

        print(
            repr(error)
        )

        print(
            f"Pastikan port {OAUTH_PORT} "
            "tidak sedang digunakan."
        )


# =========================================================
# MAIN APP
# =========================================================

class VaultXApp(App):

    title = "VaultX"

    # -----------------------------------------------------
    # ENCRYPTION KEY
    # -----------------------------------------------------

    crypto_key = None

    # -----------------------------------------------------
    # USER INFO
    # -----------------------------------------------------

    current_user_id = ""

    current_user_email = ""

    last_vaultx_email = ""

    # =====================================================
    # BUILD
    # =====================================================

    def build(self):

        # -------------------------------------------------
        # START GOOGLE CALLBACK SERVER
        # -------------------------------------------------

        oauth_thread = threading.Thread(
            target=start_oauth_server,
            daemon=True,
        )

        oauth_thread.start()

        # -------------------------------------------------
        # SCREEN MANAGER
        # -------------------------------------------------

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

        manager.add_widget(
            login
        )

        manager.add_widget(
            register
        )

        manager.add_widget(
            dashboard
        )

        # -------------------------------------------------
        # COBA PULIHKAN SESSION
        # -------------------------------------------------

        Clock.schedule_once(
            lambda dt: (
                self.restore_session()
            ),
            0.2
        )

        return manager

    # =====================================================
    # PREPARE CRYPTO KEY
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

        # Simpan user ID aktif.

        self.current_user_id = (
            user_id
        )

        # Ambil / buat Vault Key
        # khusus user tersebut.

        self.crypto_key = (
            get_or_create_vault_key(
                user_id
            )
        )

        print(
            "VaultX crypto key siap."
        )

    # =====================================================
    # SAVE CURRENT SESSION
    # =====================================================

    def save_current_session(self):

        try:

            session = (
                supabase.auth.get_session()
            )

            if not session:

                print(
                    "Tidak ada session "
                    "untuk disimpan."
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
                    "Tidak ada session "
                    "VaultX tersimpan."
                )

                return

            print(
                "Mencoba memulihkan "
                "session VaultX..."
            )

            response = (
                supabase.auth.set_session(
                    stored["access_token"],
                    stored["refresh_token"],
                )
            )

            # -------------------------------------------------
            # AMBIL USER
            # -------------------------------------------------

            session = (
                supabase.auth.get_session()
            )

            if not session or not session.user:

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

            self.current_user_email = (
                user_email
            )

            # -------------------------------------------------
            # SIAPKAN CRYPTO KEY
            # -------------------------------------------------

            self.prepare_crypto_key(
                user_id
            )

            # -------------------------------------------------
            # SIMPAN TOKEN BARU
            # -------------------------------------------------

            self.save_current_session()

            # -------------------------------------------------
            # DASHBOARD
            # -------------------------------------------------

            dashboard = (
                self.root.get_screen(
                    "dashboard"
                )
            )

            dashboard.load_accounts()

            self.root.current = (
                "dashboard"
            )

            print(
                "Session VaultX berhasil "
                "dipulihkan."
            )

        except Exception as error:

            print(
                "Restore session gagal:",
                repr(error)
            )

            # Session lokal sudah tidak valid.

            clear_session()

            self.crypto_key = None

            self.current_user_id = ""

            self.current_user_email = ""

    # =====================================================
    # GOOGLE LOGIN SUCCESS
    # =====================================================

    def google_login_success(self):

        print(
            "VaultX menerima Google session."
        )

        try:

            session = (
                supabase.auth.get_session()
            )

            if not session or not session.user:

                raise RuntimeError(
                    "Google session tidak ditemukan."
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

            self.current_user_email = (
                user_email
            )

            # -------------------------------------------------
            # SIAPKAN VAULT KEY GOOGLE
            # -------------------------------------------------

            self.prepare_crypto_key(
                user_id
            )

            # -------------------------------------------------
            # SIMPAN SESSION
            # -------------------------------------------------

            self.save_current_session()

            # -------------------------------------------------
            # DASHBOARD
            # -------------------------------------------------

            dashboard = (
                self.root.get_screen(
                    "dashboard"
                )
            )

            dashboard.load_accounts()

            self.root.current = (
                "dashboard"
            )

            print(
                "VaultX berhasil masuk "
                "ke Dashboard."
            )

        except Exception as error:

            print(
                "Gagal membuka Dashboard "
                "setelah Google Login:"
            )

            print(
                repr(error)
            )

            self.crypto_key = None

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

        # -------------------------------------------------
        # HAPUS SESSION LOKAL
        # -------------------------------------------------

        clear_session()

        # -------------------------------------------------
        # JANGAN HAPUS VAULT KEY
        # JANGAN HAPUS DATA
        # -------------------------------------------------

        self.crypto_key = None

        self.current_user_id = ""

        self.current_user_email = ""

        # -------------------------------------------------
        # KEMBALI KE LOGIN
        # -------------------------------------------------

        self.root.current = (
            "login"
        )

        try:

            login = (
                self.root.get_screen(
                    "login"
                )
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