from pydantic import BaseModel

class CandidateReport(BaseModel):
    trust_score: int
    ai_confidence: int
    verified_claims: int
    risk_level: str
    recruiter_verdict: str
    skills: list[str]
    strengths: list[str]
    warnings: list[str]