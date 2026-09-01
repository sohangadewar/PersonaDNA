# PersonaDNA - Risk Engine


def clamp_score(score: int) -> int:
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0
    return max(0, min(100, score))


def classify_risk(score: int) -> str:
    """Classify claim risk: lower score = lower risk."""
    score = clamp_score(score)

    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def recommended_action(level: str) -> str:
    if level == "High":
        return (
            "Additional verification is recommended "
            "before relying on this claim."
        )

    if level == "Medium":
        return (
            "Review supporting project, portfolio, "
            "or technical evidence."
        )

    return "No immediate additional verification is required."


def _safe_bool(value) -> bool:
    """Avoid bool('false') incorrectly evaluating to True."""
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}

    return bool(value)


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def calculate_claim_risk(
    claim: dict,
    evidence: dict,
    identity: dict,
) -> dict:

    claim = claim if isinstance(claim, dict) else {}
    evidence = evidence if isinstance(evidence, dict) else {}
    identity = identity if isinstance(identity, dict) else {}

    claim_name = str(claim.get("claim", "")).strip()
    claim_type = str(claim.get("type", "")).strip().lower()

    evidence_score = clamp_score(
        _safe_int(evidence.get("score", 0))
    )

    evidence_level = str(
        evidence.get(
            "level",
            evidence.get("strength", "None"),
        )
    ).strip()

    github_repository_count = max(
        0,
        _safe_int(evidence.get("github_repository_count", 0)),
    )

    github_username = str(
        identity.get("github_username", "")
    ).strip()

    github_match = _safe_bool(
        identity.get("github_match", False)
    )

    linkedin_username = str(
        identity.get("linkedin_username", "")
    ).strip()

    linkedin_match = _safe_bool(
        identity.get("linkedin_match", False)
    )

    risk_score = 0
    reasons = []

    # ========================================================
    # 1. BASE RISK FROM EVIDENCE
    # ========================================================

    if evidence_score >= 80:
        risk_score = 10
        reasons.append("Strong external evidence supports the claim.")

    elif evidence_score >= 60:
        risk_score = 20
        reasons.append("Moderate external evidence supports the claim.")

    elif evidence_score >= 40:
        risk_score = 35
        reasons.append("Some external evidence supports the claim.")

    elif evidence_score >= 20:
        risk_score = 50
        reasons.append(
            "Only limited external evidence supports the claim."
        )

    else:
        risk_score = 65
        reasons.append("No supporting external evidence was found.")

    # ========================================================
    # 2. REPOSITORY SUPPORT
    # ========================================================

    if github_repository_count >= 3:
        risk_score -= 15
        reasons.append(
            "The claim is supported across multiple repositories."
        )

    elif github_repository_count == 2:
        risk_score -= 10
        reasons.append(
            "The claim is supported across multiple repositories."
        )

    elif github_repository_count == 1:
        risk_score -= 5
        reasons.append(
            "The claim has repository-level GitHub evidence."
        )

    # ========================================================
    # 3. IDENTITY ATTRIBUTION
    # ========================================================

    if (
        github_username
        and not github_match
        and github_repository_count > 0
    ):
        risk_score += 15
        reasons.append(
            "GitHub evidence exists, but the supplied GitHub identity "
            "does not match the resume identity."
        )

    elif (
        github_username
        and not github_match
        and github_repository_count == 0
    ):
        risk_score += 5
        reasons.append(
            "The supplied GitHub identity does not match "
            "the resume identity."
        )

    # LinkedIn is a secondary claim-level signal.
    if (
        linkedin_username
        and not linkedin_match
        and claim_type == "skill"
    ):
        risk_score += 3
        reasons.append(
            "The supplied LinkedIn identity does not match "
            "the resume identity."
        )

    # ========================================================
    # 4. CLAIM TYPE
    # ========================================================

    if claim_type in {"education", "certification"}:

        # Lack of supported verification should remain a review-level
        # issue rather than automatically becoming high risk.
        if evidence_score == 0:
            risk_score = 45
            reasons.append(
                "External education/certification verification "
                "is not available in the current system."
            )

    elif claim_type == "project":

        if github_repository_count == 0:
            # A project without repository evidence is high-risk.
            risk_score = max(risk_score, 80)
            reasons.append(
                "No supporting GitHub repository was matched "
                "to this project."
            )

        else:
            risk_score -= 10
            reasons.append(
                "A GitHub repository provides project evidence."
            )

    # ========================================================
    # 5. EVIDENCE SAFETY CAP
    #
    # Strong evidence must not become high risk solely because
    # of identity attribution.
    # ========================================================

    if (
        evidence_score >= 80
        and github_repository_count > 0
    ):
        risk_score = min(risk_score, 55)

    elif (
        evidence_score >= 40
        and github_repository_count > 0
    ):
        risk_score = min(risk_score, 65)

    # ========================================================
    # 6. FINAL
    # ========================================================

    risk_score = clamp_score(risk_score)
    risk_level = classify_risk(risk_score)

    return {
        "claim": claim_name,
        "type": claim_type,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "evidence_score": evidence_score,
        "evidence_level": evidence_level,
        "github_repository_count": github_repository_count,
        "reasons": reasons,
        "recommended_action": recommended_action(risk_level),
    }


# ============================================================
# BUILD RISK REPORT
# ============================================================

def build_risk_report(
    claims: list[dict],
    evidence_report: list[dict],
    identity: dict,
) -> list[dict]:

    claims = claims if isinstance(claims, list) else []
    evidence_report = (
        evidence_report if isinstance(evidence_report, list) else []
    )
    identity = identity if isinstance(identity, dict) else {}

    evidence_by_claim = {}

    for item in evidence_report:
        if not isinstance(item, dict):
            continue

        claim_key = str(item.get("claim", "")).strip().lower()

        if claim_key:
            evidence_by_claim[claim_key] = item

    report = []

    for claim in claims:
        if not isinstance(claim, dict):
            continue

        claim_name = str(claim.get("claim", "")).strip()

        # Only use evidence that actually exists in the
        # authoritative evidence report.
        evidence = evidence_by_claim.get(claim_name.lower())

        if evidence is None:
            evidence = {
                "score": 0,
                "level": "None",
                "github_repository_count": 0,
            }

        report.append(
            calculate_claim_risk(
                claim,
                evidence,
                identity,
            )
        )

    return report


# ============================================================
# SUMMARY
# ============================================================

def calculate_risk_summary(
    risk_report: list[dict],
) -> dict:

    risk_report = (
        risk_report if isinstance(risk_report, list) else []
    )

    low = sum(
        1
        for item in risk_report
        if item.get("risk_level") == "Low"
    )

    medium = sum(
        1
        for item in risk_report
        if item.get("risk_level") == "Medium"
    )

    high = sum(
        1
        for item in risk_report
        if item.get("risk_level") == "High"
    )

    if high > 0:
        overall = "High"
    elif medium > 0:
        overall = "Medium"
    else:
        overall = "Low"

    return {
        "overall_risk": overall,
        "total_claims": len(risk_report),
        "low_risk_claims": low,
        "medium_risk_claims": medium,
        "high_risk_claims": high,
    }
