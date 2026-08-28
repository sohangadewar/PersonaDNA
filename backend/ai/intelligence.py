from backend.ai.evidence import  (
    build_repository_skill_mapping,
    calculate_evidence_strength,
    extract_project_evidence,
    detect_suspicious_claims,
)


def build_candidate_intelligence(
    claims: list[dict],
    github_evidence: dict,
) -> dict:

    # -------------------------------------------------
    # 1. Repository → Skill Mapping
    # -------------------------------------------------

    repository_skill_mapping = (
        build_repository_skill_mapping(
            claims,
            github_evidence,
        )
    )

    # -------------------------------------------------
    # 2. Evidence Strength
    # -------------------------------------------------

    evidence_strength = {}

    for claim in claims:

        if claim.get("type") != "skill":
            continue

        skill = str(
            claim.get("claim", "")
        )

        repository_matches = (
            repository_skill_mapping.get(
                skill,
                [],
            )
        )

        strength = (
            calculate_evidence_strength(
                claim,
                repository_matches,
                github_evidence,
            )
        )

        evidence_strength[skill] = strength

    # -------------------------------------------------
    # 3. Project Evidence
    # -------------------------------------------------

    project_evidence = (
        extract_project_evidence(
            claims,
            github_evidence,
        )
    )

    # -------------------------------------------------
    # 4. Suspicious Claims
    # -------------------------------------------------

    suspicious_claims = (
        detect_suspicious_claims(
            claims,
            repository_skill_mapping,
            evidence_strength,
        )
    )

    # -------------------------------------------------
    # 5. Coverage
    # -------------------------------------------------

    skill_claims = [
        claim
        for claim in claims
        if claim.get("type") == "skill"
    ]

    total_skills = len(skill_claims)

    strongly_supported = sum(
        1
        for strength in evidence_strength.values()
        if strength.get("score", 0) >= 80
    )

    moderately_supported = sum(
        1
        for strength in evidence_strength.values()
        if 60 <= strength.get("score", 0) < 80
    )

    if total_skills:

        evidence_coverage = round(
            (
                strongly_supported
                + moderately_supported
            )
            / total_skills
            * 100,
            2,
        )

    else:
        evidence_coverage = 0.0

    # -------------------------------------------------
    # Final intelligence report
    # -------------------------------------------------

    return {
        "evidence_strength": (
            evidence_strength
        ),

        "repository_skill_mapping": (
            repository_skill_mapping
        ),

        "project_evidence": (
            project_evidence
        ),

        "suspicious_claims": (
            suspicious_claims
        ),

        "evidence_coverage": (
            evidence_coverage
        ),

        "total_skill_claims": (
            total_skills
        ),

        "strongly_supported_skills": (
            strongly_supported
        ),

        "moderately_supported_skills": (
            moderately_supported
        ),
    }