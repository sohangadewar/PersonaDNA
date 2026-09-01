from pydantic import BaseModel


class CandidateReport(BaseModel):
    """
    Final PersonaDNA candidate verification report.
    """

    # ========================================================
    # PERSONADNA SCORING
    # ========================================================

    trust_score: int
    ai_confidence: int

    # ========================================================
    # CLAIM VERIFICATION
    # ========================================================

    verified_claims: int

    # ========================================================
    # RECRUITER ASSESSMENT
    # ========================================================

    risk_level: str
    recruiter_verdict: str

    # ========================================================
    # CANDIDATE PROFILE
    # ========================================================

    skills: list[str]
    strengths: list[str]
    warnings: list[str]

    # ========================================================
    # GEMINI CANDIDATE INTELLIGENCE
    # ========================================================

    candidate_insight: str