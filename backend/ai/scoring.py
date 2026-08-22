def calculate_trust_score(
    identity: dict,
    github_evidence: dict,
) -> dict:

    score = 40

    github_match = bool(
        identity.get("github_match", False)
    )

    linkedin_match = bool(
        identity.get("linkedin_match", False)
    )

    github_found = bool(
        github_evidence.get("profile_found", False)
    )

    repository_count = int(
        github_evidence.get(
            "repository_count",
            0,
        )
        or 0
    )

    # ----------------------------------------------
    # Identity evidence
    # ----------------------------------------------

    if linkedin_match:
        score += 30

    if github_match:
        score += 20

    # ----------------------------------------------
    # GitHub technical evidence
    # ----------------------------------------------

    if github_found:
        score += 5

    if repository_count >= 3:
        score += 5

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    # ----------------------------------------------
    # Risk
    # ----------------------------------------------

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
    }