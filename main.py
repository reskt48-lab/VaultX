import base64
from io import BytesIO
import hashlib
import json
import re
import secrets
import string
import shutil
import uuid
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from kivy.app import App
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


# =========================================================
# CONFIG
# =========================================================

APP_DIR = Path.home() / ".vaultx"
VAULT_FILE = APP_DIR / "vault.json"
IMAGE_DIR = APP_DIR / "images"

PBKDF2_ITERATIONS = 600_000


# =========================================================
# CRYPTO
# =========================================================

def derive_key(password, salt, iterations=PBKDF2_ITERATIONS):

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations
    )

    key = kdf.derive(
        password.encode("utf-8")
    )

    return base64.urlsafe_b64encode(key)


# =========================================================
# PASSWORD VALIDATION
# =========================================================

def validate_password(password):

    errors = []

    if len(password) < 12:
        errors.append("Minimal 12 karakter")

    if not re.search(r"[A-Z]", password):
        errors.append("Harus memiliki huruf besar")

    if not re.search(r"[a-z]", password):
        errors.append("Harus memiliki huruf kecil")

    if not re.search(r"[0-9]", password):
        errors.append("Harus memiliki angka")

    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Harus memiliki simbol")

    return errors


def password_strength(password):

    score = 0

    if len(password) >= 12:
        score += 1

    if len(password) >= 16:
        score += 1

    if re.search(r"[A-Z]", password):
        score += 1

    if re.search(r"[a-z]", password):
        score += 1

    if re.search(r"[0-9]", password):
        score += 1

    if re.search(r"[^A-Za-z0-9]", password):
        score += 1

    if score <= 2:
        return "LEMAH"

    if score <= 4:
        return "SEDANG"

    return "KUAT"


def generate_password(length=20):

    chars = (
        string.ascii_letters
        + string.digits
        + "!@#$%^&*()-_=+"
    )

    return "".join(
        secrets.choice(chars)
        for _ in range(length)
    )


# =========================================================
# CUSTOM INPUT
# =========================================================

