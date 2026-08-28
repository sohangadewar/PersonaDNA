# ============================================================
# PersonaDNA - Trust Scoring Engine
# ============================================================


def clamp_score(score: float) -> int:
    return max(0, min(100, round(score)))


def safe_confidence(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


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

    score = 0.0
    breakdown = {}

    # ========================================================
    # 1. CLAIM EVIDENCE - 40 POINTS
    #
    # Measures actual source coverage.
    #
    # IMPORTANT:
    # - Resume presence alone does NOT mean verified.
    # - GitHub / LinkedIn provide independent corroboration.
    # - RAG is NOT counted here.
    # - Claim status is NOT counted here.
    #
    # This prevents double-counting.
    # ========================================================

    claim_score = 0.0

    if claims:

        claim_points = 0.0

        print("\n========== CLAIM SCORING DEBUG ==========")

        for claim in claims:

            evidence = claim.get("evidence", {})

            if not isinstance(evidence, dict):
                evidence = {}

            claim_type = str(
                claim.get("type", "skill")
            ).strip().lower()

            resume_supported = (
                evidence.get("resume", False) is True
            )

            github_supported = (
                evidence.get("github", False) is True
            )

            linkedin_supported = (
                evidence.get("linkedin", False) is True
            )

            # ------------------------------------------------
            # Source weights
            #
            # These weights describe source coverage only.
            # They are NOT probability of truth.
            # ------------------------------------------------

            if claim_type == "skill":

                resume_weight = 0.25
                github_weight = 0.45
                linkedin_weight = 0.30

            elif claim_type == "education":

                # GitHub is not an appropriate education
                # verification source.
                resume_weight = 0.60
                github_weight = 0.00
                linkedin_weight = 0.40

            elif claim_type == "certification":

                # GitHub is not an appropriate certification
                # verification source.
                resume_weight = 0.50
                github_weight = 0.00
                linkedin_weight = 0.50

            else:

                resume_weight = 0.25
                github_weight = 0.45
                linkedin_weight = 0.30

            source_strength = 0.0

            if resume_supported:
                source_strength += resume_weight

            if github_supported:
                source_strength += github_weight

            if linkedin_supported:
                source_strength += linkedin_weight

            source_strength = min(
                source_strength,
                1.0,
            )

            claim_points += source_strength

            print(
                "CLAIM:",
                claim.get("claim"),
                "| type:",
                claim_type,
                "| source_strength:",
                round(source_strength, 2),
                "| resume:",
                resume_supported,
                "| github:",
                github_supported,
                "| linkedin:",
                linkedin_supported,
            )

        claim_ratio = (
            claim_points / len(claims)
        )

        claim_score = min(
            claim_ratio * 40,
            40,
        )

        print("-----------------------------------------")

        print(
            "Claim source points:",
            round(claim_points, 2),
        )

        print(
            "Total claims:",
            len(claims),
        )

        print(
            "Claim source ratio:",
            round(claim_ratio, 3),
        )

        print(
            "Claim evidence score:",
            round(claim_score, 2),
        )

        print(
            "========================================="
        )

    score += claim_score

    breakdown["claim_evidence"] = round(
        claim_score
    )

    # ========================================================
    # 2. RAG VERIFICATION - 20 POINTS
    #
    # Measures RAG verification independently.
    #
    # needs_review = 0
    #
    # Confidence alone does NOT turn an unverified claim
    # into verified evidence.
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

    rag_score = 0.0

    if rag_claims:

        rag_points = 0.0

        print(
            "\n========== RAG SCORING DEBUG =========="
        )

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

            # ------------------------------------------------
            # Fully verified
            # ------------------------------------------------

            if status in verified_statuses:

                if confidence >= 80:
                    points = 1.00

                elif confidence >= 60:
                    points = 0.85

                elif confidence >= 40:
                    points = 0.70

                else:
                    points = 0.50

            # ------------------------------------------------
            # Partially verified
            # ------------------------------------------------

            elif status in partially_supported_statuses:

                if confidence >= 80:
                    points = 0.75

                elif confidence >= 60:
                    points = 0.60

                elif confidence >= 50:
                    points = 0.50

                else:
                    points = 0.25

            # ------------------------------------------------
            # Needs review
            #
            # IMPORTANT:
            # This is NOT verification.
            # ------------------------------------------------

            elif status == "needs_review":

                points = 0.00

            # ------------------------------------------------
            # Unknown status
            # ------------------------------------------------

            else:

                points = 0.00

            rag_points += points

            print(
                "CLAIM:",
                claim.get("claim"),
                "| rag_status:",
                status,
                "| confidence:",
                confidence,
                "| points:",
                round(points, 3),
            )

        rag_score = min(
            (
                rag_points / len(rag_claims)
            ) * 20,
            20,
        )

        print(
            "--------------------------------------"
        )

        print(
            "RAG points:",
            round(rag_points, 3),
        )

        print(
            "RAG claims:",
            len(rag_claims),
        )

        print(
            "RAG score:",
            round(rag_score, 2),
        )

        print(
            "======================================"
        )

    else:

        # No RAG verification.
        rag_score = 0.0

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

    # --------------------------------------------------------
    # GitHub identity
    # --------------------------------------------------------

    if github_match:

        identity_score += 10

    elif github_found:

        identity_score += 5

    # --------------------------------------------------------
    # LinkedIn identity
    # --------------------------------------------------------

    if linkedin_authorized:

        if linkedin_match:

            identity_score += 10

        else:

            identity_score += 5

    else:

        # No LinkedIn authorization is not treated as
        # negative evidence.
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
    #
    # Measures quality/availability of the GitHub source.
    #
    # It does NOT directly verify every resume claim.
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

    # GitHub profile exists

    if github_found:

        github_score += 5

    # At least one repository

    if repositories:

        github_score += 5

    # Meaningful repository count

    if len(repositories) >= 3:

        github_score += 5

    # Technology evidence exists

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
    #
    # REMOVED FROM SCORE.
    #
    # GitHub quality and identity are already represented
    # above. Adding another bonus would double-count them.
    #
    # Field retained as 0 for API/frontend compatibility.
    # ========================================================

    strong_evidence = 0

    breakdown["strong_evidence_bonus"] = 0

    # ========================================================
    # FINAL SCORE
    #
    # Maximum:
    #
    # Claim Evidence       = 40
    # RAG Verification     = 20
    # Identity Verification = 20
    # GitHub Quality       = 20
    # Strong Evidence      =  0
    #
    # TOTAL                = 100
    # ========================================================

    trust_score = clamp_score(
        score
    )

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

    # ========================================================
    # FINAL DEBUG
    # ========================================================

    print(
        "\n========== PERSONADNA FINAL SCORE =========="
    )

    print(
        "Claim evidence:",
        round(claim_score),
        "/ 40",
    )

    print(
        "RAG verification:",
        round(rag_score),
        "/ 20",
    )

    print(
        "Identity verification:",
        identity_score,
        "/ 20",
    )

    print(
        "GitHub quality:",
        github_score,
        "/ 20",
    )

    print(
        "Strong evidence bonus:",
        strong_evidence,
        "/ 0",
    )

    print(
        "--------------------------------------------"
    )

    print(
        "RAW SCORE:",
        round(score, 2),
    )

    print(
        "FINAL TRUST SCORE:",
        trust_score,
        "/ 100",
    )

    print(
        "RISK LEVEL:",
        risk_level,
    )

    print(
        "============================================"
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "trust_score": trust_score,
        "risk_level": risk_level,
        "recruiter_verdict": recruiter_verdict,
        "score_breakdown": breakdown,
    }