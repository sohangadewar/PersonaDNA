from fastapi import APIRouter

router = APIRouter()

@router.post("/analyze")
def analyze():

    return {
        "trust_score": 94,
        "ai_confidence": 98,
        "verified_claims": 18,
        "risk_level": "Low",
        "recruiter_verdict": "Recommended for Technical Interview",

        "skills": [
            "React",
            "Python",
            "FastAPI",
            "Machine Learning",
            "Prompt Engineering"
        ],

        "strengths": [
            "Resume matches LinkedIn timeline",
            "GitHub repositories show consistent commits",
            "Projects support listed skills"
        ],

        "warnings": [
            "One certificate could not be verified",
            "Portfolio has no live deployment"
        ]
    }