# ============================================================
# PersonaDNA - Risk Engine
# ============================================================


def clamp_score(score: int) -> int:
    return max(
        0,
        min(
            100,
            int(score),
        ),
    )


def classify_risk(
    score: int,
) -> str:

    if score >= 70:
        return "High"

    if score >= 40:
        return "Medium"

    return "Low"


def recommended_action(
    level: str,
) -> str:

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

    return (
        "No immediate additional verification "
        "is required."
    )


def calculate_claim_risk(
    claim: dict,
    evidence: dict,
    identity: dict,
) -> dict:

    claim_name = str(
        claim.get(
            "claim",
            "",
        )
    ).strip()

    claim_type = claim.get(
        "type",
        "",
    )

    evidence_score = int(
        evidence.get(
            "score",
            0,
        )
    )

    evidence_level = str(
        evidence.get(
            "level",
            "None",
        )
    )

    github_repository_count = int(
        evidence.get(
            "github_repository_count",
            0,
        )
    )

    github_username = str(
        identity.get(
            "github_username",
            "",
        )
    ).strip()

    github_match = bool(
        identity.get(
            "github_match",
            False,
        )
    )

    linkedin_username = str(
        identity.get(
            "linkedin_username",
            "",
        )
    ).strip()

    linkedin_match = bool(
        identity.get(
            "linkedin_match",
            False,
        )
    )

    risk_score = 0
    reasons = []

    # ========================================================
    # Base risk from evidence
    # ========================================================

    if evidence_score >= 80:

        risk_score = 10

        reasons.append(
            "Strong external evidence supports the claim."
        )

    elif evidence_score >= 60:

        risk_score = 20

        reasons.append(
            "Moderate external evidence supports the claim."
        )

    elif evidence_score >= 40:

        risk_score = 35

        reasons.append(
            "Some external evidence supports the claim."
        )

    elif evidence_score >= 20:

        risk_score = 50

        reasons.append(
            "Only limited external evidence supports the claim."
        )

    else:

        risk_score = 65

        reasons.append(
            "No supporting external evidence was found."
        )

    # ========================================================
    # Repository support
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
    # Identity attribution
    # ========================================================

    if (
        github_username
        and not github_match
        and github_repository_count > 0
    ):

        risk_score += 15

        reasons.append(
            "GitHub evidence exists, but the supplied "
            "GitHub identity does not match the resume identity."
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

    # LinkedIn is only a secondary signal until Step 5.
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
    # Claim type
    # ========================================================

    if claim_type in {
        "education",
        "certification",
    }:

        if evidence_score == 0:

            risk_score = 45

            reasons.append(
                "External education/certification verification "
                "is not available in the current system."
            )

    elif claim_type == "project":

        if github_repository_count == 0:

            risk_score = 50

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
    # Prevent strong evidence from becoming high risk
    # only because of identity attribution.
    # ========================================================

    if (
        evidence_score >= 80
        and github_repository_count > 0
    ):

        risk_score = min(
            risk_score,
            55,
        )

    elif (
        evidence_score >= 40
        and github_repository_count > 0
    ):

        risk_score = min(
            risk_score,
            65,
        )

    # ========================================================
    # Final
    # ========================================================

    risk_score = clamp_score(
        risk_score
    )

    risk_level = classify_risk(
        risk_score
    )

    return {
        "claim": claim_name,
        "type": claim_type,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "evidence_score": evidence_score,
        "evidence_level": evidence_level,
        "github_repository_count": github_repository_count,
        "reasons": reasons,
        "recommended_action": recommended_action(
            risk_level
        ),
    }


# ============================================================
# Build risk report
# ============================================================

def build_risk_report(
    claims: list[dict],
    evidence_report: list[dict],
    identity: dict,
) -> list[dict]:

    evidence_by_claim = {
        str(item.get("claim", "")).strip().lower(): item
        for item in evidence_report
    }

    report = []

    for claim in claims:

        claim_name = str(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        # Only use evidence that actually exists
        # in the authoritative report.
        evidence = evidence_by_claim.get(
            claim_name.lower()
        )

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
# Summary
# ============================================================

def calculate_risk_summary(
    risk_report: list[dict],
) -> dict:

    low = sum(
        1
        for item in risk_report
        if item.get(
            "risk_level"
        ) == "Low"
    )

    medium = sum(
        1
        for item in risk_report
        if item.get(
            "risk_level"
        ) == "Medium"
    )

    high = sum(
        1
        for item in risk_report
        if item.get(
            "risk_level"
        ) == "High"
    )

    if high > 0:
        overall = "High"

    elif medium > 0:
        overall = "Medium"

    else:
        overall = "Low"

    return {
        "overall_risk": overall,
        "total_claims": len(
            risk_report
        ),
        "low_risk_claims": low,
        "medium_risk_claims": medium,
        "high_risk_claims": high,
    }