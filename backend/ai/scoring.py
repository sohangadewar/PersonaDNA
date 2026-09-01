# ============================================================
# PersonaDNA - Trust Scoring Engine
# ============================================================


def clamp_score(score: float) -> int:
    """Keep trust score between 0 and 100."""
    return max(0, min(100, round(score)))


def safe_confidence(value) -> float:
    """Safely convert confidence to a 0-100 float."""
    try:
        return max(
            0.0,
            min(100.0, float(value or 0))
        )
    except (TypeError, ValueError):
        return 0.0


# ============================================================
# TRUST SCORE
#
# TOTAL = 100
#
# Claim Evidence        = 30
# RAG Verification      = 20
# Identity Verification = 20
# GitHub Quality        = 15
# LinkedIn Verification = 15
# ============================================================

def calculate_trust_score(
    identity: dict,
    github_evidence: dict,
    claims: list[dict] | None = None,
    evidence_report: list[dict] | None = None,
    linkedin_evidence: dict | None = None,
) -> dict:

    identity = identity or {}
    github_evidence = github_evidence or {}
    linkedin_evidence = linkedin_evidence or {}

    claims = claims or []
    evidence_report = evidence_report or []

    breakdown = {}

    # ========================================================
    # 1. CLAIM EVIDENCE — 30
    #
    # Uses the authoritative evidence report.
    # ========================================================

    claim_score = 0.0

    if evidence_report:

        valid_report = [
            item
            for item in evidence_report
            if isinstance(item, dict)
        ]

        if valid_report:

            report_scores = []

            for item in valid_report:

                try:
                    score = float(
                        item.get(
                            "score",
                            0,
                        )
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    score = 0.0

                score = max(
                    0.0,
                    min(
                        100.0,
                        score,
                    ),
                )

                report_scores.append(score)

            if report_scores:

                average_evidence_score = (
                    sum(report_scores)
                    / len(report_scores)
                )

                claim_score = (
                    average_evidence_score
                    / 100.0
                ) * 30

    breakdown["claim_evidence"] = round(
        claim_score
    )

    # ========================================================
    # 2. RAG VERIFICATION — 20
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

    partial_statuses = {
        "partially_supported",
        "partially supported",
        "partial",
    }

    rag_score = 0.0

    if rag_claims:

        rag_points = 0.0

        for claim in rag_claims:

            status = str(
                claim.get(
                    "rag_status",
                    "",
                )
            ).strip().lower()

            confidence = safe_confidence(
                claim.get(
                    "rag_confidence",
                    0,
                )
            )

            if status in verified_statuses:

                points = (
                    confidence
                    / 100.0
                )

            elif status in partial_statuses:

                points = (
                    confidence
                    / 100.0
                ) * 0.60

            else:

                points = 0.0

            rag_points += min(
                points,
                1.0,
            )

        rag_score = (
            rag_points
            / len(rag_claims)
        ) * 20

    breakdown["rag_verification"] = round(
        rag_score
    )

    # ========================================================
    # 3. IDENTITY VERIFICATION — 20
    #
    # GitHub  = 10
    # LinkedIn = 10
    #
    # Missing evidence = 0
    # Mismatch           = 0
    # Match              = full points
    # ========================================================

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

    identity_score = 0

    # --------------------------------------------------------
    # GitHub identity — 10
    # --------------------------------------------------------

    if github_match:
        identity_score += 10

    # Do not reward GitHub merely because a profile exists.
    # It must match the candidate identity.

    # --------------------------------------------------------
    # LinkedIn identity — 10
    # --------------------------------------------------------

    if (
        linkedin_authorized
        and linkedin_match
    ):
        identity_score += 10

    identity_score = min(
        identity_score,
        20,
    )

    breakdown["identity_verification"] = (
        identity_score
    )

    # ========================================================
    # 4. GITHUB QUALITY — 15
    #
    # Only count GitHub quality when:
    #
    #     GitHub exists
    #     AND
    #     GitHub identity matches
    # ========================================================

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    technology_evidence = github_evidence.get(
        "technology_evidence",
        [],
    )

    if not isinstance(
        repositories,
        list,
    ):
        repositories = []

    if not isinstance(
        technology_evidence,
        list,
    ):
        technology_evidence = []

    github_score = 0

    if (
        github_found
        and github_match
    ):

        # Candidate-owned GitHub profile
        github_score += 4

        # Has repositories
        if repositories:
            github_score += 4

        # At least 3 repositories
        if len(repositories) >= 3:
            github_score += 4

        # Technology evidence
        if technology_evidence:
            github_score += 3

    github_score = min(
        github_score,
        15,
    )

    breakdown["github_quality"] = (
        github_score
    )

    # ========================================================
    # 5. LINKEDIN VERIFICATION — 15
    #
    # Authorized LinkedIn = 7
    # Identity match      = +8
    #
    # Maximum = 15
    # ========================================================

    linkedin_score = 0

    if linkedin_authorized:

        # Authorized LinkedIn evidence
        linkedin_score += 7

        if linkedin_match:

            # Identity confirmed
            linkedin_score += 8

        # If authorized but identity does not match,
        # keep only the source-verification points.

    linkedin_score = min(
        linkedin_score,
        15,
    )

    breakdown["linkedin_verification"] = (
        linkedin_score
    )

       # ========================================================
    # 6. TOTAL SCORE
    #
    # IMPORTANT:
    # Calculate the final score from the displayed rounded
    # components so the breakdown always matches the total.
    # ========================================================

    trust_score = clamp_score(
        breakdown["claim_evidence"]
        + breakdown["rag_verification"]
        + breakdown["identity_verification"]
        + breakdown["github_quality"]
        + breakdown["linkedin_verification"]
    )



    # ========================================================
    # 7. RISK LEVEL
    # ========================================================

    if trust_score >= 80:

        risk_level = "Low"

    elif trust_score >= 60:

        risk_level = "Medium"

    else:

        risk_level = "High"

    # ========================================================
    # 8. RECRUITER VERDICT
    #
    # Important wording:
    # We say "supporting evidence", not "proven".
    # ========================================================

    if trust_score >= 90:

        recruiter_verdict = (
            "Excellent supporting evidence. "
            "The candidate's claims are strongly "
            "supported by the available evidence."
        )

    elif trust_score >= 80:

        recruiter_verdict = (
            "Strong supporting evidence. "
            "The candidate's profile is well "
            "supported by the available evidence."
        )

    elif trust_score >= 70:

        recruiter_verdict = (
            "Good supporting evidence. "
            "Minor manual verification is recommended."
        )

    elif trust_score >= 60:

        recruiter_verdict = (
            "Moderate supporting evidence. "
            "Manual verification is recommended."
        )

    else:

        recruiter_verdict = (
            "Limited supporting evidence. "
            "Additional verification is recommended."
        )

    # ========================================================
    # 9. SCORE VALIDATION
    # ========================================================

    breakdown["total"] = (
        breakdown["claim_evidence"]
        + breakdown["rag_verification"]
        + breakdown["identity_verification"]
        + breakdown["github_quality"]
        + breakdown["linkedin_verification"]
    )

    # Safety check
    breakdown["total"] = max(
        0,
        min(
            100,
            breakdown["total"],
        ),
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {
        "trust_score": trust_score,
        "risk_level": risk_level,
        "recruiter_verdict": recruiter_verdict,
        "score_breakdown": breakdown,
    }
