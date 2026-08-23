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

LINKEDIN_AUTH_URL = (
    "https://www.linkedin.com/oauth/v2/authorization"
)

LINKEDIN_TOKEN_URL = (
    "https://www.linkedin.com/oauth/v2/accessToken"
)

LINKEDIN_API_URL = (
    "https://api.linkedin.com/rest"
)


# ============================================================
# LinkedIn OAuth scopes
# ============================================================

LINKEDIN_SCOPES = [
    "openid",
    "profile",
    "email",
]


# ============================================================
# Temporary OAuth storage
# ============================================================

# Development only.
#
# For production, use a database, Redis, or another
# server-side persistent storage mechanism.

OAUTH_STATES: set[str] = set()

OAUTH_RESULTS: dict[str, dict] = {}


# ============================================================
# OAuth State
# ============================================================

def generate_oauth_state() -> str:
    """
    Generate a random OAuth state value.

    Used for CSRF protection.
    """

    state = secrets.token_urlsafe(32)

    OAUTH_STATES.add(state)

    return state


def validate_oauth_state(
    state: str,
) -> bool:
    """
    Validate and consume an OAuth state.

    A state can only be used once.
    """

    if not state:
        return False

    if state not in OAUTH_STATES:
        return False

    OAUTH_STATES.remove(state)

    return True


# ============================================================
# OAuth Result Storage
# ============================================================

def create_oauth_result(
    linkedin_data: dict,
) -> str:
    """
    Store authorized LinkedIn data temporarily.

    Returns a one-time result code that is sent to
    the frontend.
    """

    result_code = secrets.token_urlsafe(32)

    OAUTH_RESULTS[result_code] = linkedin_data

    return result_code


def consume_oauth_result(
    result_code: str,
) -> dict | None:
    """
    Retrieve and immediately delete a LinkedIn
    OAuth result.

    This makes the result code one-time use.
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
    Build the LinkedIn OAuth authorization URL.

    Returns:
        authorization_url
        state
    """

    if not LINKEDIN_CLIENT_ID:
        raise RuntimeError(
            "LINKEDIN_CLIENT_ID is not configured."
        )

    state = generate_oauth_state()

    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": " ".join(LINKEDIN_SCOPES),
    }

    authorization_url = (
        f"{LINKEDIN_AUTH_URL}?"
        f"{urlencode(params)}"
    )

    return (
        authorization_url,
        state,
    )


# ============================================================
# Authorization Code → Access Token
# ============================================================

def exchange_code_for_token(
    code: str,
) -> dict:
    """
    Exchange LinkedIn authorization code
    for an access token.
    """

    if not code:
        raise ValueError(
            "Authorization code is missing."
        )

    if not LINKEDIN_CLIENT_ID:
        raise RuntimeError(
            "LINKEDIN_CLIENT_ID is not configured."
        )

    if not LINKEDIN_CLIENT_SECRET:
        raise RuntimeError(
            "LINKEDIN_CLIENT_SECRET is not configured."
        )

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
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
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
# Generic LinkedIn REST API GET
# ============================================================

def linkedin_get(
    endpoint: str,
    access_token: str,
) -> dict:
    """
    Perform an authenticated LinkedIn REST API GET request.
    """

    if not access_token:
        raise ValueError(
            "LinkedIn access token is missing."
        )

    response = requests.get(
        f"{LINKEDIN_API_URL}{endpoint}",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "LinkedIn-Version": LINKEDIN_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
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
# Extract Localized LinkedIn Value
# ============================================================

def extract_localized_value(
    field: dict | None,
) -> str:
    """
    Extract the first localized value from a
    LinkedIn localized field.
    """

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

    return str(
        next(
            iter(localized.values())
        )
    )


# ============================================================
# LinkedIn OpenID Connect UserInfo
# ============================================================

def fetch_linkedin_identity(
    access_token: str,
) -> dict:
    """
    Fetch the authorized member's identity information
    using LinkedIn OpenID Connect UserInfo.
    """

    if not access_token:
        raise ValueError(
            "LinkedIn access token is missing."
        )

    response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
        },
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "LinkedIn UserInfo request failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    return response.json()


# ============================================================
# LinkedIn Verification Data
# ============================================================

def fetch_linkedin_verification(
    access_token: str,
) -> dict:
    """
    Fetch LinkedIn verification information.

    Currently returns an empty structure because the
    verification endpoint/data is not being requested by
    the current OAuth integration.

    This is intentionally kept separate so verification
    support can be added later without changing the OAuth flow.
    """

    return {
        "verifications": [],
    }


# ============================================================
# Normalize LinkedIn API Response
# ============================================================

def build_linkedin_profile_data(
    identity_data: dict,
    verification_data: dict,
) -> dict:
    """
    Convert LinkedIn UserInfo data into the structure
    expected by PersonaDNA.
    """

    if not isinstance(
        identity_data,
        dict,
    ):
        identity_data = {}

    if not isinstance(
        verification_data,
        dict,
    ):
        verification_data = {}

    first_name = str(
        identity_data.get(
            "given_name",
            "",
        )
        or ""
    ).strip()

    last_name = str(
        identity_data.get(
            "family_name",
            "",
        )
        or ""
    ).strip()

    display_name = str(
        identity_data.get(
            "name",
            "",
        )
        or ""
    ).strip()

    # If LinkedIn does not provide "name",
    # construct it from first and last name.
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

        "verification_categories": (
            verification_categories
        ),

        "verification_report": (
            verification_data
        ),
    }


# ============================================================
# Complete Authorized LinkedIn Analysis
# ============================================================

def fetch_authorized_linkedin_data(
    access_token: str,
) -> dict:
    """
    Fetch and normalize authorized LinkedIn data.

    This function is called by main.py after successful
    OAuth authorization.
    """

    if not access_token:
        raise ValueError(
            "LinkedIn access token is missing."
        )

    # --------------------------------------------------------
    # 1. Get LinkedIn identity
    # --------------------------------------------------------

    identity_data = fetch_linkedin_identity(
        access_token
    )

    # --------------------------------------------------------
    # 2. Get verification data
    # --------------------------------------------------------

    verification_data = (
        fetch_linkedin_verification(
            access_token
        )
    )

    # --------------------------------------------------------
    # 3. Normalize data
    # --------------------------------------------------------

    profile_data = build_linkedin_profile_data(
        identity_data,
        verification_data,
    )

    # --------------------------------------------------------
    # 4. Safe debug information
    #
    # Never print the access token.
    # --------------------------------------------------------

    print(
        "\n========== LINKEDIN OAUTH DEBUG =========="
    )

    print(
        "LinkedIn display name:",
        profile_data.get(
            "name",
            "",
        ),
    )

    print(
        "LinkedIn email available:",
        bool(
            profile_data.get(
                "email",
                "",
            )
        ),
    )

    print(
        "LinkedIn authorized data:",
        bool(profile_data),
    )

    print(
        "==========================================\n"
    )

    return profile_data