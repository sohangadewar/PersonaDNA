def calculate_trust_score(
    identity: dict,
    github_evidence: dict,
) -> dict:
    """
    Calculate PersonaDNA Trust Score.

    Score:
        Base evidence                    = 40
        LinkedIn identity match          = +30
        GitHub identity match            = +20
        Verified GitHub profile          = +5
        3+ public repositories           = +5

        Maximum = 100
    """

    score = 40

    linkedin_match = bool(
        identity.get(
            "linkedin_match",
            False,
        )
    )

    github_match = bool(
        identity.get(
            "github_match",
            False,
        )
    )

    github_found = bool(
        github_evidence.get(
            "profile_found",
            False,
        )
    )

    try:
        repository_count = int(
            github_evidence.get(
                "repository_count",
                github_evidence.get(
                    "public_repositories",
                    0,
                ),
            )
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        repository_count = 0

    # --------------------------------------------------------
    # Identity evidence
    # --------------------------------------------------------

    if linkedin_match:
        score += 30

    if github_match:
        score += 20

    # --------------------------------------------------------
    # GitHub evidence
    # --------------------------------------------------------

    if github_found:
        score += 5

    if repository_count >= 3:
        score += 5

    # --------------------------------------------------------
    # Limit
    # --------------------------------------------------------

    score = min(
        100,
        max(0, score),
    )

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    if score >= 80:

        risk_level = "Low"

        recruiter_verdict = (
            "Recommended for Technical Interview"
        )

    elif score >= 60:

        risk_level = "Medium"

        recruiter_verdict = (
            "Manual Verification Recommended"
        )

    else:

        risk_level = "High"

        recruiter_verdict = (
            "Verification Required Before Interview"
        )

    return {
        "trust_score": score,
        "risk_level": risk_level,
        "recruiter_verdict": recruiter_verdict,
        "score_breakdown": {
            "base_evidence": 40,
            "linkedin_identity": 30 if linkedin_match else 0,
            "github_identity": 20 if github_match else 0,
            "github_profile": 5 if github_found else 0,
            "repository_evidence": 5 if repository_count >= 3 else 0,
        },
    }