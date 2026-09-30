import base64
import hashlib
import json
import secrets
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


# =========================================================
# VAULTX LOCAL DIRECTORY
# =========================================================

APP_DIR = Path.home() / ".vaultx"
KEY_FILE = APP_DIR / "vault_keys.json"
SESSION_FILE = APP_DIR / "session.json"

APP_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# PASSWORD -> KEY
# Dipertahankan untuk kompatibilitas dengan kode lama.
# =========================================================

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Menghasilkan Fernet key dari password + salt.
    """

    if not isinstance(password, str):
        password = str(password)

    if not isinstance(salt, bytes):
        raise TypeError("salt harus berupa bytes")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )

    return base64.urlsafe_b64encode(
        kdf.derive(password.encode("utf-8"))
    )


# =========================================================
# ENCRYPT / DECRYPT
# =========================================================

def encrypt_text(text: str, key: bytes) -> str:
    """
    Mengenkripsi text menggunakan Fernet.
    """

    if not text:
        return ""

    if not key:
        raise ValueError("Encryption key belum tersedia.")

    cipher = Fernet(key)

    encrypted = cipher.encrypt(
        text.encode("utf-8")
    )

    return encrypted.decode("utf-8")


def decrypt_text(text: str, key: bytes) -> str:
    """
    Mendekripsi text menggunakan Fernet.
    """

    if not text:
        return ""

    if not key:
        raise ValueError("Encryption key belum tersedia.")

    cipher = Fernet(key)

    decrypted = cipher.decrypt(
        text.encode("utf-8")
    )

    return decrypted.decode("utf-8")


# =========================================================
# SALT
# =========================================================

def create_salt(user_id: str = "") -> bytes:
    """
    Membuat salt.

    Jika user_id diberikan, salt dibuat stabil berdasarkan
    user_id sehingga bisa digunakan kembali.

    Fungsi ini dipertahankan agar kode lama tetap kompatibel.
    """

    if user_id:
        return hashlib.sha256(
            f"VaultX-SALT-v1:{user_id}".encode("utf-8")
        ).digest()

    return secrets.token_bytes(32)


# =========================================================
# RANDOM VAULT KEY
# =========================================================

def generate_vault_key() -> bytes:
    """
    Membuat encryption key baru untuk vault.
    """

    return Fernet.generate_key()


# =========================================================
# LOAD LOCAL VAULT KEYS
# =========================================================

def _load_vault_keys() -> dict:
    """
    Membaca daftar Vault Key lokal.
    """

    if not KEY_FILE.exists():
        return {}

    try:
        with open(KEY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {}

        return data

    except Exception as error:
        print("Vault key file error:", repr(error))
        return {}


# =========================================================
# SAVE LOCAL VAULT KEYS
# =========================================================

def _save_vault_keys(data: dict):
    """
    Menyimpan Vault Key lokal.
    """

    APP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_file = KEY_FILE.with_suffix(".tmp")

    with open(
        temporary_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2
        )

    temporary_file.replace(KEY_FILE)

    # Linux/macOS:
    # mencoba membatasi permission file.
    try:
        KEY_FILE.chmod(0o600)
    except Exception:
        pass


# =========================================================
# GET / CREATE VAULT KEY
# =========================================================

def get_or_create_vault_key(user_id: str) -> bytes:
    """
    Mengambil Vault Key berdasarkan user_id.

    Kalau belum ada:
        buat key baru
        simpan lokal
        kembalikan key

    Kalau sudah ada:
        ambil key lama
    """

    if not user_id:
        raise ValueError(
            "user_id diperlukan untuk membuat Vault Key."
        )

    user_id = str(user_id).strip()

    if not user_id:
        raise ValueError(
            "user_id tidak boleh kosong."
        )

    data = _load_vault_keys()

    stored_key = data.get(user_id)

    # -----------------------------------------------------
    # KEY SUDAH ADA
    # -----------------------------------------------------

    if stored_key:

        try:
            key = stored_key.encode("utf-8")

            # Validasi apakah key benar-benar Fernet key.
            Fernet(key)

            return key

        except Exception:
            print(
                "Vault Key lama tidak valid. "
                "Membuat key baru."
            )

    # -----------------------------------------------------
    # BUAT KEY BARU
    # -----------------------------------------------------

    key = generate_vault_key()

    data[user_id] = key.decode("utf-8")

    _save_vault_keys(data)

    print(
        "Vault Key dibuat untuk user:",
        user_id
    )

    return key


# =========================================================
# SESSION STORAGE
# =========================================================

def save_session(
    access_token: str,
    refresh_token: str
):
    """
    Menyimpan session Supabase secara lokal.

    Digunakan supaya aplikasi dapat mencoba memulihkan
    login ketika dibuka kembali.
    """

    if not access_token or not refresh_token:
        return

    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

    temporary_file = SESSION_FILE.with_suffix(".tmp")

    with open(
        temporary_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file
        )

    temporary_file.replace(
        SESSION_FILE
    )

    try:
        SESSION_FILE.chmod(0o600)
    except Exception:
        pass


# =========================================================
# LOAD SESSION
# =========================================================

def load_session() -> dict | None:
    """
    Mengambil session lokal.
    """

    if not SESSION_FILE.exists():
        return None

    try:
        with open(
            SESSION_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            return None

        access_token = data.get(
            "access_token"
        )

        refresh_token = data.get(
            "refresh_token"
        )

        if not access_token or not refresh_token:
            return None

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    except Exception as error:
        print(
            "Session file error:",
            repr(error)
        )

        return None


# =========================================================
# CLEAR SESSION
# =========================================================

def clear_session():
    """
    Menghapus session lokal.

    Tidak menghapus:
    - Vault Key
    - password database
    - akun Supabase
    """

    try:
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()

    except Exception as error:
        print(
            "Clear session error:",
            repr(error)
        )