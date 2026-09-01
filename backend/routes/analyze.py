from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.services.verifier import verify_candidate

router = APIRouter()


@router.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    github_url: str = Form(""),
    linkedin_url: str = Form(""),
    linkedin_result: str = Form(""),
):

    try:

        result = await verify_candidate(
            resume=resume,
            github_url=github_url,
            linkedin_url=linkedin_url,
            linkedin_result=linkedin_result,
        )

        print("API RESULT:", result)
        print("API RESULT TYPE:", type(result))

        if result is None:
            raise HTTPException(
                status_code=500,
                detail="verify_candidate returned None"
            )

        print("DEBUG RESULT:", result)
        print("DEBUG RESULT TYPE:", type(result))

        return result.model_dump()

    except HTTPException:

        raise

    except Exception as exc:

        print("Analyze route error:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail="Candidate verification failed.",
        ) from exc
