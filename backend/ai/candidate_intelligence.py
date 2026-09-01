# ============================================================
# PersonaDNA - Candidate Intelligence Engine
# ============================================================

import json


# ============================================================
# Evidence Strength
# ============================================================

def calculate_evidence_strength(
    claim,
    github_evidence=None,
):
    """
    Calculate external/source coverage for a claim.

    IMPORTANT:
    This measures evidence coverage, NOT whether the claim
    is definitely true.

    Standard claims:
        Resume   = 20
        GitHub   = 40
        LinkedIn = 40

    Education / Certification:
        Resume   = 50
        LinkedIn = 50
    """

    claim = claim if isinstance(claim, dict) else {}

    evidence = claim.get("evidence", {})

    if not isinstance(evidence, dict):
        evidence = {}

    claim_type = str(
        claim.get("type", "skill")
    ).strip().lower()

    resume = evidence.get("resume") is True
    github = evidence.get("github") is True
    linkedin = evidence.get("linkedin") is True

    if claim_type in {
        "education",
        "certification",
    }:
        resume_weight = 50
        github_weight = 0
        linkedin_weight = 50
    else:
        resume_weight = 20
        github_weight = 40
        linkedin_weight = 40

    score = 0
    sources = []

    if resume:
        score += resume_weight
        sources.append("resume")

    if github:
        score += github_weight
        sources.append("github")

    if linkedin:
        score += linkedin_weight
        sources.append("linkedin")

    score = max(0, min(score, 100))

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
# Project Evidence
# ============================================================

def extract_project_evidence(
    claims,
) -> list[dict]:

    projects = []

    for claim in claims or []:

        if not isinstance(claim, dict):
            continue

        if str(
            claim.get("type", "")
        ).strip().lower() != "project":
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
                "status": claim.get(
                    "status",
                    claim.get(
                        "rag_status",
                        "needs_review",
                    ),
                ),
                "rag_confidence": claim.get(
                    "rag_confidence",
                    0,
                ),
            }
        )

    return projects


# ============================================================
# Suspicious Claims
# ============================================================

def detect_suspicious_claims(
    claims,
    identity,
    github_evidence,
):

    suspicious = []

    claims = claims or []
    identity = identity or {}
    github_evidence = github_evidence or {}

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

        if not isinstance(claim, dict):
            continue

        claim_type = str(
            claim.get(
                "type",
                "",
            )
        ).strip().lower()

        # ----------------------------------------------------
        # Suspicious detection currently focuses on skills.
        # ----------------------------------------------------

        if claim_type != "skill":
            continue

        # ----------------------------------------------------
        # IMPORTANT:
        # RAG / final status is authoritative.
        #
        # A supported claim must NEVER be marked suspicious.
        # ----------------------------------------------------

        final_status = str(
            claim.get(
                "status",
                claim.get(
                    "rag_status",
                    "needs_review",
                ),
            )
        ).strip().lower()

        if final_status == "supported":
            continue

        evidence = claim.get(
            "evidence",
            {},
        )

        if not isinstance(evidence, dict):
            evidence = {}

        github_claim = (
            evidence.get("github") is True
        )

        linkedin_claim = (
            evidence.get("linkedin") is True
        )

        reasons = []

        # ----------------------------------------------------
        # No external evidence
        # ----------------------------------------------------

        if (
            not github_claim
            and not linkedin_claim
        ):
            reasons.append(
                "No external evidence found for this skill."
            )

        # ----------------------------------------------------
        # GitHub identity mismatch
        #
        # Only report mismatch when GitHub actually provided
        # evidence for the claim.
        # ----------------------------------------------------

        if (
            github_profile_found
            and github_claim
            and not github_match
        ):
            reasons.append(
                "GitHub identity does not match "
                "the resume identity."
            )

        # ----------------------------------------------------
        # Create suspicious record only when an actual reason
        # exists.
        # ----------------------------------------------------

        if reasons:

            risk = "medium"

            if (
                github_profile_found
                and github_claim
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
                    "rag_status": final_status,
                    "rag_confidence": claim.get(
                        "rag_confidence",
                        0,
                    ),
                }
            )

    return suspicious


# ============================================================
# Candidate Intelligence
# ============================================================

