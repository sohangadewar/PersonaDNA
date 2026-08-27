# ============================================================
# PersonaDNA - Trust Scoring Engine
# ============================================================

def clamp_score(score: float) -> int:
    return max(0, min(100, round(score)))


def calculate_trust_score(
    identity: dict,
    github_evidence: dict,
    claims: list[dict] | None = None,
    evidence_report: list[dict] | None = None,
    linkedin_evidence: dict | None = None,
) -> dict:

    claims = claims or []
    evidence_report = evidence_report or []
    linkedin_evidence = linkedin_evidence or {}

    score = 0
    breakdown = {}

    # ========================================================
    # 1. CLAIM EVIDENCE - 40 POINTS
    # ========================================================

    skill_claims = [
        claim
        for claim in claims
        if claim.get("type") == "skill"
    ]

    if skill_claims:

        supported = sum(
            1
            for claim in skill_claims
            if claim.get("status") == "supported"
        )

        claim_ratio = supported / len(skill_claims)

        claim_score = claim_ratio * 40

    else:
        # If there are no skill claims, don't punish the candidate.
        claim_score = 30

    score += claim_score
    breakdown["claim_evidence"] = round(claim_score)

    # ========================================================
    # 2. RAG VERIFICATION - 20 POINTS
    # ========================================================

    rag_claims = [
        claim
        for claim in claims
        if claim.get("rag_status")
    ]

    if rag_claims:

        rag_verified = sum(
            1
            for claim in rag_claims
            if claim.get("rag_status") in {
                "verified",
                "supported",
                "confirmed",
            }
        )

        rag_ratio = rag_verified / len(rag_claims)

        rag_score = rag_ratio * 20

    else:
        rag_score = 10

    score += rag_score
    breakdown["rag_verification"] = round(rag_score)

    # ========================================================
    # 3. IDENTITY VERIFICATION - 20 POINTS
    # ========================================================

    identity_score = 0

    github_match = bool(
        identity.get("github_match", False)
    )

    linkedin_match = bool(
        identity.get("linkedin_match", False)
    )

    github_found = bool(
        github_evidence.get("profile_found", False)
    )

    linkedin_authorized = bool(
        linkedin_evidence.get(
            "authorized_source",
            False,
        )
    )

    if github_match:
        identity_score += 10
    elif github_found:
        identity_score += 5

    if linkedin_match and linkedin_authorized:
        identity_score += 10
    elif linkedin_authorized:
        identity_score += 5

    # If LinkedIn wasn't supplied/authorized, don't penalize
    # the candidate for something they didn't provide.
    if not linkedin_authorized:
        identity_score += 5

    identity_score = min(identity_score, 20)

    score += identity_score
    breakdown["identity_verification"] = identity_score

    # ========================================================
    # 4. GITHUB QUALITY - 10 POINTS
    # ========================================================

    github_score = 0

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if github_found:
        github_score += 5

    if repositories:
        github_score += 3

    if len(repositories) >= 3:
        github_score += 2

    github_score = min(github_score, 10)

    score += github_score
    breakdown["github_quality"] = github_score

    # ========================================================
    # FINAL SCORE
    # ========================================================

    trust_score = clamp_score(score)

    # ========================================================
    # RISK LEVEL
    # ========================================================

    if trust_score >= 80:
        risk_level = "Low"

    elif trust_score >= 60:
        risk_level = "Medium"

    else:
        risk_level = "High"

    # ========================================================
    # RECRUITER VERDICT
    # ========================================================

    if trust_score >= 85:
        recruiter_verdict = (
            "Strong verification evidence. "
            "Candidate appears highly credible."
        )

    elif trust_score >= 75:
        recruiter_verdict = (
            "Good verification evidence. "
            "Candidate appears credible with minor review recommended."
        )

    elif trust_score >= 60:
        recruiter_verdict = (
            "Moderate verification evidence. "
            "Manual verification recommended."
        )

    else:
        recruiter_verdict = (
            "Limited verification evidence. "
            "Additional verification required."
        )

    return {
        "trust_score": trust_score,
        "risk_level": risk_level,
        "recruiter_verdict": recruiter_verdict,
        "score_breakdown": breakdown,
    }