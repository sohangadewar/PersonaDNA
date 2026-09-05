from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from backend.ai.linkedin_oauth import (
    build_linkedin_authorization_url,
    validate_oauth_state,
    exchange_code_for_token,
    fetch_authorized_linkedin_data,
    create_oauth_result,
    consume_oauth_result,
)

router = APIRouter()


@router.get("/linkedin/connect")
async def linkedin_connect():
    """
    Start the LinkedIn OAuth flow.

    The user is redirected to LinkedIn's authorization page.
    """
    try:
        authorization_url, _ = build_linkedin_authorization_url()

        return RedirectResponse(
            url=authorization_url,
            status_code=307,
        )

    except Exception as exc:
        print("LinkedIn connect error:", repr(exc))
        raise HTTPException(
            status_code=500,
            detail="Unable to start LinkedIn authorization.",
        ) from exc


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str = "",
    state: str = "",
    error: str = "",
    error_description: str = "",
):
    """
    Handle LinkedIn's OAuth callback.

    LinkedIn redirects the user here after authorization.
    """
    frontend_url = "http://localhost:5173"

    if error:
        print(
            "LinkedIn authorization error:",
            error,
            error_description,
        )

        return RedirectResponse(
            url=(
                f"{frontend_url}"
                "?linkedin_error=authorization_failed"
            ),
            status_code=307,
        )

    if not code:
        return RedirectResponse(
            url=(
                f"{frontend_url}"
                "?linkedin_error=missing_code"
            ),
            status_code=307,
        )

    if not state:
        return RedirectResponse(
            url=(
                f"{frontend_url}"
                "?linkedin_error=missing_state"
            ),
            status_code=307,
        )

    try:
        if not validate_oauth_state(state):
            print("LinkedIn OAuth state validation failed.")

            return RedirectResponse(
                url=(
                    f"{frontend_url}"
                    "?linkedin_error=invalid_state"
                ),
                status_code=307,
            )

        access_token_data = exchange_code_for_token(code)

        access_token = access_token_data.get("access_token", "")

        if not access_token:
            print("LinkedIn token response did not contain access_token.")

            return RedirectResponse(
                url=(
                    f"{frontend_url}"
                    "?linkedin_error=token_failed"
                ),
                status_code=307,
            )

        linkedin_data = fetch_authorized_linkedin_data(
            access_token
        )

        if not linkedin_data:
            print("LinkedIn returned empty profile data.")

            return RedirectResponse(
                url=(
                    f"{frontend_url}"
                    "?linkedin_error=profile_failed"
                ),
                status_code=307,
            )

        result_code = create_oauth_result(linkedin_data)

        redirect_url = (
            f"{frontend_url}"
            f"?linkedin_result={result_code}"
        )

        return RedirectResponse(
            url=redirect_url,
            status_code=307,
        )

    except Exception as exc:
        print("LinkedIn callback error:", repr(exc))

        return RedirectResponse(
            url=(
                f"{frontend_url}"
                "?linkedin_error=authorization_failed"
            ),
            status_code=307,
        )


@router.get("/linkedin/result")
async def linkedin_result(code: str = ""):
    """
    Retrieve the LinkedIn profile stored during OAuth.

    The result code is one-time use.
    """
    if not code:
        raise HTTPException(
            status_code=400,
            detail="LinkedIn result code is required.",
        )

    try:
        linkedin_data = consume_oauth_result(code)

        if not linkedin_data:
            raise HTTPException(
                status_code=404,
                detail="LinkedIn result not found or already consumed.",
            )

        return {
            "linkedin": linkedin_data
        }

    except HTTPException:
        raise

    except Exception as exc:
        print("LinkedIn result error:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve LinkedIn result.",
        ) from exc