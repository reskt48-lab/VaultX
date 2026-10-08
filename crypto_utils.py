import base64
import hashlib
import json
import secrets
from pathlib import Path

try:
    from kivy.app import App
except ImportError:
    App = None

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def get_app_dir():
    try:
        if App is not None:
            app = App.get_running_app()

            if app:
                path = Path(app.user_data_dir) / ".vaultx"
            else:
                path = Path.home() / ".vaultx"
        else:
            path = Path.home() / ".vaultx"

    except Exception:
        path = Path.home() / ".vaultx"

    path.mkdir(parents=True, exist_ok=True)
    return path


def get_key_file():
    return get_app_dir() / "vault_keys.json"


def get_session_file():
    return get_app_dir() / "session.json"


def derive_key(password: str, salt: bytes) -> bytes:
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


def encrypt_text(text: str, key: bytes) -> str:
    if not text:
        return ""

    if not key:
        raise ValueError("Encryption key belum tersedia.")

    return Fernet(key).encrypt(
        text.encode("utf-8")
    ).decode("utf-8")


def decrypt_text(text: str, key: bytes) -> str:
    if not text:
        return ""

    if not key:
        raise ValueError("Encryption key belum tersedia.")

    return Fernet(key).decrypt(
        text.encode("utf-8")
    ).decode("utf-8")


def create_salt(user_id: str = "") -> bytes:
    if user_id:
        return hashlib.sha256(
            f"VaultX-SALT-v1:{user_id}".encode("utf-8")
        ).digest()

    return secrets.token_bytes(32)


def generate_vault_key() -> bytes:
    return Fernet.generate_key()


def _load_vault_keys() -> dict:
    key_file = get_key_file()

    if not key_file.exists():
        return {}

    try:
        with open(key_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except Exception as error:
        print("Vault key file error:", repr(error))
        return {}


def _save_vault_keys(data: dict):
    key_file = get_key_file()

    key_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_file = key_file.with_suffix(".tmp")

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

    temporary_file.replace(key_file)

    try:
        key_file.chmod(0o600)
    except Exception:
        pass


def get_or_create_vault_key(user_id: str) -> bytes:
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

    if stored_key:
        try:
            key = stored_key.encode("utf-8")
            Fernet(key)
            return key

        except Exception:
            print(
                "Vault Key lama tidak valid. "
                "Membuat key baru."
            )

    key = generate_vault_key()

    data[user_id] = key.decode("utf-8")

    _save_vault_keys(data)

    return key


def save_session(
    access_token: str,
    refresh_token: str
):
    if not access_token or not refresh_token:
        return

    session_file = get_session_file()

    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

    temporary_file = session_file.with_suffix(".tmp")

    with open(
        temporary_file,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(data, file)

    temporary_file.replace(session_file)

    try:
        session_file.chmod(0o600)
    except Exception:
        pass


def load_session() -> dict | None:
    session_file = get_session_file()

    if not session_file.exists():
        return None

    try:
        with open(
            session_file,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return None

        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")

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


def clear_session():
    session_file = get_session_file()

    try:
        if session_file.exists():
            session_file.unlink()
    except Exception as error:
        print(
            "Clear session error:",
            repr(error)
        )