def build_candidate_intelligence(
    claims,
    github_evidence,
    identity,
    resume_text,
):

    claims = claims or []
    github_evidence = github_evidence or {}
    identity = identity or {}
    resume_text = resume_text or ""

    # ========================================================
    # Suspicious claims
    # ========================================================

    suspicious_claims = detect_suspicious_claims(
        claims=claims,
        identity=identity,
        github_evidence=github_evidence,
    )

    # ========================================================
    # Claim evidence
    # ========================================================

    claim_evidence = []

    for claim in claims:

        if not isinstance(claim, dict):
            continue

        evidence_result = calculate_evidence_strength(
            claim=claim,
            github_evidence=github_evidence,
        )

        final_status = str(
            claim.get(
                "status",
                claim.get(
                    "rag_status",
                    "needs_review",
                ),
            )
        ).strip().lower()

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
                "score": evidence_result["score"],
                "strength": evidence_result["strength"],
                "sources": evidence_result["sources"],

                # Final verification result
                "status": final_status,

                # RAG information
                "rag_status": claim.get(
                    "rag_status",
                    final_status,
                ),
                "rag_confidence": claim.get(
                    "rag_confidence",
                    0,
                ),
            }
        )

    # ========================================================
    # Claim statistics
    # ========================================================

    total_claims = len(claim_evidence)

    verified_claims = sum(
        1
        for item in claim_evidence
        if item.get("status") == "supported"
    )

    needs_review_claims = sum(
        1
        for item in claim_evidence
        if item.get("status") == "needs_review"
    )

    contradicted_claims = sum(
        1
        for item in claim_evidence
        if item.get("status") == "contradicted"
    )

    # ========================================================
    # Evidence score
    # ========================================================

    if total_claims:

        overall_evidence_score = round(
            sum(
                item["score"]
                for item in claim_evidence
            )
            / total_claims
        )

    else:

        overall_evidence_score = 0

    # ========================================================
    # Evidence level
    # ========================================================

    if overall_evidence_score >= 80:
        evidence_level = "strong"

    elif overall_evidence_score >= 50:
        evidence_level = "moderate"

    elif overall_evidence_score > 0:
        evidence_level = "weak"

    else:
        evidence_level = "none"

    # ========================================================
    # Return intelligence
    # ========================================================

    return {
        "overall_evidence_score": overall_evidence_score,
        "evidence_level": evidence_level,

        "total_claims": total_claims,
        "verified_claims": verified_claims,
        "needs_review_claims": needs_review_claims,
        "contradicted_claims": contradicted_claims,

        "claim_evidence": claim_evidence,

        "project_evidence": extract_project_evidence(
            claims
        ),

        "suspicious_claims": suspicious_claims,

        "suspicious_claim_count": len(
            suspicious_claims
        ),
    }


# ============================================================
# Candidate Knowledge
# ============================================================

