def calculate_trust_score(
    identity: dict,
    github_evidence: dict,
) -> dict:
    """
    MVP evidence-based scoring model.

    This is a prototype heuristic and is not a
    validated identity verification algorithm.
    """

    score = 100

    github_match = identity.get("github_match", False)
    linkedin_match = identity.get("linkedin_match", False)

    github_found = github_evidence.get("profile_found", False)
    repository_count = github_evidence.get("repository_count", 0)

    # --------------------------------------------------
    # Identity consistency
    # --------------------------------------------------

    if not github_match:
        score -= 30

    if not linkedin_match:
        score -= 30

    # --------------------------------------------------
    # GitHub evidence
    # --------------------------------------------------

    if github_found:
        score += 5

    if repository_count >= 3:
        score += 5

    # --------------------------------------------------
    # Keep score between 0 and 100
    # --------------------------------------------------

    score = max(0, min(100, score))

    # --------------------------------------------------
    # Risk classification
    # --------------------------------------------------

    if score >= 80:
        risk_level = "Low"
        recruiter_verdict = "Recommended for Technical Interview"

    elif score >= 60:
        risk_level = "Medium"
        recruiter_verdict = "Manual Verification Recommended"

    else:
        risk_level = "High"
        recruiter_verdict = "Verification Required Before Interview"

    return {
        "trust_score": score,
        "risk_level": risk_level,
        "recruiter_verdict": recruiter_verdict,
    }
