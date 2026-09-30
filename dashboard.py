import os
import uuid
import mimetypes
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from supabase_client import supabase
from crypto_utils import encrypt_text, decrypt_text


BUCKET_NAME = "vault-images"


# =========================================================
# SUPABASE RESPONSE HELPERS
# =========================================================

def get_response_data(response):
    if response is None:
        return None

    if isinstance(response, dict):
        return response.get("data", response)

    data = getattr(response, "data", None)

    if data is not None:
        return data

    return None


def get_signed_url(image_path):
    if not image_path:
        return ""

    try:
        response = (
            supabase
            .storage
            .from_(BUCKET_NAME)
            .create_signed_url(image_path, 3600)
        )

        print("SIGNED URL RESPONSE:", repr(response))

        # Beberapa versi supabase-py
        for attr in ("signed_url", "signedURL", "signedUrl"):
            value = getattr(response, attr, None)
            if value:
                return value

        # Response berupa dictionary
        if isinstance(response, dict):
            for key in ("signed_url", "signedURL", "signedUrl"):
                value = response.get(key)
                if value:
                    return value

            data = response.get("data")

            if isinstance(data, dict):
                for key in ("signed_url", "signedURL", "signedUrl"):
                    value = data.get(key)
                    if value:
                        return value

        # Response punya .data
        data = getattr(response, "data", None)

        if isinstance(data, dict):
            for key in ("signed_url", "signedURL", "signedUrl"):
                value = data.get(key)
                if value:
                    return value

        return ""

    except Exception as e:
        print("SIGNED URL ERROR:", repr(e))
        return ""


# =========================================================
# PASSWORD CARD
# =========================================================

class PasswordCard(BoxLayout):

    website = StringProperty("")
    username = StringProperty("")
    password = StringProperty("")
    notes = StringProperty("")
    image_source = StringProperty("")

    favorite = BooleanProperty(False)
    password_visible = BooleanProperty(False)

    account_data = ObjectProperty(None)
    dashboard = ObjectProperty(None)

    def toggle_password(self):
        self.password_visible = not self.password_visible

    def toggle_favorite(self):
        if self.dashboard and self.account_data:
            self.dashboard.toggle_favorite(self.account_data)

    def edit_account(self):
        if self.dashboard and self.account_data:
            self.dashboard.edit_account(self.account_data)

    def delete_account(self):
        if self.dashboard and self.account_data:
            self.dashboard.confirm_delete(self.account_data)


# =========================================================
# ADD / EDIT PASSWORD FORM
# =========================================================

class AddPasswordForm(BoxLayout):

    dashboard = ObjectProperty(None)

    editing_account = ObjectProperty(
        None,
        allownone=True
    )

    selected_photo = StringProperty("")
    selected_photo_path = StringProperty("")
    preview_source = StringProperty("")

    password_visible = BooleanProperty(False)
    photo_removed = BooleanProperty(False)

    def __init__(self, dashboard=None, editing_account=None, **kwargs):
        super().__init__(**kwargs)

        self.dashboard = dashboard
        self.editing_account = editing_account

        Clock.schedule_once(
            self._prepare_form,
            0.15
        )

    def _prepare_form(self, *_):
        if self.editing_account:
            self.load_account_data(self.editing_account)

    # -----------------------------------------------------
    # EDIT DATA
    # -----------------------------------------------------

    def load_account_data(self, account):

        self.editing_account = account

        self.ids.website.text = account.get("website", "")
        self.ids.username.text = account.get("username", "")

        self.ids.password.text = account.get(
            "_decrypted_password",
            ""
        )

        self.ids.notes.text = account.get(
            "_decrypted_notes",
            ""
        )

        self.password_visible = False
        self.photo_removed = False
        self.selected_photo_path = ""

        image_path = account.get(
            "image_path",
            ""
        ) or ""

        image_url = account.get(
            "_image_url",
            ""
        ) or ""

        if image_path:
            self.selected_photo = os.path.basename(
                image_path
            )

            self.preview_source = image_url
        else:
            self.selected_photo = ""
            self.preview_source = ""

    # -----------------------------------------------------
    # PASSWORD VISIBILITY
    # -----------------------------------------------------

    def toggle_password_visibility(self):
        self.password_visible = not self.password_visible

    # -----------------------------------------------------
    # CHOOSE PHOTO
    # -----------------------------------------------------

    def choose_photo(self):

        try:
            from plyer import filechooser

            filechooser.open_file(
                on_selection=self._photo_selected
            )

        except Exception as e:
            print(
                "FILE CHOOSER ERROR:",
                repr(e)
            )

            self.ids.form_status.text = (
                "Gagal membuka pemilih foto."
            )

    def _photo_selected(self, selection):

        if not selection:
            return

        try:
            path = selection[0]

            if not os.path.isfile(path):
                return

            self.selected_photo_path = path
            self.selected_photo = os.path.basename(path)

            # Local preview
            self.preview_source = path

            self.photo_removed = False

            self.ids.form_status.text = ""

        except Exception as e:
            print(
                "PHOTO SELECT ERROR:",
                repr(e)
            )

    # -----------------------------------------------------
    # REMOVE PHOTO
    # -----------------------------------------------------

    def remove_photo(self):

        self.selected_photo = ""
        self.selected_photo_path = ""
        self.preview_source = ""

        if self.editing_account:
            self.photo_removed = True

        self.ids.form_status.text = ""

    # -----------------------------------------------------
    # CANCEL
    # -----------------------------------------------------

    def cancel(self):

        if self.dashboard:
            self.dashboard.close_add_popup()

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    def save(self):

        if self.dashboard:
            self.dashboard.save_account(self)


