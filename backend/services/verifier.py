from models.report import CandidateReport


def verify_candidate():

    return CandidateReport(
        trust_score=94,
        ai_confidence=98,
        verified_claims=18,
        risk_level="Low",
        recruiter_verdict="Recommended for Technical Interview",

        skills=[
            "React",
            "Python",
            "FastAPI",
            "Machine Learning",
            "Prompt Engineering",
        ],

        strengths=[
            "Resume matches LinkedIn",
            "GitHub repositories are active",
            "Projects validate listed skills",
        ],

        warnings=[
            "Portfolio lacks deployed project",
            "AWS certificate pending verification",
        ],
    )