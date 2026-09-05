from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from backend.services.verifier import verify_candidate
from backend.routes.linkedin import router as linkedin_router
from fastapi.responses import RedirectResponse

from backend.ai.linkedin_oauth import (
    build_linkedin_authorization_url,
    exchange_code_for_token,
    fetch_authorized_linkedin_data,
    create_oauth_result,
    validate_oauth_state,
    consume_oauth_result,
)


app = FastAPI(
    title="PersonaDNA API",
    version="1.0.0",
    description="AI-powered candidate verification and trust analysis API.",
)

app.include_router(linkedin_router)

@app.get("/linkedin/connect")
async def linkedin_connect():
    try:
        authorization_url, _ = build_linkedin_authorization_url()
        return RedirectResponse(url=authorization_url)

    except Exception as exc:
        print("LinkedIn connect error:", repr(exc))
        raise HTTPException(
            status_code=500,
            detail="Unable to start LinkedIn authorization.",
        ) from exc


@app.get("/linkedin/callback")
async def linkedin_callback(
    code: str = "",
    state: str = "",
    error: str = "",
):
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"LinkedIn authorization failed: {error}",
        )

    if not code:
        raise HTTPException(
            status_code=400,
            detail="LinkedIn authorization code is missing.",
        )

    if not validate_oauth_state(state):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired LinkedIn OAuth state.",
        )

    try:
        token_data = exchange_code_for_token(code)

        access_token = token_data.get("access_token", "")

        if not access_token:
            raise RuntimeError(
                "LinkedIn access token was not returned."
            )

        linkedin_data = fetch_authorized_linkedin_data(
            access_token
        )

        result_code = create_oauth_result(
            linkedin_data
        )

        frontend_url = (
            "http://localhost:5173"
            f"?linkedin_result={result_code}"
        )

        return RedirectResponse(url=frontend_url)

    except Exception as exc:
        print("LinkedIn callback error:", repr(exc))
        raise HTTPException(
            status_code=500,
            detail="LinkedIn authorization failed.",
        ) from exc


@app.get("/linkedin/result")
async def linkedin_result(
    code: str = "",
):
    if not code:
        raise HTTPException(
            status_code=400,
            detail="LinkedIn result code is missing.",
        )

    linkedin_data = consume_oauth_result(code)

    if linkedin_data is None:
        raise HTTPException(
            status_code=404,
            detail="LinkedIn result not found or already consumed.",
        )

    return {
        "linkedin": linkedin_data
    }
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "PersonaDNA API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }


@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    github_url: str = Form(""),
    linkedin_url: str = Form(""),
    linkedin_result: str = Form(""),
):
    return await verify_candidate(
        resume=resume,
        github_url=github_url,
        linkedin_url=linkedin_url,
        linkedin_result=linkedin_result,
    )
    