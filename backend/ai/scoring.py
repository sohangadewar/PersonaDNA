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

       # ========================================================
    # 1. CLAIM EVIDENCE - 40 POINTS
    # ========================================================

    if claims:

        supported_claims = 0.0

        for claim in claims:

            status = str(
                claim.get(
                    "status",
                    "",
                )
            ).strip().lower()

            rag_status = str(
                claim.get(
                    "rag_status",
                    "",
                )
            ).strip().lower()

            rag_confidence = float(
                claim.get(
                    "rag_confidence",
                    0,
                )
                or 0
            )

            github_supported = (
                claim.get(
                    "evidence",
                    {}
                ).get(
                    "github",
                    False,
                )
                is True
            )

            # Strong direct evidence
            if (
                status == "supported"
                or rag_status in {
                    "verified",
                    "supported",
                    "confirmed",
                    "matched",
                    "match",
                    "strong",
                }
                or github_supported
            ):
                supported_claims += 1.0

            # Partial RAG evidence
            elif (
                rag_status
                in {
                    "partially_supported",
                    "partially supported",
                }
                and rag_confidence >= 50
            ):
                supported_claims += 0.5

        claim_ratio = (
            supported_claims
            / len(claims)
        )

        claim_score = claim_ratio * 40

    else:

        claim_score = 0

    score += claim_score

    breakdown["claim_evidence"] = round(
        claim_score
    )

    # ========================================================
    # 2. RAG VERIFICATION - 20 POINTS
    # ========================================================

    # ========================================================
    # 2. RAG VERIFICATION - 20 POINTS
    # ========================================================

    rag_claims = [
        claim
        for claim in claims
        if claim.get("rag_status")
    ]

    verified_statuses = {
        "verified",
        "supported",
        "confirmed",
        "match",
        "matched",
        "strong",
        "true",
    }

    partially_supported_statuses = {
        "partially_supported",
        "partially supported",
    }

    if rag_claims:

        rag_points = 0.0

        for claim in rag_claims:

            status = str(
                claim.get(
                    "rag_status",
                    "",
                )
            ).strip().lower()

            try:
                rag_confidence = float(
                    claim.get(
                        "rag_confidence",
                        0,
                    ) or 0
                )
            except (
                TypeError,
                ValueError,
            ):
                rag_confidence = 0.0

            # Fully supported RAG claim
            if status in verified_statuses:

                rag_points += 1.0

            # Partially supported claim
            elif status in partially_supported_statuses:

                rag_points += 0.75

            # Resume-only / needs review
            elif status == "needs_review":

                rag_points += 0.35

            # Use confidence as a secondary signal
            # when the status itself is not decisive.
            elif rag_confidence >= 80:

                rag_points += 0.75

            elif rag_confidence >= 60:

                rag_points += 0.50

            elif rag_confidence >= 40:

                rag_points += 0.25

        rag_score = (
            rag_points / len(rag_claims)
        ) * 20

    else:

        # RAG did not return claim statuses.
        # Give a neutral score rather than zero.
        rag_score = 10

    score += rag_score

    breakdown["rag_verification"] = round(
        rag_score
    )

    # ========================================================
    # 3. IDENTITY VERIFICATION - 20 POINTS
    # ========================================================

    identity_score = 0

    github_match = bool(
        identity.get(
            "github_match",
            False,
        )
    )

    linkedin_match = bool(
        identity.get(
            "linkedin_match",
            False,
        )
    )

    github_found = bool(
        github_evidence.get(
            "profile_found",
            False,
        )
    )

    linkedin_authorized = bool(
        linkedin_evidence.get(
            "authorized_source",
            False,
        )
    )

    # GitHub
    if github_match:
        identity_score += 10

    elif github_found:
        identity_score += 5

    # LinkedIn
    if linkedin_authorized:

        if linkedin_match:
            identity_score += 10
        else:
            identity_score += 5

    else:
        # LinkedIn was not authorized.
        # Do not heavily penalize the candidate.
        identity_score += 5

    identity_score = min(
        identity_score,
        20,
    )

    score += identity_score

    breakdown["identity_verification"] = (
        identity_score
    )

    # ========================================================
    # 4. GITHUB QUALITY - 20 POINTS
    # ========================================================

    github_score = 0

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    technology_evidence = github_evidence.get(
        "technology_evidence",
        [],
    )

    if github_found:
        github_score += 5

    if repositories:
        github_score += 5

    if len(repositories) >= 3:
        github_score += 5

    if technology_evidence:
        github_score += 5

    github_score = min(
        github_score,
        20,
    )

    score += github_score

    breakdown["github_quality"] = (
        github_score
    )

    # ========================================================
    # 5. STRONG EVIDENCE BONUS
    # ========================================================

    strong_evidence = 0

    # Multiple GitHub repositories
    if len(repositories) >= 3:
        strong_evidence += 3

    # Technology evidence
    if len(technology_evidence) >= 5:
        strong_evidence += 3

    # Identity
    if github_match:
        strong_evidence += 2

    if (
        linkedin_authorized
        and linkedin_match
    ):
        strong_evidence += 2

    strong_evidence = min(
        strong_evidence,
        10,
    )

    score += strong_evidence

    breakdown["strong_evidence_bonus"] = (
        strong_evidence
    )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    trust_score = clamp_score(score)

    # ========================================================
    # RISK
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

    if trust_score >= 90:

        recruiter_verdict = (
            "Excellent verification evidence. "
            "Candidate appears highly credible."
        )

    elif trust_score >= 80:

        recruiter_verdict = (
            "Strong verification evidence. "
            "Candidate appears credible."
        )

    elif trust_score >= 70:

        recruiter_verdict = (
            "Good verification evidence. "
            "Minor manual verification is recommended."
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