class VaultInput(TextInput):

    def __init__(
        self,
        hint="",
        password=False,
        multiline=False,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.hint_text = hint
        self.password = password
        self.multiline = multiline

        self.size_hint_y = None

        self.height = (
            dp(90)
            if multiline
            else dp(48)
        )

        self.padding = [
            dp(14),
            dp(12)
        ]

        self.background_normal = ""
        self.background_active = ""

        self.background_color = (
            0.08,
            0.09,
            0.12,
            1
        )

        self.foreground_color = (
            0.94,
            0.95,
            0.98,
            1
        )

        self.hint_text_color = (
            0.45,
            0.48,
            0.55,
            1
        )

        self.cursor_color = (
            0.3,
            0.6,
            1,
            1
        )


# =========================================================
# BUTTONS
# =========================================================

class PrimaryButton(Button):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.size_hint_y = None
        self.height = dp(48)

        self.background_normal = ""

        self.background_color = (
            0.16,
            0.43,
            0.82,
            1
        )

        self.color = (
            1,
            1,
            1,
            1
        )

        self.bold = True


class SecondaryButton(Button):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.size_hint_y = None
        self.height = dp(44)

        self.background_normal = ""

        self.background_color = (
            0.12,
            0.13,
            0.17,
            1
        )

        self.color = (
            0.85,
            0.87,
            0.92,
            1
        )


# =========================================================
# ACCOUNT IMAGE
# =========================================================

class AccountImageBox(FloatLayout):

    def __init__(self, app, entry, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.entry = entry
        self.size_hint = (None, None)
        self.size = (dp(72), dp(72))

        self.image = Image(
            size_hint=(1, 1),
            fit_mode="cover",
            opacity=0,
        )
        # Simpan referensi texture di widget ini sendiri.
        # Jadi texture akun lama tidak bergantung pada cache/path akun lain.
        self._texture_ref = None
        self.add_widget(self.image)

        self.button = Button(
            text="+" if not entry.get("image") else "",
            font_size=dp(28),
            bold=True,
            background_normal="",
            background_color=(0.08, 0.09, 0.12, 1) if not entry.get("image") else (0, 0, 0, 0),
            color=(0.85, 0.87, 0.92, 1),
            size_hint=(1, 1),
        )
        self.button.bind(on_release=lambda *_: app.open_image_picker(entry["id"]))
        self.add_widget(self.button)
        self.reload()

    def reload(self):
        # Setiap AccountImageBox memegang texture miliknya sendiri.
        # Foto diambil dari image_data (base64) sehingga tidak berbagi
        # source/path/cache dengan akun lain.
        try:
            data = str(self.entry.get("image_data", "") or "").strip()

            if data:
                raw = base64.b64decode(data, validate=True)
                image_ext = str(self.entry.get("image_ext", "") or "").lower()
                if image_ext not in {".png", ".jpg", ".jpeg", ".webp"}:
                    image_ext = ".png"

                # CoreImage dari BytesIO membuat texture mandiri untuk akun ini.
                stream = BytesIO(raw)
                texture = CoreImage(stream, ext=image_ext.lstrip(".")).texture

                # Simpan stream + texture agar keduanya tetap hidup.
                self._texture_stream = stream
                self._texture_ref = texture

                self.image.texture = texture
                self.image.opacity = 1
                self.button.text = ""
                self.button.background_color = (0, 0, 0, 0)
                return

            # Fallback untuk data lama yang belum punya image_data.
            path = self.app.get_image_path(self.entry)
            if path and path.is_file():
                raw = path.read_bytes()
                stream = BytesIO(raw)
                texture = CoreImage(
                    stream,
                    ext=path.suffix.lower().lstrip(".")
                ).texture

                self._texture_stream = stream
                self._texture_ref = texture
                self.image.texture = texture
                self.image.opacity = 1
                self.button.text = ""
                self.button.background_color = (0, 0, 0, 0)
                return

        except Exception as error:
            print("IMAGE LOAD ERROR:", repr(error))

        self._texture_stream = None
        self._texture_ref = None
        self.image.texture = None
        self.image.opacity = 0
        self.button.text = "+"
        self.button.background_color = (0.08, 0.09, 0.12, 1)


class AccountCard(BoxLayout):

    def __init__(self, app, entry, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.entry = entry
        self.orientation = "horizontal"
        self.spacing = dp(12)
        self.padding = dp(10)
        self.size_hint_y = None
        self.height = dp(92)

        # Keep the same image widget/card alive between refreshes.
        # This prevents an older account photo from disappearing when a new
        # account is added and the vault list is refreshed.
        self.image_box = AccountImageBox(app, entry)
        self.add_widget(self.image_box)

        info = BoxLayout(orientation="vertical", spacing=dp(2), padding=(0, dp(3)))
        self.website_label = app.make_label(
            entry.get("website", ""), 15, (0.92,0.94,0.98,1), 30, True
        )
        self.username_label = app.make_label(
            entry.get("username", ""), 12, (0.55,0.58,0.65,1), 26
        )
        info.add_widget(self.website_label)
        info.add_widget(self.username_label)
        self.add_widget(info)

        edit = SecondaryButton(text="EDIT", size_hint_x=None, width=dp(72))
        edit.bind(on_release=lambda *_: app.open_edit(entry["id"]))
        self.add_widget(edit)

    def refresh_from_entry(self, entry):
        self.entry = entry
        self.image_box.entry = entry
        self.website_label.text = str(entry.get("website", ""))
        self.username_label.text = str(entry.get("username", ""))
        self.image_box.reload()


# =========================================================
# SCREEN
# =========================================================

class VaultScreen(Screen):
    pass


# =========================================================
# MAIN APP
# =========================================================

class VaultX(App):

    def build(self):

        self.title = "VaultX"

        # Ukuran awal desktop, tetapi window tetap bebas di-resize.
        Window.size = (
            900,
            650
        )

        # Bisa diperkecil seperti tampilan HP.
        Window.minimum_width = 360
        Window.minimum_height = 560

        Window.clearcolor = (
            0.035,
            0.04,
            0.055,
            1
        )

        # Layout di-refresh ketika ukuran window berubah.
        Window.bind(on_resize=self._on_window_resize)

        APP_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        IMAGE_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        self.key = None
        self.entries = []

        # Texture foto disimpan di masing-masing AccountImageBox.
        # Tidak ada cache texture global antar-akun.

        self.sm = ScreenManager(
            transition=NoTransition()
        )

        self.create_setup_screen()
        self.create_login_screen()
        self.create_vault_screen()
        self.create_add_screen()
        self.create_edit_screen()

        return self.sm

    # =====================================================
    # LABEL
    # =====================================================

    def make_label(
        self,
        text="",
        size=14,
        color=(0.85, 0.87, 0.92, 1),
        height=None,
        bold=False
    ):

        label = Label(
            text=text,
            font_size=dp(size),
            color=color,
            bold=bold,
            halign="left",
            valign="middle"
        )

        if height:

            label.size_hint_y = None
            label.height = dp(height)

        label.bind(
            size=lambda obj, value:
            setattr(
                obj,
                "text_size",
                (obj.width, None)
            )
        )

        return label

    # =====================================================
    # PAGE
    # =====================================================

    def page(self, title, subtitle):

        root = BoxLayout(
            orientation="vertical",
            padding=dp(30),
            spacing=dp(10)
        )

        root.add_widget(
            self.make_label(
                title,
                28,
                (0.3, 0.6, 1, 1),
                50,
                True
            )
        )

        root.add_widget(
            self.make_label(
                subtitle,
                12,
                (0.48, 0.51, 0.58, 1),
                28
            )
        )

        return root

    # =====================================================
    # SETUP
    # =====================================================

    def create_setup_screen(self):

        screen = VaultScreen(
            name="setup"
        )

        root = self.page(
            "VAULTX",
            "LOCAL PASSWORD MANAGER"
        )

        root.add_widget(
            self.make_label(
                "Create Master Password",
                17,
                height=35,
                bold=True
            )
        )

        self.setup_password = VaultInput(
            "Master Password",
            password=True
        )

        root.add_widget(
            self.setup_password
        )

        show_button = SecondaryButton(
            text="SHOW / HIDE PASSWORD"
        )

        show_button.bind(
            on_release=lambda x:
            self.toggle_password(
                self.setup_password
            )
        )

        root.add_widget(
            show_button
        )

        self.setup_confirm = VaultInput(
            "Confirm Master Password",
            password=True
        )

        root.add_widget(
            self.setup_confirm
        )

        check_button = PrimaryButton(
            text="CHECK PASSWORD"
        )

        check_button.bind(
            on_release=lambda x:
            self.check_password()
        )

        root.add_widget(
            check_button
        )

        self.setup_status = self.make_label(
            "Minimal 12 karakter, huruf besar, huruf kecil, angka, dan simbol.",
            12,
            (0.55, 0.58, 0.65, 1),
            110
        )

        root.add_widget(
            self.setup_status
        )

        create_button = PrimaryButton(
            text="CREATE VAULT"
        )

        create_button.bind(
            on_release=lambda x:
            self.create_vault()
        )

        root.add_widget(
            create_button
        )

        root.add_widget(
            self.make_label(
                "Vault disimpan secara lokal dan terenkripsi.",
                11,
                (0.4, 0.43, 0.5, 1),
                25
            )
        )

        screen.add_widget(root)

        self.sm.add_widget(screen)

    # =====================================================
    # CHECK PASSWORD
    # =====================================================

    def check_password(self):

        password = self.setup_password.text
        confirm = self.setup_confirm.text

        errors = validate_password(
            password
        )

        strength = (
            password_strength(password)
            if password
            else "BELUM DIISI"
        )

        if errors:

            self.setup_status.text = (
                f"Kekuatan: {strength}\n\n"
                +
                "\n".join(
                    "• " + error
                    for error in errors
                )
            )

            self.setup_status.color = (
                1,
                0.65,
                0.25,
                1
            )

            return

        if password != confirm:

            self.setup_status.text = (
                "Password kuat, tetapi "
                "konfirmasi password TIDAK SAMA."
            )

            self.setup_status.color = (
                1,
                0.35,
                0.35,
                1
            )

            return

        self.setup_status.text = (
            f"Password valid.\n"
            f"Kekuatan: {strength}\n"
            f"Password cocok."
        )

        self.setup_status.color = (
            0.3,
            0.9,
            0.45,
            1
        )

    # =====================================================
    # CREATE VAULT
    # =====================================================

    def create_vault(self):

        password = self.setup_password.text
        confirm = self.setup_confirm.text

        errors = validate_password(
            password
        )

        if errors:

            self.show_popup(
                "Password Tidak Valid",
                "\n".join(
                    "• " + error
                    for error in errors
                )
            )

            return

        if password != confirm:

            self.show_popup(
                "Password Tidak Sama",
                "Master password dan konfirmasi password harus sama."
            )

            return

        salt = secrets.token_bytes(
            16
        )

        self.key = derive_key(
            password,
            salt
        )

        self.entries = []
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        encrypted = Fernet(
            self.key
        ).encrypt(
            b"[]"
        )

        vault = {

            "version": 1,

            "iterations":
                PBKDF2_ITERATIONS,

            "salt":
                base64.b64encode(
                    salt
                ).decode("ascii"),

            "vault":
                encrypted.decode("ascii")

        }

        VAULT_FILE.write_text(
            json.dumps(
                vault,
                indent=4
            ),
            encoding="utf-8"
        )

        self.setup_password.text = ""
        self.setup_confirm.text = ""

        self.sm.current = "vault"

        self.refresh_entries()

    # =====================================================
    # LOGIN
    # =====================================================

    def create_login_screen(self):

        screen = VaultScreen(
            name="login"
        )

        root = self.page(
            "VAULTX",
            "UNLOCK YOUR VAULT"
        )

        root.add_widget(
            self.make_label(
                "Master Password",
                17,
                height=35,
                bold=True
            )
        )

        self.login_password = VaultInput(
            "Master Password",
            password=True
        )

        root.add_widget(
            self.login_password
        )

        show = SecondaryButton(
            text="SHOW / HIDE"
        )

        show.bind(
            on_release=lambda x:
            self.toggle_password(
                self.login_password
            )
        )

        root.add_widget(
            show
        )

        unlock = PrimaryButton(
            text="UNLOCK VAULT"
        )

        unlock.bind(
            on_release=lambda x:
            self.login()
        )

        root.add_widget(
            unlock
        )

        root.add_widget(
            Label()
        )

        screen.add_widget(root)

        self.sm.add_widget(screen)

    # =====================================================
    # LOGIN FUNCTION
    # =====================================================

    def login(self):

        password = self.login_password.text

        if not password:

            self.show_popup(
                "Password Kosong",
                "Masukkan master password."
            )

            return

        try:

            data = json.loads(
                VAULT_FILE.read_text(
                    encoding="utf-8"
                )
            )

            salt = base64.b64decode(
                data["salt"]
            )

            iterations = int(
                data.get(
                    "iterations",
                    PBKDF2_ITERATIONS
                )
            )

            key = derive_key(
                password,
                salt,
                iterations
            )

            decrypted = Fernet(
                key
            ).decrypt(
                data["vault"].encode(
                    "ascii"
                )
            )

            entries = json.loads(
                decrypted.decode(
                    "utf-8"
                )
            )

            if not isinstance(
                entries,
                list
            ):
                raise ValueError(
                    "Vault invalid"
                )

            self.key = key
            self.entries = entries

            migrated = False
            for entry in self.entries:
                self._normalize_entry(entry)
                if self._ensure_image_embedded(entry):
                    migrated = True

            if migrated:
                self.save_vault()

            self.login_password.text = ""

            self.sm.current = "vault"

            self.refresh_entries()

        except InvalidToken:

            self.show_popup(
                "Login Gagal",
                "Master password salah."
            )

        except Exception as error:

            print(
                "LOGIN ERROR:",
                repr(error)
            )

            self.show_popup(
                "Error",
                "Vault tidak dapat dibuka."
            )

    # =====================================================
    # VAULT
    # =====================================================

    def create_vault_screen(self):

        screen = VaultScreen(
            name="vault"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(10)
        )

        top = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(8)
        )

        top.add_widget(
            self.make_label(
                "MY VAULT",
                23,
                height=50,
                bold=True
            )
        )

        lock = SecondaryButton(
            text="LOCK",
            size_hint_x=None,
            width=dp(90)
        )

        lock.bind(
            on_release=lambda x:
            self.logout()
        )

        top.add_widget(lock)

        root.add_widget(top)

        self.search = VaultInput(
            "Search website or username..."
        )

        self.search.bind(
            text=self.refresh_entries
        )

        root.add_widget(
            self.search
        )

        self.count_label = self.make_label(
            "0 account(s)",
            12,
            (0.5, 0.52, 0.58, 1),
            25
        )

        root.add_widget(
            self.count_label
        )

        scroll = ScrollView()

        self.entry_list = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None
        )

        self.entry_list.bind(
            minimum_height=
            self.entry_list.setter(
                "height"
            )
        )

        scroll.add_widget(
            self.entry_list
        )

        root.add_widget(
            scroll
        )

        add = PrimaryButton(
            text="+ ADD PASSWORD"
        )

        add.bind(
            on_release=lambda x:
            self.open_add()
        )

        root.add_widget(
            add
        )

        screen.add_widget(root)

        self.sm.add_widget(screen)

    # =====================================================
    # REFRESH
    # =====================================================

    def refresh_entries(self, *args):

        if not hasattr(self, "entry_list"):
            return

        # IMPORTANT: do not recreate every AccountCard during refresh.
        # We keep one card per account and only detach/reattach the existing
        # widgets. Their Image/Texture objects therefore remain independent.
        if not hasattr(self, "_account_cards"):
            self._account_cards = {}

        query = self.search.text.lower().strip() if hasattr(self, "search") else ""
        results = []
        repaired_any = False
        current_ids = set()

        for entry in self.entries:
            self._normalize_entry(entry)
            entry_id = str(entry.get("id", ""))
            current_ids.add(entry_id)

            if self._repair_entry_image(entry):
                repaired_any = True
            if self._ensure_image_embedded(entry):
                repaired_any = True

            website = str(entry.get("website", ""))
            username = str(entry.get("username", ""))
            if query in website.lower() or query in username.lower():
                results.append(entry)

            card = self._account_cards.get(entry_id)
            if card is None:
                self._account_cards[entry_id] = AccountCard(self, entry)
            else:
                card.refresh_from_entry(entry)

        # Remove card references for accounts that were actually deleted.
        for entry_id in list(self._account_cards):
            if entry_id not in current_ids:
                self._account_cards.pop(entry_id, None)

        self.count_label.text = f"{len(results)} account(s)"

        # clear_widgets() only detaches widgets; it does not destroy them.
        # Reusing the same cards keeps old photos visible after adding accounts.
        self.entry_list.clear_widgets()
        for entry in results:
            entry_id = str(entry.get("id", ""))
            self.entry_list.add_widget(self._account_cards[entry_id])

        if repaired_any and self.key is not None:
            self.save_vault()

    # =====================================================
    # ADD
    # =====================================================

    def create_add_screen(self):

        screen = VaultScreen(
            name="add"
        )

        root = self.page(
            "ADD PASSWORD",
            "Add account baru"
        )

        self.add_website = VaultInput(
            "Website / Application"
        )

        self.add_username = VaultInput(
            "Username / Email"
        )

        self.add_password = VaultInput(
            "Password",
            password=True
        )

        self.add_note = VaultInput(
            "Notes",
            multiline=True
        )

        root.add_widget(
            self.add_website
        )

        root.add_widget(
            self.add_username
        )

        password_row = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )

        password_row.add_widget(
            self.add_password
        )

        show = SecondaryButton(
            text="SHOW",
            size_hint_x=None,
            width=dp(80)
        )

        show.bind(
            on_release=lambda x:
            self.toggle_password(
                self.add_password
            )
        )

        password_row.add_widget(show)

        root.add_widget(
            password_row
        )

        generate = SecondaryButton(
            text="GENERATE STRONG PASSWORD"
        )

        generate.bind(
            on_release=lambda x:
            self.generate_into(
                self.add_password
            )
        )

        root.add_widget(
            generate
        )

        root.add_widget(
            self.add_note
        )

        root.add_widget(
            Label()
        )

        save = PrimaryButton(
            text="SAVE PASSWORD"
        )

        save.bind(
            on_release=lambda x:
            self.add_account()
        )

        root.add_widget(
            save
        )

        cancel = SecondaryButton(
            text="CANCEL"
        )

        cancel.bind(
            on_release=lambda x:
            self.back_vault()
        )

        root.add_widget(
            cancel
        )

        screen.add_widget(root)

        self.sm.add_widget(screen)

    # =====================================================
    # OPEN ADD
    # =====================================================

    def open_add(self):

        self.add_website.text = ""
        self.add_username.text = ""
        self.add_password.text = ""
        self.add_note.text = ""

        self.sm.current = "add"

    # =====================================================
    # ADD ACCOUNT
    # =====================================================

    def add_account(self):

        website = (
            self.add_website.text.strip()
        )

        username = (
            self.add_username.text.strip()
        )

        password = (
            self.add_password.text
        )

        note = (
            self.add_note.text.strip()
        )

        if not website:

            self.show_popup(
                "Data Kurang",
                "Website wajib diisi."
            )

            return

        if not username:

            self.show_popup(
                "Data Kurang",
                "Username wajib diisi."
            )

            return

        if not password:

            self.show_popup(
                "Data Kurang",
                "Password wajib diisi."
            )

            return

        # Menambahkan akun hanya boleh menyentuh akun baru. Jangan memproses
        # ulang metadata atau foto akun lama di alur ini.
        new_entry = {

            "id":
                secrets.token_hex(8),

            "website":
                website,

            "username":
                username,

            "password":
                password,

            "note":
                note,

            "image":
                ""

        }

        self.entries.append(new_entry)

        # Jangan refresh daftar sebelum vault benar-benar tersimpan. Jika
        # gagal, batalkan perubahan di memori agar akun lama tetap utuh.
        if not self.save_vault():
            self.entries.pop()
            return

        self.back_vault()

    # =====================================================
    # EDIT SCREEN
    # =====================================================

    def create_edit_screen(self):

        screen = VaultScreen(
            name="edit"
        )

        screen.entry_id = ""

        root = self.page(
            "EDIT PASSWORD",
            "Edit akun"
        )

        self.edit_website = VaultInput(
            "Website / Application"
        )

        self.edit_username = VaultInput(
            "Username / Email"
        )

        self.edit_password = VaultInput(
            "Password",
            password=True
        )

        self.edit_note = VaultInput(
            "Notes",
            multiline=True
        )

        root.add_widget(
            self.edit_website
        )

        root.add_widget(
            self.edit_username
        )

        password_row = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )

        password_row.add_widget(
            self.edit_password
        )

        show = SecondaryButton(
            text="SHOW",
            size_hint_x=None,
            width=dp(80)
        )

        show.bind(
            on_release=lambda x:
            self.toggle_password(
                self.edit_password
            )
        )

        password_row.add_widget(
            show
        )

        root.add_widget(
            password_row
        )

        generate = SecondaryButton(
            text="GENERATE STRONG PASSWORD"
        )

        generate.bind(
            on_release=lambda x:
            self.generate_into(
                self.edit_password
            )
        )

        root.add_widget(
            generate
        )

        root.add_widget(
            self.edit_note
        )

        root.add_widget(
            Label()
        )

        update = PrimaryButton(
            text="UPDATE PASSWORD"
        )

        update.bind(
            on_release=lambda x:
            self.update_account()
        )

        root.add_widget(
            update
        )

        delete = Button(
            text="DELETE PASSWORD",
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=(
                0.65,
                0.15,
                0.15,
                1
            )
        )

        delete.bind(
            on_release=lambda x:
            self.confirm_delete()
        )

        root.add_widget(
            delete
        )

        cancel = SecondaryButton(
            text="CANCEL"
        )

        cancel.bind(
            on_release=lambda x:
            self.back_vault()
        )

        root.add_widget(
            cancel
        )

        screen.add_widget(root)

        self.sm.add_widget(screen)

    # =====================================================
    # OPEN EDIT
    # =====================================================

    def open_edit(self, entry_id):

        entry = next(
            (
                item
                for item in self.entries
                if item["id"] == entry_id
            ),
            None
        )

        if not entry:
            return

        self.sm.get_screen(
            "edit"
        ).entry_id = entry_id

        self.edit_website.text = (
            entry["website"]
        )

        self.edit_username.text = (
            entry["username"]
        )

        self.edit_password.text = (
            entry["password"]
        )

        self.edit_note.text = (
            entry.get(
                "note",
                ""
            )
        )

        self.sm.current = "edit"

    # =====================================================
    # UPDATE
    # =====================================================

    def update_account(self):

        entry_id = self.sm.get_screen(
            "edit"
        ).entry_id

        website = (
            self.edit_website.text.strip()
        )

        username = (
            self.edit_username.text.strip()
        )

        password = (
            self.edit_password.text
        )

        note = (
            self.edit_note.text.strip()
        )

        if not website or not username or not password:

            self.show_popup(
                "Data Kurang",
                "Website, username, dan password wajib diisi."
            )

            return

        for entry in self.entries:

            if entry["id"] == entry_id:

                entry["website"] = website
                entry["username"] = username
                entry["password"] = password
                entry["note"] = note

                break

        if self.save_vault():
            self.back_vault()

    # =====================================================
    # DELETE
    # =====================================================

    def confirm_delete(self):

        entry_id = self.sm.get_screen(
            "edit"
        ).entry_id

        box = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12)
        )

        box.add_widget(
            self.make_label(
                "Yakin ingin menghapus akun ini?",
                13,
                height=70
            )
        )

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(45),
            spacing=dp(8)
        )

        cancel = SecondaryButton(
            text="BATAL"
        )

        delete = Button(
            text="HAPUS",
            background_normal="",
            background_color=(
                0.65,
                0.15,
                0.15,
                1
            )
        )

        buttons.add_widget(cancel)
        buttons.add_widget(delete)

        box.add_widget(buttons)

        popup = Popup(
            title="Konfirmasi",
            content=box,
            size_hint=(0.7, 0.3),
            auto_dismiss=False
        )

        cancel.bind(
            on_release=popup.dismiss
        )

        delete.bind(
            on_release=lambda x:
            self.delete_account(
                entry_id,
                popup
            )
        )

        popup.open()

    def delete_account(
        self,
        entry_id,
        popup
    ):

        self.entries = [

            entry

            for entry in self.entries

            if entry["id"] != entry_id

        ]

        self.save_vault()

        popup.dismiss()

        self.back_vault()

    # =====================================================
    # SAVE
    # =====================================================

    def _normalize_entry(self, entry):
        if not isinstance(entry, dict):
            return
        entry.setdefault("id", secrets.token_hex(8))
        entry.setdefault("website", "")
        entry.setdefault("username", "")
        entry.setdefault("password", "")
        entry.setdefault("note", "")
        entry.setdefault("image", "")
        entry.setdefault("image_data", "")
        entry.setdefault("image_ext", "")

    def _repair_entry_image(self, entry):
        """Recover image references used by old VaultX versions.

        IMPORTANT: this function never deletes an image. It only finds an
        existing file and updates the entry's reference when necessary.
        """
        if not isinstance(entry, dict):
            return False

        image_value = str(entry.get("image", "") or "").strip()
        candidates = []
        extensions = {".png", ".jpg", ".jpeg", ".webp"}
        entry_id = str(entry.get("id", "")).strip()

        # 1. The reference stored in the vault, if it still points to a file.
        if image_value:
            try:
                raw_path = Path(image_value)
                if raw_path.is_absolute() and raw_path.is_file():
                    candidates.append(raw_path)
            except Exception:
                pass

            try:
                relative_candidate = (APP_DIR / image_value).resolve()
                if relative_candidate.is_file() and relative_candidate.suffix.lower() in extensions:
                    candidates.append(relative_candidate)
            except Exception:
                pass

        # 2. Legacy filenames: <id>.jpg and <id>_<anything>.jpg.
        #    This also works when the old entry had no "image" field.
        if entry_id:
            try:
                IMAGE_DIR.mkdir(parents=True, exist_ok=True)
                for ext in extensions:
                    exact = IMAGE_DIR / f"{entry_id}{ext}"
                    if exact.is_file():
                        candidates.append(exact)
                for candidate in IMAGE_DIR.glob(f"{entry_id}_*"):
                    if candidate.is_file() and candidate.suffix.lower() in extensions:
                        candidates.append(candidate)
            except Exception:
                pass

            # Some old builds stored images directly in .vaultx.
            try:
                for ext in extensions:
                    legacy = APP_DIR / f"{entry_id}{ext}"
                    if legacy.is_file():
                        candidates.append(legacy)
            except Exception:
                pass

        # Deduplicate candidates.
        unique = []
        seen = set()
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
                key = str(resolved).lower()
            except Exception:
                resolved = candidate
                key = str(candidate).lower()
            if key not in seen:
                seen.add(key)
                unique.append(resolved)

        if not unique:
            return False

        source = unique[0]
        try:
            root = APP_DIR.resolve()
            image_root = IMAGE_DIR.resolve()

            # Never accept an image outside the VaultX directory.
            if source != root and root not in source.parents:
                return False

            # If already managed by VaultX, only fix the reference.
            if source.parent == image_root:
                new_value = str(source.relative_to(root)).replace("\\", "/")
                if image_value != new_value:
                    entry["image"] = new_value
                    return True
                return False

            # Legacy image elsewhere inside .vaultx: copy it into images.
            destination = IMAGE_DIR / f"{entry_id}_{uuid.uuid4().hex}{source.suffix.lower()}"
            shutil.copy2(source, destination)
            entry["image"] = str(destination.relative_to(root)).replace("\\", "/")
            return True
        except Exception as error:
            print("IMAGE REPAIR ERROR:", repr(error))
            return False


    def _image_cache_path(self, entry):
        entry_id = str(entry.get("id", "")).strip()
        ext = str(entry.get("image_ext", "") or "").lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
            ext = ".png"
        return IMAGE_DIR / f"{entry_id}_embedded{ext}"

    def _embed_image_from_file(self, entry, path):
        try:
            if not path or not path.is_file():
                return False
            ext = path.suffix.lower()
            if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
                return False
            entry["image_data"] = base64.b64encode(path.read_bytes()).decode("ascii")
            entry["image_ext"] = ext
            return True
        except Exception as error:
            print("IMAGE EMBED ERROR:", repr(error))
            return False

    def _materialize_embedded_image(self, entry):
        """Create/use a stable local image copy from the encrypted image bytes.

        The embedded bytes are the source of truth. This avoids stale or broken
        paths from older versions and prevents Kivy refreshes from losing an
        existing account image.
        """
        data = str(entry.get("image_data", "") or "").strip()
        if not data:
            return None
        try:
            IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            raw = base64.b64decode(data, validate=True)
            ext = str(entry.get("image_ext", "") or "").lower()
            if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
                ext = ".png"

            # Use a content-derived filename. If the same account is refreshed,
            # Kivy gets the exact same valid file; if the photo is replaced, the
            # bytes change and therefore the cache filename changes too.
            digest = hashlib.sha256(raw).hexdigest()[:20]
            destination = IMAGE_DIR / f"{entry.get('id', 'image')}_cache_{digest}{ext}"

            if not destination.is_file() or destination.stat().st_size != len(raw):
                destination.write_bytes(raw)

            return destination if destination.is_file() else None
        except Exception as error:
            print("IMAGE MATERIALIZE ERROR:", repr(error))
            return None

    def _ensure_image_embedded(self, entry):
        # The encrypted vault keeps the actual image bytes. This prevents an
        # ADD ACCOUNT / refresh from ever losing an existing account photo.
        if str(entry.get("image_data", "") or "").strip():
            return False
        path = self._path_from_entry_image(entry)
        if path and path.is_file():
            return self._embed_image_from_file(entry, path)
        return False

    def _path_from_entry_image(self, entry):
        relative = str(entry.get("image", "") or "").strip()
        if not relative:
            return None
        try:
            root = APP_DIR.resolve()
            raw = Path(relative)
            path = raw.resolve() if raw.is_absolute() else (APP_DIR / raw).resolve()
            if path != root and root not in path.parents:
                return None
            return path if path.is_file() else None
        except Exception:
            return None

    def get_image_texture(self, entry, path):
        """Load texture from the file bytes without sharing Kivy file-cache state."""
        if not path or not path.is_file():
            return None

        try:
            raw = path.read_bytes()
            stream = BytesIO(raw)
            return CoreImage(
                stream,
                ext=path.suffix.lower().lstrip(".")
            ).texture
        except Exception as error:
            print("IMAGE TEXTURE ERROR:", repr(error))
            return None

    def get_image_path(self, entry):
        # IMPORTANT: once image_data exists, ALWAYS render from the encrypted
        # copy. Never prefer the legacy/path-based image because that path can
        # become stale after an account is added or the card list is rebuilt.
        embedded = self._materialize_embedded_image(entry)
        if embedded:
            return embedded

        # Legacy account: recover the old file only when no embedded copy exists.
        path = self._path_from_entry_image(entry)
        if path:
            if self._embed_image_from_file(entry, path):
                embedded = self._materialize_embedded_image(entry)
                if embedded:
                    return embedded
            return path
        return None

    def _pick_image_file(self):
        root = None
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            selected = filedialog.askopenfilename(
                title="Pilih Foto Akun",
                filetypes=[("Gambar", "*.png *.jpg *.jpeg *.webp"), ("Semua File", "*.*")]
            )
            return Path(selected) if selected else None
        except Exception as error:
            print("FILE PICKER ERROR:", repr(error))
            return None
        finally:
            if root is not None:
                try: root.destroy()
                except Exception: pass

    def open_image_picker(self, entry_id):
        entry = next((e for e in self.entries if e.get("id") == entry_id), None)
        if not entry:
            return

        box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        box.add_widget(self.make_label("Pilih tindakan foto akun.", 13, height=45))
        choose = PrimaryButton(text="PILIH / GANTI FOTO")
        remove = SecondaryButton(text="HAPUS FOTO")
        remove.disabled = self.get_image_path(entry) is None
        cancel = SecondaryButton(text="BATAL")
        box.add_widget(choose); box.add_widget(remove); box.add_widget(cancel)

        popup = Popup(title="Foto Akun", content=box, size_hint=(0.68,0.42), auto_dismiss=False)
        cancel.bind(on_release=popup.dismiss)
        choose.bind(on_release=lambda *_: self._choose_from_popup(popup, entry_id))
        remove.bind(on_release=lambda *_: self._remove_from_popup(popup, entry_id))
        popup.open()

    def _choose_from_popup(self, popup, entry_id):
        popup.dismiss()
        source = self._pick_image_file()
        if source is None:
            return
        entry = next((e for e in self.entries if e.get("id") == entry_id), None)
        if entry:
            self.select_local_image_path(entry, source)

    def _remove_from_popup(self, popup, entry_id):
        popup.dismiss()
        self.confirm_remove_account_image(entry_id)

    def select_local_image_path(self, entry, source):
        if source.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            self.show_popup("Format Tidak Didukung", "Gunakan PNG, JPG, JPEG, atau WEBP.")
            return
        try:
            IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            destination = IMAGE_DIR / f"{entry['id']}_{uuid.uuid4().hex}{source.suffix.lower()}"
            shutil.copy2(source, destination)

            # Foto lama tidak dihapus di sini. Foto lama hanya milik akun ini,
            # sedangkan foto akun lain sama sekali tidak disentuh.
            entry["image"] = str(destination.relative_to(APP_DIR)).replace("\\", "/")
            # Store the actual image bytes inside the encrypted vault too.
            self._embed_image_from_file(entry, destination)
            if self.save_vault():
                self.refresh_entries()
        except Exception as error:
            print("IMAGE COPY ERROR:", repr(error))
            self.show_popup("Gagal", "Foto tidak dapat disimpan.")

    def confirm_remove_account_image(self, entry_id):
        entry = next((e for e in self.entries if e.get("id") == entry_id), None)
        if not entry or not self.get_image_path(entry):
            return
        box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        box.add_widget(self.make_label("Yakin ingin menghapus foto ini?", 14, height=55))
        buttons = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(44))
        no = SecondaryButton(text="TIDAK"); yes = PrimaryButton(text="YA")
        buttons.add_widget(no); buttons.add_widget(yes); box.add_widget(buttons)
        popup = Popup(title="Konfirmasi", content=box, size_hint=(0.65,0.3), auto_dismiss=False)
        no.bind(on_release=popup.dismiss)
        yes.bind(on_release=lambda *_: self._delete_image_confirmed(entry_id, popup))
        popup.open()

    def _delete_image_confirmed(self, entry_id, popup):
        popup.dismiss()
        entry = next((e for e in self.entries if e.get("id") == entry_id), None)
        if not entry:
            return
        path = self.get_image_path(entry)
        if path and path.is_file():
            try: path.unlink()
            except OSError as error:
                print("IMAGE DELETE ERROR:", repr(error))
                self.show_popup("Gagal", "Foto sedang digunakan atau tidak dapat dihapus.")
                return
        entry["image"] = ""
        entry["image_data"] = ""
        entry["image_ext"] = ""

        if self.save_vault():
            self.refresh_entries()

    def save_vault(self):

        if self.key is None:
            return False

        try:
            if not VAULT_FILE.exists():
                return False

            data = json.loads(VAULT_FILE.read_text(encoding="utf-8"))

            # Simpan salinan metadata gambar apa adanya. save_vault TIDAK
            # boleh menghapus, mengganti nama, atau memindahkan foto akun.
            for entry in self.entries:
                self._normalize_entry(entry)

            encrypted = Fernet(self.key).encrypt(
                json.dumps(self.entries, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            ).decode("ascii")
            data["vault"] = encrypted

            temp = VAULT_FILE.with_suffix(".tmp")
            temp.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
            os.replace(temp, VAULT_FILE)
            return True

        except Exception as error:
            print("SAVE VAULT ERROR:", repr(error))
            try:
                temp = VAULT_FILE.with_suffix(".tmp")
                if temp.exists(): temp.unlink()
            except Exception: pass
            self.show_popup("Gagal Menyimpan", "Perubahan tidak tersimpan. Vault lama tetap dipertahankan.")
            return False

    # =====================================================
    # UTILITIES
    # =====================================================

    def toggle_password(self, field):

        field.password = (
            not field.password
        )

    def generate_into(self, field):

        field.text = generate_password()

    def back_vault(self):

        self.sm.current = "vault"

        self.refresh_entries()

    def logout(self):

        self.key = None

        self.entries = []

        self.login_password.text = ""

        self.sm.current = "login"

    # =====================================================
    # POPUP
    # =====================================================

    def show_popup(
        self,
        title,
        message
    ):

        box = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12)
        )

        label = self.make_label(
            message,
            13,
            height=120
        )

        box.add_widget(
            label
        )

        ok = PrimaryButton(
            text="OK"
        )

        box.add_widget(
            ok
        )

        popup = Popup(
            title=title,
            content=box,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )

        ok.bind(
            on_release=popup.dismiss
        )

        popup.open()

    # =====================================================
    # RESPONSIVE WINDOW
    # =====================================================

    def _on_window_resize(self, window, width, height):
        if hasattr(self, "entry_list"):
            try:
                self.entry_list.do_layout()
            except Exception:
                pass

    # =====================================================
    # START
    # =====================================================

    def on_start(self):

        if VAULT_FILE.exists():

            self.sm.current = "login"

        else:

            self.sm.current = "setup"


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    VaultX().run()