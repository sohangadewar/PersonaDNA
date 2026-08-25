from ai.rag_engine import verify_claim_with_rag
import json

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

def build_candidate_knowledge(
    resume_text: str,
    claims: list,
    github_evidence: dict,
    linkedin_evidence: dict,
    candidate_intelligence: dict,
    skill_repository_mapping: dict,
    project_repository_mapping: dict,
    identity: dict,
) -> str:
    """
    Combine everything known about a candidate into one plain-text
    knowledge document for retrieval / grounding.
    """
 
    sections = []
 
    # ---------------- Resume ----------------
    sections.append("===== RESUME TEXT =====")
    sections.append((resume_text or "").strip())
 
    # ---------------- Identity ----------------
    sections.append("\n===== IDENTITY =====")
    sections.append(_safe_json(identity))
 
    # ---------------- Claims ----------------
    sections.append("\n===== EXTRACTED CLAIMS =====")
    if claims:
        for i, claim in enumerate(claims, start=1):
            claim_text = claim.get("claim", "") if isinstance(claim, dict) else str(claim)
            status = claim.get("rag_status", "unverified") if isinstance(claim, dict) else "unverified"
            sections.append(f"{i}. \"{claim_text}\" — status: {status}")
    else:
        sections.append("No claims were extracted from the resume.")
 
    # ---------------- GitHub evidence ----------------
    sections.append("\n===== GITHUB EVIDENCE =====")
    sections.append(_safe_json(github_evidence))
 
    # ---------------- LinkedIn evidence ----------------
    sections.append("\n===== LINKEDIN EVIDENCE =====")
    sections.append(_safe_json(linkedin_evidence))
 
    # ---------------- Candidate intelligence ----------------
    sections.append("\n===== CANDIDATE INTELLIGENCE =====")
    sections.append(_safe_json(candidate_intelligence))
 
    # ---------------- Skill -> repository mapping ----------------
    sections.append("\n===== SKILL TO REPOSITORY MAPPING =====")
    sections.append(_safe_json(skill_repository_mapping))
 
    # ---------------- Project -> repository mapping ----------------
    sections.append("\n===== PROJECT TO REPOSITORY MAPPING =====")
    sections.append(_safe_json(project_repository_mapping))
 
    return "\n".join(sections)
 
 
# ============================================================
# RECRUITER PROMPT BUILDER
# ============================================================
 
def build_recruiter_prompt(question: str, candidate_knowledge: str) -> str:
    """
    Wrap a recruiter's free-text question together with the candidate's
    knowledge document into a single prompt for an LLM to answer, using
    only the supplied evidence.
    """
 
    return (
        "You are PersonaDNA's recruiting assistant. Answer the recruiter's "
        "question using ONLY the candidate information provided below. "
        "If the evidence does not support a clear answer, say so explicitly "
        "instead of guessing.\n\n"
        "===== CANDIDATE KNOWLEDGE =====\n"
        f"{candidate_knowledge}\n\n"
        "===== RECRUITER QUESTION =====\n"
        f"{question}\n\n"
        "===== ANSWER =====\n"
    )
 
 
# ============================================================
# HELPERS
# ============================================================
 
def _safe_json(value) -> str:
    """
    Safely pretty-print a dict/list as JSON text for inclusion in the
    knowledge document. Falls back to str() if it isn't serializable.
    """
 
    try:
        return json.dumps(value, indent=2, default=str)
    except (TypeError, ValueError):
        return str(value)
    
def build_candidate_intelligence(
    claims,
    github_evidence,
    identity,
    resume_text,
):
    """
    Build a candidate intelligence summary from
    resume claims, GitHub evidence, and identity.
    """

    claims = claims or []
    github_evidence = github_evidence or {}
    identity = identity or {}
    resume_text = resume_text or ""

    suspicious_claims = detect_suspicious_claims(
        claims=claims,
        identity=identity,
        github_evidence=github_evidence,
    )

    claim_evidence = []

    for claim in claims:

        if not isinstance(claim, dict):
            continue

        if claim.get("type") != "skill":
            continue

        evidence = claim.get(
            "evidence",
            {},
        )

        evidence_result = calculate_evidence_strength(
            claim=claim,
            github_evidence=github_evidence,
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
                "score": evidence_result["score"],
                "strength": evidence_result["strength"],
                "sources": evidence_result["sources"],
            }
        )

    total_claims = len(claim_evidence)

    if total_claims > 0:
        overall_evidence_score = round(
            sum(
                item["score"]
                for item in claim_evidence
            ) / total_claims
        )
    else:
        overall_evidence_score = 0

    if overall_evidence_score >= 80:
        evidence_level = "strong"

    elif overall_evidence_score >= 50:
        evidence_level = "moderate"

    elif overall_evidence_score > 0:
        evidence_level = "weak"

    else:
        evidence_level = "none"

    return {
        "overall_evidence_score": overall_evidence_score,
        "evidence_level": evidence_level,
        "claim_evidence": claim_evidence,
        "project_evidence": extract_project_evidence(
            claims
        ),
        "suspicious_claims": suspicious_claims,
        "suspicious_claim_count": len(
            suspicious_claims
        ),
    }