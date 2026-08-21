def normalize_text(value) -> str:
    if value is None:
        return ""

    return str(
        value
    ).lower().strip()


# ============================================================
# Evidence strength
# ============================================================

def calculate_evidence_strength(
    claim,
    github_evidence,
):

    evidence = claim.get(
        "evidence",
        {},
    )

    score = 0
    sources = []

    if evidence.get(
        "resume",
        False,
    ):
        score += 20
        sources.append(
            "resume"
        )

    if evidence.get(
        "github",
        False,
    ):
        score += 40
        sources.append(
            "github"
        )

    if evidence.get(
        "linkedin",
        False,
    ):
        score += 40
        sources.append(
            "linkedin"
        )

    score = min(
        score,
        100,
    )

    if score >= 80:
        strength = "strong"

    elif score >= 50:
        strength = "moderate"

    elif score > 0:
        strength = "weak"

    else:
        strength = "none"

    return {
        "score": score,
        "strength": strength,
        "sources": sources,
    }


# ============================================================
# Project evidence
# ============================================================

def extract_project_evidence(
    claims,
) -> list[dict]:

    projects = []

    for claim in claims:

        if claim.get(
            "type"
        ) != "project":
            continue

        projects.append(
            {
                "project": claim.get(
                    "claim",
                    "",
                ),
                "resume_evidence": claim.get(
                    "project_text",
                    claim.get(
                        "claim",
                        "",
                    ),
                ),
                "technologies": claim.get(
                    "technologies",
                    [],
                ),
            }
        )

    return projects


# ============================================================
# Suspicious claims
# ============================================================

def detect_suspicious_claims(
    claims,
    identity,
    github_evidence,
):

    suspicious = []

    github_profile_found = bool(
        github_evidence.get(
            "profile_found",
            False,
        )
    )

    github_match = bool(
        identity.get(
            "github_match",
            False,
        )
    )

    for claim in claims:

        if claim.get(
            "type"
        ) != "skill":
            continue

        evidence = claim.get(
            "evidence",
            {},
        )

        github_claim = bool(
            evidence.get(
                "github",
                False,
            )
        )

        linkedin_claim = bool(
            evidence.get(
                "linkedin",
                False,
            )
        )

        reasons = []

        if (
            not github_claim
            and not linkedin_claim
        ):

            reasons.append(
                "No external evidence found for this skill."
            )

        if (
            github_profile_found
            and not github_match
        ):

            reasons.append(
                "GitHub identity does not match the resume identity."
            )

        if reasons:

            risk = "medium"

            if (
                not github_claim
                and github_profile_found
                and not github_match
            ):
                risk = "high"

            suspicious.append(
                {
                    "claim": claim.get(
                        "claim",
                        "",
                    ),
                    "type": "skill",
                    "reasons": reasons,
                    "risk": risk,
                }
            )

    return suspicious


# ============================================================
# Candidate intelligence
# ============================================================

def build_candidate_intelligence(
    claims,
    github_evidence,
    identity,
    resume_text,
):

    # --------------------------------------------------------
    # Claim evidence
    # --------------------------------------------------------

    claim_evidence = []

    for claim in claims:

        strength = calculate_evidence_strength(
            claim,
            github_evidence,
        )

        claim_evidence.append(
            {
                "claim": claim.get(
                    "claim",
                    "",
                ),
                "type": claim.get(
                    "type",
                    "",
                ),
                "score": strength[
                    "score"
                ],
                "strength": strength[
                    "strength"
                ],
                "sources": strength[
                    "sources"
                ],
            }
        )

    # --------------------------------------------------------
    # Overall score
    # --------------------------------------------------------

    if claim_evidence:

        overall_score = round(
            sum(
                item["score"]
                for item in claim_evidence
            )
            / len(
                claim_evidence
            )
        )

    else:

        overall_score = 0

    if overall_score >= 80:
        evidence_level = "strong"

    elif overall_score >= 50:
        evidence_level = "moderate"

    elif overall_score > 0:
        evidence_level = "weak"

    else:
        evidence_level = "insufficient"

    # --------------------------------------------------------
    # Project evidence
    # --------------------------------------------------------

    project_evidence = extract_project_evidence(
        claims
    )

    # --------------------------------------------------------
    # Suspicious claims
    # --------------------------------------------------------

    suspicious_claims = (
        detect_suspicious_claims(
            claims,
            identity,
            github_evidence,
        )
    )

    return {
        "overall_evidence_score": overall_score,
        "evidence_level": evidence_level,
        "claim_evidence": claim_evidence,
        "project_evidence": project_evidence,
        "suspicious_claims": suspicious_claims,
        "suspicious_claim_count": len(
            suspicious_claims
        ),
    }