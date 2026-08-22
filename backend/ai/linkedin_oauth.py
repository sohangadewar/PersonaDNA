import os
import secrets
from urllib.parse import urlencode

import requests

# ============================================================
# Configuration
# ============================================================

LINKEDIN_CLIENT_ID = os.getenv(
    "LINKEDIN_CLIENT_ID",
    "",
)

LINKEDIN_CLIENT_SECRET = os.getenv(
    "LINKEDIN_CLIENT_SECRET",
    "",
)

LINKEDIN_REDIRECT_URI = os.getenv(
    "LINKEDIN_REDIRECT_URI",
    "http://127.0.0.1:8000/linkedin/callback",
)

LINKEDIN_VERSION = os.getenv(
    "LINKEDIN_VERSION",
    "202510",
)

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"

LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

LINKEDIN_API_URL = "https://api.linkedin.com/rest"

# Development/Lite:
# r_profile_basicinfo + r_verify
LINKEDIN_SCOPES = [
    "openid",
    "profile",
    "email",
]

# ============================================================
# Temporary OAuth state storage
# ============================================================

# IMPORTANT:
# This in-memory store is acceptable for local development only.
# For production, store state server-side in a session/database.
OAUTH_STATES = set()
OAUTH_RESULTS = {}


def generate_oauth_state() -> str:
    """
    Generate a random CSRF protection state.
    """

    state = secrets.token_urlsafe(32)

    OAUTH_STATES.add(state)

    return state


def validate_oauth_state(
    state: str,
) -> bool:

    if not state:
        return False

    if state not in OAUTH_STATES:
        return False

    OAUTH_STATES.remove(state)

    return True


def create_oauth_result(
    linkedin_data: dict,
) -> str:
    """
    Create a one-time code for handing LinkedIn
    profile data from the backend to the frontend.
    """

    result_code = secrets.token_urlsafe(32)

    OAUTH_RESULTS[result_code] = linkedin_data

    return result_code


def consume_oauth_result(
    result_code: str,
) -> dict | None:
    """
    Retrieve and immediately delete a one-time
    LinkedIn OAuth result.
    """

    if not result_code:
        return None

    return OAUTH_RESULTS.pop(
        result_code,
        None,
    )


# ============================================================
# Authorization URL
# ============================================================


def build_linkedin_authorization_url() -> tuple[str, str]:
    """
    Build LinkedIn OAuth authorization URL.

    Returns:
        authorization_url
        state
    """

    if not LINKEDIN_CLIENT_ID:
        raise RuntimeError("LINKEDIN_CLIENT_ID is not configured.")

    state = generate_oauth_state()

    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": " ".join(LINKEDIN_SCOPES),
    }

    authorization_url = f"{LINKEDIN_AUTH_URL}?" f"{urlencode(params)}"

    return (
        authorization_url,
        state,
    )


# ============================================================
# Authorization code → access token
# ============================================================


def exchange_code_for_token(
    code: str,
) -> dict:

    if not code:
        raise ValueError("Authorization code is missing.")

    if not LINKEDIN_CLIENT_ID:
        raise RuntimeError("LINKEDIN_CLIENT_ID is not configured.")

    if not LINKEDIN_CLIENT_SECRET:
        raise RuntimeError("LINKEDIN_CLIENT_SECRET is not configured.")

    response = requests.post(
        LINKEDIN_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": LINKEDIN_REDIRECT_URI,
            "client_id": LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET,
        },
        headers={
            "Content-Type": ("application/x-www-form-urlencoded"),
        },
        timeout=15,
    )

    if response.status_code != 200:

        raise RuntimeError(
            "LinkedIn token exchange failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    return response.json()


# ============================================================
# Generic LinkedIn API GET
# ============================================================


def linkedin_get(
    endpoint: str,
    access_token: str,
) -> dict:

    if not access_token:
        raise ValueError("LinkedIn access token is missing.")

    response = requests.get(
        f"{LINKEDIN_API_URL}{endpoint}",
        headers={
            "Authorization": (f"Bearer {access_token}"),
            "LinkedIn-Version": (LINKEDIN_VERSION),
            "X-Restli-Protocol-Version": ("2.0.0"),
        },
        timeout=15,
    )

    if response.status_code != 200:

        raise RuntimeError(
            "LinkedIn API request failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    return response.json()


# ============================================================
# Extract localized LinkedIn text
# ============================================================


def extract_localized_value(
    field: dict | None,
) -> str:

    if not isinstance(
        field,
        dict,
    ):
        return ""

    localized = field.get(
        "localized",
        {},
    )

    if not isinstance(
        localized,
        dict,
    ):
        return ""

    if not localized:
        return ""

    return str(next(iter(localized.values())))


# ============================================================
# LinkedIn OpenID Connect UserInfo
# ============================================================


def fetch_linkedin_identity(
    access_token: str,
) -> dict:

    response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"LinkedIn UserInfo request failed: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


# ============================================================
# Verification data
# ============================================================


def fetch_linkedin_verification(
    access_token: str,
) -> dict:

    return {}


# ============================================================
# Normalize LinkedIn API response
# ============================================================


def build_linkedin_profile_data(
    identity_data: dict,
    verification_data: dict,
) -> dict:

    first_name = identity_data.get(
        "given_name",
        "",
    )

    last_name = identity_data.get(
        "family_name",
        "",
    )

    display_name = identity_data.get(
        "name",
        "",
    )

    if not display_name:
        display_name = " ".join(
            value
            for value in (
                first_name,
                last_name,
            )
            if value
        ).strip()

    verification_categories = verification_data.get(
        "verifications",
        [],
    )

    if not isinstance(
        verification_categories,
        list,
    ):
        verification_categories = []

    return {
        "id": identity_data.get(
            "sub",
            "",
        ),
        "first_name": first_name,
        "last_name": last_name,
        "name": display_name,
        "email": identity_data.get(
            "email",
            "",
        ),
        "profile_url": identity_data.get(
            "profile_url",
            "",
        ),
        "profile_picture": identity_data.get(
            "picture",
            "",
        ),
        "verification_categories": (verification_categories),
        "verification_report": (verification_data),
    }


# ============================================================
# Complete authorized LinkedIn analysis
# ============================================================


def fetch_authorized_linkedin_data(
    access_token: str,
) -> dict:

    identity_data = fetch_linkedin_identity(access_token)

    verification_data = fetch_linkedin_verification(access_token)

    profile_data = build_linkedin_profile_data(
        identity_data,
        verification_data,
    )

    return profile_data
