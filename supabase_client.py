import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client


BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(
    ENV_FILE
)

SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)


if not SUPABASE_URL:

    raise RuntimeError(
        "SUPABASE_URL belum diatur."
    )


if not SUPABASE_KEY:

    raise RuntimeError(
        "SUPABASE_KEY belum diatur."
    )


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


def sign_up(
    email: str,
    password: str
):

    return supabase.auth.sign_up(
        {
            "email": email,
            "password": password
        }
    )


def sign_in(
    email: str,
    password: str
):

    return supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password
        }
    )


def sign_out():

    try:

        supabase.auth.sign_out()

    except Exception:

        pass


def current_user():

    try:

        response = (
            supabase.auth.get_user()
        )

        if response and response.user:

            return response.user

    except Exception:

        pass

    return None