def build_candidate_knowledge(
    resume_text,
    claims,
    github_evidence,
    linkedin_evidence,
    candidate_intelligence,
    skill_repository_mapping,
    project_repository_mapping,
    identity,
    trust_score=None,
    ai_confidence=None,
    risk_level=None,
    recruiter_verdict=None,
):

    sections = []

    # ========================================================
    # OFFICIAL PERSONADNA SCORES
    # ========================================================

    sections.append(
        "===== OFFICIAL PERSONADNA SCORES ====="
    )

    if trust_score is not None:
        sections.append(
            f"Official PersonaDNA Trust Score: {trust_score}"
        )

    if ai_confidence is not None:
        sections.append(
            f"Official PersonaDNA AI Confidence: {ai_confidence}"
        )

    if risk_level:
        sections.append(
            f"Official PersonaDNA Risk Level: {risk_level}"
        )

    if recruiter_verdict:
        sections.append(
            f"Official PersonaDNA Recruiter Verdict: {recruiter_verdict}"
        )

    # ========================================================
    # CLAIM SUMMARY
    # ========================================================

    sections.append(
        "\n===== CLAIM SUMMARY ====="
    )

    if isinstance(candidate_intelligence, dict):

        sections.append(
            f"Total Claims: "
            f"{candidate_intelligence.get('total_claims', 0)}"
        )

        sections.append(
            f"Verified Claims: "
            f"{candidate_intelligence.get('verified_claims', 0)}"
        )

        sections.append(
            f"Claims Needing Review: "
            f"{candidate_intelligence.get('needs_review_claims', 0)}"
        )

        sections.append(
            f"Contradicted Claims: "
            f"{candidate_intelligence.get('contradicted_claims', 0)}"
        )

        sections.append(
            f"Suspicious Claims: "
            f"{candidate_intelligence.get('suspicious_claim_count', 0)}"
        )

        sections.append(
            f"Overall Evidence Score: "
            f"{candidate_intelligence.get('overall_evidence_score', 0)}"
        )

        sections.append(
            f"Evidence Level: "
            f"{candidate_intelligence.get('evidence_level', 'none')}"
        )

    # ========================================================
    # RESUME
    # ========================================================

    sections.append(
        "\n===== RESUME TEXT ====="
    )

    sections.append(
        (resume_text or "").strip()
    )

    # ========================================================
    # IDENTITY
    # ========================================================

    sections.append(
        "\n===== IDENTITY ====="
    )

    sections.append(
        _safe_json(identity)
    )

    # ========================================================
    # CLAIMS
    # ========================================================

    sections.append(
        "\n===== EXTRACTED CLAIMS ====="
    )

    if claims:

        for i, claim in enumerate(
            claims,
            start=1,
        ):

            if not isinstance(
                claim,
                dict,
            ):
                continue

            final_status = claim.get(
                "status",
                claim.get(
                    "rag_status",
                    "needs_review",
                ),
            )

            sections.append(
                f'{i}. "{claim.get("claim", "")}" '
                f'— status: {final_status} '
                f'— RAG confidence: '
                f'{claim.get("rag_confidence", 0)}'
            )

    else:

        sections.append(
            "No claims were extracted from the resume."
        )

    # ========================================================
    # GITHUB
    # ========================================================

    sections.append(
        "\n===== GITHUB EVIDENCE ====="
    )

    sections.append(
        _safe_json(github_evidence)
    )

    # ========================================================
    # LINKEDIN
    # ========================================================

    sections.append(
        "\n===== LINKEDIN EVIDENCE ====="
    )

    sections.append(
        _safe_json(linkedin_evidence)
    )

    # ========================================================
    # CANDIDATE INTELLIGENCE
    # ========================================================

    sections.append(
        "\n===== CANDIDATE INTELLIGENCE ====="
    )

    sections.append(
        _safe_json(candidate_intelligence)
    )

    # ========================================================
    # SKILL MAPPING
    # ========================================================

    sections.append(
        "\n===== SKILL TO REPOSITORY MAPPING ====="
    )

    sections.append(
        _safe_json(skill_repository_mapping)
    )

    # ========================================================
    # PROJECT MAPPING
    # ========================================================

    sections.append(
        "\n===== PROJECT TO REPOSITORY MAPPING ====="
    )

    sections.append(
        _safe_json(project_repository_mapping)
    )

    return "\n".join(sections)


# ============================================================
# Recruiter Prompt
# ============================================================

def build_recruiter_prompt(
    question,
    candidate_knowledge,
):

    return (
        "You are PersonaDNA's evidence-based recruiting assistant.\n\n"

        "Your job is to answer recruiter questions using ONLY "
        "the candidate evidence provided below.\n\n"

        "STRICT RULES:\n"
        "1. Never invent candidate information.\n"
        "2. Never assume that a resume claim is true merely "
        "because it appears on the resume.\n"
        "3. Treat status='supported' as externally supported.\n"
        "4. Treat status='needs_review' as unverified, NOT false.\n"
        "5. Treat status='contradicted' as conflicting evidence.\n"
        "6. Do not call a claim suspicious unless the evidence "
        "explicitly contains a risk signal.\n"
        "7. If evidence is insufficient, clearly say that "
        "additional verification is required.\n"
        "8. Do not make predictions about the candidate's "
        "future performance.\n"
        "9. Do not reinterpret or recalculate the official "
        "PersonaDNA Trust Score.\n"
        "10. Use the official PersonaDNA scores exactly as provided.\n\n"

        "IMPORTANT DATE RULE:\n"
        "Do not describe a date as suspicious, future-dated, "
        "incorrect, or anomalous unless PersonaDNA's evidence "
        "explicitly identifies it as a date anomaly.\n\n"

        "===== CANDIDATE KNOWLEDGE =====\n"
        f"{candidate_knowledge}\n\n"

        "===== RECRUITER QUESTION =====\n"
        f"{question}\n\n"

        "===== ANSWER =====\n"
    )


# ============================================================
# Safe JSON
# ============================================================

def _safe_json(value) -> str:

    try:

        return json.dumps(
            value,
            indent=2,
            default=str,
        )

    except (
        TypeError,
        ValueError,
    ):

        return str(value)