# =========================================================
# DASHBOARD
# =========================================================

class DashboardScreen(Screen):

    search_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_popup = None
        self.delete_popup = None

        self.accounts = []

    # -----------------------------------------------------
    # CURRENT USER
    # -----------------------------------------------------

    def get_current_user(self):

        response = supabase.auth.get_user()

        user = getattr(
            response,
            "user",
            None
        )

        return user

    # -----------------------------------------------------
    # LOAD ACCOUNTS
    # -----------------------------------------------------

    def load_accounts(self, *_):

        try:
            user = self.get_current_user()

            if not user:
                print("LOAD ACCOUNTS: USER TIDAK ADA")
                return

            app = App.get_running_app()

            if not getattr(app, "crypto_key", None):
                print(
                    "LOAD ACCOUNTS: CRYPTO KEY BELUM ADA"
                )
                return

            response = (
                supabase
                .table("passwords")
                .select("*")
                .eq("user_id", user.id)
                .order(
                    "created_at",
                    desc=True
                )
                .execute()
            )

            accounts = get_response_data(response)

            if accounts is None:
                accounts = []

            if not isinstance(accounts, list):
                accounts = []

            self.accounts = []

            for account in accounts:

                # -------------------------------
                # DECRYPT PASSWORD
                # -------------------------------

                encrypted_password = account.get(
                    "password_ciphertext",
                    ""
                )

                encrypted_notes = account.get(
                    "notes_ciphertext",
                    ""
                )

                try:
                    account["_decrypted_password"] = (
                        decrypt_text(
                            encrypted_password,
                            app.crypto_key
                        )
                        if encrypted_password
                        else ""
                    )

                    account["_decrypted_notes"] = (
                        decrypt_text(
                            encrypted_notes,
                            app.crypto_key
                        )
                        if encrypted_notes
                        else ""
                    )

                except Exception as e:

                    print(
                        "DECRYPT ERROR:",
                        repr(e)
                    )

                    account["_decrypted_password"] = ""
                    account["_decrypted_notes"] = ""

                # -------------------------------
                # PHOTO
                # -------------------------------

                image_path = account.get(
                    "image_path",
                    ""
                ) or ""

                account["_image_url"] = ""

                if image_path:
                    try:
                        account["_image_url"] = (
                            get_signed_url(image_path)
                        )
                    except Exception as e:
                        print(
                            "IMAGE URL ERROR:",
                            repr(e)
                        )

                self.accounts.append(account)

            self.refresh_cards()

            print(
                "LOAD ACCOUNTS OK:",
                len(self.accounts)
            )

        except Exception as e:

            print(
                "LOAD ACCOUNTS ERROR:",
                repr(e)
            )

            traceback.print_exc()

    # -----------------------------------------------------
    # REFRESH CARD
    # -----------------------------------------------------

    def refresh_cards(self, accounts=None):

        if accounts is None:
            accounts = self.accounts

        container = self.ids.account_list
        container.clear_widgets()

        for account in accounts:

            card = PasswordCard(
                website=account.get(
                    "website",
                    ""
                ),

                username=account.get(
                    "username",
                    ""
                ),

                password=account.get(
                    "_decrypted_password",
                    ""
                ),

                notes=account.get(
                    "_decrypted_notes",
                    ""
                ),

                image_source=account.get(
                    "_image_url",
                    ""
                ),

                favorite=bool(
                    account.get(
                        "is_favorite",
                        False
                    )
                ),

                account_data=account,
                dashboard=self
            )

            container.add_widget(card)

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    def search_accounts(self, text):

        self.search_text = text

        query = (
            text or ""
        ).strip().lower()

        if not query:
            self.refresh_cards()
            return

        filtered = []

        for account in self.accounts:

            website = str(
                account.get(
                    "website",
                    ""
                )
            ).lower()

            username = str(
                account.get(
                    "username",
                    ""
                )
            ).lower()

            if (
                query in website
                or query in username
            ):
                filtered.append(account)

        self.refresh_cards(filtered)

    # -----------------------------------------------------
    # ADD PASSWORD
    # -----------------------------------------------------

    def add_password(self):

        form = AddPasswordForm(
            dashboard=self
        )

        self.add_popup = Popup(
            title="Add Password",
            content=form,
            size_hint=(0.92, 0.90),
            auto_dismiss=False
        )

        self.add_popup.open()

    # -----------------------------------------------------
    # EDIT PASSWORD
    # -----------------------------------------------------

    def edit_account(self, account):

        form = AddPasswordForm(
            dashboard=self,
            editing_account=account
        )

        self.add_popup = Popup(
            title="Edit Password",
            content=form,
            size_hint=(0.92, 0.90),
            auto_dismiss=False
        )

        self.add_popup.open()

        Clock.schedule_once(
            lambda *_: form.load_account_data(account),
            0.2
        )

    # -----------------------------------------------------
    # CLOSE POPUP
    # -----------------------------------------------------

    def close_add_popup(self):

        if self.add_popup:
            self.add_popup.dismiss()
            self.add_popup = None

    # -----------------------------------------------------
    # SAVE ACCOUNT
    # -----------------------------------------------------

    def save_account(self, form):

        try:

            app = App.get_running_app()

            if not getattr(
                app,
                "crypto_key",
                None
            ):
                form.ids.form_status.text = (
                    "Encryption key belum tersedia."
                )
                return

            website = self.ids_value(
                form,
                "website"
            )

            username = self.ids_value(
                form,
                "username"
            )

            password = self.ids_value(
                form,
                "password"
            )

            notes = self.ids_value(
                form,
                "notes"
            )

            if not website:
                form.ids.form_status.text = (
                    "Website wajib diisi."
                )
                return

            if not username:
                form.ids.form_status.text = (
                    "Username wajib diisi."
                )
                return

            if not password:
                form.ids.form_status.text = (
                    "Password wajib diisi."
                )
                return

            user = self.get_current_user()

            if not user:
                form.ids.form_status.text = (
                    "Session login tidak ditemukan."
                )
                return

            encrypted_password = encrypt_text(
                password,
                app.crypto_key
            )

            encrypted_notes = encrypt_text(
                notes,
                app.crypto_key
            )

            old_image_path = ""

            if form.editing_account:
                old_image_path = (
                    form.editing_account.get(
                        "image_path",
                        ""
                    ) or ""
                )

            new_image_path = old_image_path

            # =================================================
            # REMOVE PHOTO
            # =================================================

            if form.photo_removed:

                if old_image_path:
                    self.delete_photo(
                        old_image_path
                    )

                new_image_path = ""

            # =================================================
            # UPLOAD NEW PHOTO
            # =================================================

            if form.selected_photo_path:

                uploaded_path = (
                    self.upload_photo(
                        form.selected_photo_path,
                        user.id
                    )
                )

                if not uploaded_path:
                    form.ids.form_status.text = (
                        "Foto gagal diupload."
                    )
                    return

                new_image_path = uploaded_path

            # =================================================
            # UPDATE
            # =================================================

            if form.editing_account:

                account_id = form.editing_account.get(
                    "id"
                )

                payload = {
                    "website": website,
                    "username": username,
                    "password_ciphertext": encrypted_password,
                    "notes_ciphertext": encrypted_notes,
                    "image_path": new_image_path,
                    "is_favorite": bool(
                        form.editing_account.get(
                            "is_favorite",
                            False
                        )
                    )
                }

                (
                    supabase
                    .table("passwords")
                    .update(payload)
                    .eq("id", account_id)
                    .eq("user_id", user.id)
                    .execute()
                )

            # =================================================
            # INSERT
            # =================================================

            else:

                payload = {
                    "user_id": user.id,
                    "website": website,
                    "username": username,
                    "password_ciphertext": encrypted_password,
                    "notes_ciphertext": encrypted_notes,
                    "image_path": new_image_path,
                    "is_favorite": False
                }

                (
                    supabase
                    .table("passwords")
                    .insert(payload)
                    .execute()
                )

            form.ids.form_status.text = (
                "Berhasil disimpan."
            )

            Clock.schedule_once(
                lambda *_: self._after_save(),
                0.25
            )

        except Exception as e:

            print(
                "SAVE ACCOUNT ERROR:",
                repr(e)
            )

            traceback.print_exc()

            if "form_status" in form.ids:
                form.ids.form_status.text = (
                    "Gagal menyimpan: "
                    + str(e)
                )

    def ids_value(self, form, name):

        widget = form.ids.get(name)

        if widget is None:
            return ""

        return widget.text.strip()

    def _after_save(self):

        self.close_add_popup()
        self.load_accounts()

    # -----------------------------------------------------
    # UPLOAD PHOTO
    # -----------------------------------------------------

    def upload_photo(self, local_path, user_id):

        if not local_path:
            return ""

        if not os.path.isfile(local_path):
            return ""

        try:

            original_name = os.path.basename(
                local_path
            )

            extension = os.path.splitext(
                original_name
            )[1].lower()

            if not extension:
                extension = ".jpg"

            filename = (
                uuid.uuid4().hex
                + extension
            )

            storage_path = (
                f"{user_id}/{filename}"
            )

            content_type = (
                mimetypes.guess_type(
                    local_path
                )[0]
                or "application/octet-stream"
            )

            with open(
                local_path,
                "rb"
            ) as file:

                (
                    supabase
                    .storage
                    .from_(BUCKET_NAME)
                    .upload(
                        storage_path,
                        file,
                        file_options={
                            "content-type": content_type,
                            "upsert": "false"
                        }
                    )
                )

            print(
                "PHOTO UPLOAD OK:",
                storage_path
            )

            return storage_path

        except Exception as e:

            print(
                "PHOTO UPLOAD ERROR:",
                repr(e)
            )

            traceback.print_exc()

            return ""

    # -----------------------------------------------------
    # DELETE PHOTO
    # -----------------------------------------------------

    def delete_photo(self, image_path):

        if not image_path:
            return

        try:

            (
                supabase
                .storage
                .from_(BUCKET_NAME)
                .remove([
                    image_path
                ])
            )

        except Exception as e:

            print(
                "PHOTO DELETE ERROR:",
                repr(e)
            )

    # -----------------------------------------------------
    # FAVORITE
    # -----------------------------------------------------

    def toggle_favorite(self, account):

        try:

            user = self.get_current_user()

            if not user:
                return

            current_value = bool(
                account.get(
                    "is_favorite",
                    False
                )
            )

            new_value = not current_value

            (
                supabase
                .table("passwords")
                .update({
                    "is_favorite": new_value
                })
                .eq(
                    "id",
                    account.get("id")
                )
                .eq(
                    "user_id",
                    user.id
                )
                .execute()
            )

            account["is_favorite"] = new_value

            self.refresh_cards()

        except Exception as e:

            print(
                "FAVORITE ERROR:",
                repr(e)
            )

    # -----------------------------------------------------
    # DELETE CONFIRM
    # -----------------------------------------------------

    def confirm_delete(self, account):

        box = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=15
        )

        from kivy.uix.label import Label
        from kivy.uix.button import Button

        box.add_widget(
            Label(
                text=(
                    "Hapus password untuk\n"
                    f"{account.get('website', '')}?"
                )
            )
        )

        buttons = BoxLayout(
            size_hint_y=None,
            height=50,
            spacing=10
        )

        cancel = Button(
            text="CANCEL"
        )

        delete = Button(
            text="DELETE"
        )

        buttons.add_widget(cancel)
        buttons.add_widget(delete)

        box.add_widget(buttons)

        popup = Popup(
            title="Delete Password",
            content=box,
            size_hint=(0.8, 0.35),
            auto_dismiss=False
        )

        cancel.bind(
            on_release=lambda *_: popup.dismiss()
        )

        delete.bind(
            on_release=lambda *_: (
                popup.dismiss(),
                self.delete_account(account)
            )
        )

        self.delete_popup = popup
        popup.open()

    # -----------------------------------------------------
    # DELETE ACCOUNT
    # -----------------------------------------------------

    def delete_account(self, account):

        try:

            user = self.get_current_user()

            if not user:
                return

            image_path = account.get(
                "image_path",
                ""
            ) or ""

            if image_path:
                self.delete_photo(
                    image_path
                )

            (
                supabase
                .table("passwords")
                .delete()
                .eq(
                    "id",
                    account.get("id")
                )
                .eq(
                    "user_id",
                    user.id
                )
                .execute()
            )

            self.load_accounts()

        except Exception as e:

            print(
                "DELETE ACCOUNT ERROR:",
                repr(e)
            )

    # -----------------------------------------------------
    # LOGOUT
    # -----------------------------------------------------

    def logout(self):

        try:
            supabase.auth.sign_out()
        except Exception as e:
            print(
                "LOGOUT ERROR:",
                repr(e)
            )

        app = App.get_running_app()

        app.crypto_key = None

        self.search_text = ""

        app.root.current = "login"

        Clock.schedule_once(
            lambda *_: self._clear_login_fields(),
            0.1
        )

    def _clear_login_fields(self):

        try:
            login = App.get_running_app().root.get_screen(
                "login"
            )

            if "login_password" in login.ids:
                login.ids.login_password.text = ""

        except Exception:
            pass