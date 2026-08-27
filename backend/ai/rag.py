

import json


# ============================================================
# CANDIDATE KNOWLEDGE BUILDER
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
