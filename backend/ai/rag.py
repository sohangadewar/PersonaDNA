
"""
PersonaDNA - RAG Knowledge Layer
================================

This module builds a structured candidate knowledge base for
PersonaDNA.

Responsibilities
----------------
1. Build a consolidated candidate knowledge document.
2. Combine resume, claims, GitHub, LinkedIn, identity,
   candidate intelligence and repository mappings.
3. Provide recruiter-oriented prompt construction.
4. Keep claim verification itself inside rag_engine.py.

This module is intentionally lightweight and deterministic.
It does NOT call Gemini or any external LLM.

The knowledge generated here can later be supplied to an LLM
for recruiter-facing candidate insights.
"""

from __future__ import annotations

from typing import Any


# ============================================================
# HELPERS
# ============================================================


def _safe_string(value: Any) -> str:
    """
    Safely convert arbitrary values into strings.
    """
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def _safe_list(value: Any) -> list:
    """
    Return a value as a list whenever possible.
    """
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def _format_value(value: Any) -> str:
    """
    Convert nested values into readable text.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, (int, float, bool)):
        return str(value)

    if isinstance(value, list):

        parts = []

        for item in value:

            formatted = _format_value(item)

            if formatted:
                parts.append(formatted)

        return ", ".join(parts)

    if isinstance(value, dict):

        parts = []

        for key, item in value.items():

            formatted = _format_value(item)

            if formatted:
                parts.append(
                    f"{key}: {formatted}"
                )

        return "; ".join(parts)

    return str(value)


def _section(
    title: str,
    content: str,
) -> str:
    """
    Create a consistently formatted knowledge section.
    """

    content = content.strip()

    if not content:
        content = "No verified information available."

    return (
        f"\n{'=' * 70}\n"
        f"{title}\n"
        f"{'=' * 70}\n"
        f"{content}\n"
    )


# ============================================================
# CLAIM KNOWLEDGE
# ============================================================


def _build_claim_knowledge(
    claims: list,
) -> str:
    """
    Convert extracted claims into recruiter-readable knowledge.
    """

    if not claims:
        return "No claims were extracted from the resume."

    lines = []

    for index, claim in enumerate(
        claims,
        start=1,
    ):

        if not isinstance(claim, dict):

            lines.append(
                f"{index}. {_safe_string(claim)}"
            )

            continue

        claim_name = _safe_string(
            claim.get("claim", "")
        )

        claim_type = _safe_string(
            claim.get("type", "")
        )

        if not claim_name:
            continue

        line = (
            f"{index}. {claim_name}"
        )

        if claim_type:
            line += f" | Type: {claim_type}"

        # Evidence fields
        github_supported = claim.get(
            "github_supported"
        )

        linkedin_supported = claim.get(
            "linkedin_supported"
        )

        if github_supported is not None:
            line += (
                f" | GitHub supported: "
                f"{github_supported}"
            )

        if linkedin_supported is not None:
            line += (
                f" | LinkedIn supported: "
                f"{linkedin_supported}"
            )

        # RAG verification
        rag_status = _safe_string(
            claim.get(
                "rag_status",
                "",
            )
        )

        rag_confidence = claim.get(
            "rag_confidence"
        )

        if rag_status:
            line += (
                f" | RAG status: "
                f"{rag_status}"
            )

        if rag_confidence is not None:
            line += (
                f" | RAG confidence: "
                f"{rag_confidence}%"
            )

        rag_sources = claim.get(
            "rag_sources",
            [],
        )

        if rag_sources:
            line += (
                f" | Sources: "
                f"{_format_value(rag_sources)}"
            )

        lines.append(line)

    return "\n".join(lines)


# ============================================================
# GITHUB KNOWLEDGE
# ============================================================


def _build_github_knowledge(
    github_evidence: dict,
) -> str:
    """
    Convert GitHub evidence into structured knowledge.
    """

    if not isinstance(
        github_evidence,
        dict,
    ):

        return (
            "No GitHub evidence was provided."
        )

    lines = []

    profile_found = github_evidence.get(
        "profile_found",
        False,
    )

    lines.append(
        f"Profile verified: {profile_found}"
    )

    username = (
        github_evidence.get("username")
        or github_evidence.get("login")
        or ""
    )

    if username:
        lines.append(
            f"Username: {_safe_string(username)}"
        )

    display_name = github_evidence.get(
        "display_name",
        "",
    )

    if display_name:
        lines.append(
            f"Display name: {_safe_string(display_name)}"
        )

    repository_count = github_evidence.get(
        "repository_count",
        0,
    )

    lines.append(
        f"Public repositories: {repository_count}"
    )

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if repositories:

        lines.append("")
        lines.append("Repositories:")

        for repository in repositories:

            if isinstance(
                repository,
                dict,
            ):

                name = _safe_string(
                    repository.get(
                        "name",
                        "",
                    )
                )

                description = _safe_string(
                    repository.get(
                        "description",
                        "",
                    )
                )

                language = _safe_string(
                    repository.get(
                        "language",
                        "",
                    )
                )

                technologies = repository.get(
                    "technologies",
                    [],
                )

                line = (
                    f"- {name}"
                    if name
                    else "- Repository"
                )

                if language:
                    line += (
                        f" | Language: {language}"
                    )

                if technologies:
                    line += (
                        f" | Technologies: "
                        f"{_format_value(technologies)}"
                    )

                if description:
                    line += (
                        f" | Description: "
                        f"{description}"
                    )

                lines.append(line)

            else:

                lines.append(
                    f"- {_safe_string(repository)}"
                )

    technologies = github_evidence.get(
        "technology_evidence",
        [],
    )

    if technologies:

        lines.append("")
        lines.append(
            "Technology evidence:"
        )

        for technology in technologies:

            formatted = _format_value(
                technology
            )

            if formatted:
                lines.append(
                    f"- {formatted}"
                )

    skills = github_evidence.get(
        "skill_evidence",
        [],
    )

    if skills:

        lines.append("")
        lines.append(
            "Skill evidence:"
        )

        for skill in skills:

            formatted = _format_value(
                skill
            )

            if formatted:
                lines.append(
                    f"- {formatted}"
                )

    return "\n".join(lines)


# ============================================================
# LINKEDIN KNOWLEDGE
# ============================================================


def _build_linkedin_knowledge(
    linkedin_evidence: dict,
) -> str:
    """
    Convert LinkedIn evidence into structured knowledge.
    """

    if not isinstance(
        linkedin_evidence,
        dict,
    ):

        return (
            "No LinkedIn evidence was provided."
        )

    lines = []

    authorized = linkedin_evidence.get(
        "authorized_source",
        False,
    )

    lines.append(
        f"Authorized LinkedIn evidence: "
        f"{authorized}"
    )

    display_name = linkedin_evidence.get(
        "display_name",
        "",
    )

    if display_name:
        lines.append(
            f"Display name: "
            f"{_safe_string(display_name)}"
        )

    headline = linkedin_evidence.get(
        "headline",
        "",
    )

    if headline:
        lines.append(
            f"Headline: "
            f"{_safe_string(headline)}"
        )

    about = (
        linkedin_evidence.get("about")
        or linkedin_evidence.get("summary")
        or ""
    )

    if about:
        lines.append(
            f"About: {_safe_string(about)}"
        )

    skills = linkedin_evidence.get(
        "skills",
        [],
    )

    if skills:

        lines.append("")
        lines.append("Skills:")

        for skill in skills:

            formatted = _format_value(
                skill
            )

            if formatted:
                lines.append(
                    f"- {formatted}"
                )

    experience = linkedin_evidence.get(
        "experience",
        [],
    )

    if experience:

        lines.append("")
        lines.append("Experience:")

        for item in experience:

            formatted = _format_value(
                item
            )

            if formatted:
                lines.append(
                    f"- {formatted}"
                )

    education = linkedin_evidence.get(
        "education",
        [],
    )

    if education:

        lines.append("")
        lines.append("Education:")

        for item in education:

            formatted = _format_value(
                item
            )

            if formatted:
                lines.append(
                    f"- {formatted}"
                )

    return "\n".join(lines)


# ============================================================
# IDENTITY KNOWLEDGE
# ============================================================


def _build_identity_knowledge(
    identity: dict,
) -> str:
    """
    Convert identity verification into knowledge.
    """

    if not isinstance(
        identity,
        dict,
    ):

        return (
            "Identity verification data "
            "is unavailable."
        )

    lines = []

    resume_name = _safe_string(
        identity.get(
            "resume_name",
            "",
        )
    )

    if resume_name:
        lines.append(
            f"Resume identity: {resume_name}"
        )

    github_username = _safe_string(
        identity.get(
            "github_username",
            "",
        )
    )

    if github_username:
        lines.append(
            f"GitHub identity: "
            f"{github_username}"
        )

    github_match = identity.get(
        "github_match"
    )

    if github_match is not None:
        lines.append(
            f"GitHub identity match: "
            f"{github_match}"
        )

    linkedin_username = _safe_string(
        identity.get(
            "linkedin_username",
            "",
        )
    )

    if linkedin_username:
        lines.append(
            f"LinkedIn identity: "
            f"{linkedin_username}"
        )

    linkedin_match = identity.get(
        "linkedin_match"
    )

    if linkedin_match is not None:
        lines.append(
            f"LinkedIn identity match: "
            f"{linkedin_match}"
        )

    return "\n".join(lines)


# ============================================================
# CANDIDATE INTELLIGENCE
# ============================================================


def _build_intelligence_knowledge(
    candidate_intelligence: dict,
) -> str:
    """
    Convert candidate intelligence into readable knowledge.
    """

    if not isinstance(
        candidate_intelligence,
        dict,
    ):

        return (
            "Candidate intelligence is unavailable."
        )

    lines = []

    for key, value in candidate_intelligence.items():

        formatted = _format_value(value)

        if not formatted:
            continue

        readable_key = str(
            key
        ).replace(
            "_",
            " ",
        ).title()

        lines.append(
            f"{readable_key}: {formatted}"
        )

    return "\n".join(lines)


# ============================================================
# REPOSITORY MAPPINGS
# ============================================================


def _build_mapping_knowledge(
    title: str,
    mapping: Any,
) -> str:
    """
    Convert skill/project repository mappings into knowledge.
    """

    if not mapping:
        return (
            f"No {title.lower()} available."
        )

    lines = []

    for item in _safe_list(mapping):

        if isinstance(
            item,
            dict,
        ):

            formatted_parts = []

            for key, value in item.items():

                formatted = _format_value(
                    value
                )

                if formatted:
                    readable_key = str(
                        key
                    ).replace(
                        "_",
                        " ",
                    ).title()

                    formatted_parts.append(
                        f"{readable_key}: "
                        f"{formatted}"
                    )

            if formatted_parts:

                lines.append(
                    "- "
                    + " | ".join(
                        formatted_parts
                    )
                )

        else:

            formatted = _format_value(
                item
            )

            if formatted:
                lines.append(
                    f"- {formatted}"
                )

    return "\n".join(lines)


# ============================================================
# CANDIDATE KNOWLEDGE
# ============================================================


def build_candidate_knowledge(
    resume_text: str = "",
    claims: list | None = None,
    github_evidence: dict | None = None,
    linkedin_evidence: dict | None = None,
    candidate_intelligence: dict | None = None,
    skill_repository_mapping: Any = None,
    project_repository_mapping: Any = None,
    identity: dict | None = None,
) -> str:
    """
    Build the complete candidate knowledge base.

    This is the primary function used by main.py.

    The output is deterministic text containing all available
    candidate evidence in a structured format.
    """

    claims = claims or []
    github_evidence = (
        github_evidence
        if isinstance(github_evidence, dict)
        else {}
    )
    linkedin_evidence = (
        linkedin_evidence
        if isinstance(linkedin_evidence, dict)
        else {}
    )
    candidate_intelligence = (
        candidate_intelligence
        if isinstance(candidate_intelligence, dict)
        else {}
    )
    identity = (
        identity
        if isinstance(identity, dict)
        else {}
    )

    resume_text = _safe_string(
        resume_text
    )

    sections = []

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    sections.append(
        "PERSONADNA CANDIDATE KNOWLEDGE BASE"
    )

    sections.append(
        "This knowledge base contains evidence "
        "collected from the candidate resume, "
        "GitHub, LinkedIn and PersonaDNA analysis."
    )

    # --------------------------------------------------------
    # Resume
    # --------------------------------------------------------

    resume_content = resume_text

    if len(resume_content) > 12000:
        resume_content = (
            resume_content[:12000]
            + "\n[Resume text truncated.]"
        )

    sections.append(
        _section(
            "RESUME",
            resume_content,
        )
    )

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    sections.append(
        _section(
            "IDENTITY VERIFICATION",
            _build_identity_knowledge(
                identity
            ),
        )
    )

    # --------------------------------------------------------
    # Claims
    # --------------------------------------------------------

    sections.append(
        _section(
            "EXTRACTED CLAIMS",
            _build_claim_knowledge(
                claims
            ),
        )
    )

    # --------------------------------------------------------
    # GitHub
    # --------------------------------------------------------

    sections.append(
        _section(
            "GITHUB EVIDENCE",
            _build_github_knowledge(
                github_evidence
            ),
        )
    )

    # --------------------------------------------------------
    # LinkedIn
    # --------------------------------------------------------

    sections.append(
        _section(
            "LINKEDIN EVIDENCE",
            _build_linkedin_knowledge(
                linkedin_evidence
            ),
        )
    )

    # --------------------------------------------------------
    # Candidate intelligence
    # --------------------------------------------------------

    sections.append(
        _section(
            "CANDIDATE INTELLIGENCE",
            _build_intelligence_knowledge(
                candidate_intelligence
            ),
        )
    )

    # --------------------------------------------------------
    # Skill → Repository
    # --------------------------------------------------------

    sections.append(
        _section(
            "SKILL → REPOSITORY MAPPING",
            _build_mapping_knowledge(
                "Skill repository mapping",
                skill_repository_mapping,
            ),
        )
    )

    # --------------------------------------------------------
    # Project → Repository
    # --------------------------------------------------------

    sections.append(
        _section(
            "PROJECT → REPOSITORY MAPPING",
            _build_mapping_knowledge(
                "Project repository mapping",
                project_repository_mapping,
            ),
        )
    )

    knowledge = "\n".join(
        sections
    ).strip()

    return knowledge


# ============================================================
# RECRUITER PROMPT
# ============================================================


def build_recruiter_prompt(
    candidate_knowledge: str,
    recruiter_question: str = "",
) -> str:
    """
    Build a recruiter-oriented prompt from the candidate
    knowledge base.

    This function does not call an LLM.
    It only constructs the prompt that can be supplied to
    Gemini or another model.
    """

    knowledge = _safe_string(
        candidate_knowledge
    )

    question = _safe_string(
        recruiter_question
    )

    if not question:
        question = (
            "Evaluate this candidate based only on "
            "the available evidence."
        )

    return f"""
You are PersonaDNA, an evidence-based candidate verification
assistant.

Your task is to help a recruiter evaluate a candidate using
ONLY the evidence contained in the candidate knowledge base.

Do not invent qualifications, experience, projects,
certifications, technologies or achievements.

Clearly distinguish between:

1. Verified evidence
2. Partially supported claims
3. Claims requiring review
4. Unsupported claims
5. Identity inconsistencies

When evidence is insufficient, explicitly say that the
available evidence is insufficient.

Do not treat a resume claim as independently verified merely
because it appears on the resume.

GitHub and authorized LinkedIn evidence should be treated as
supporting evidence, not automatic proof of every claim.

Recruiter question:
{question}

Candidate knowledge base:
------------------------------------------------------------
{knowledge}
------------------------------------------------------------

Provide a concise, evidence-based recruiter response.
""".strip()


# ============================================================
# COMPATIBILITY EXPORTS
# ============================================================

# The actual claim verification functions remain in
# rag_engine.py. These imports preserve compatibility for
# modules that may still import them from rag.py.

from .rag_engine import (
    normalize_text,
    tokenize,
    calculate_text_similarity,
    claim_matches,
    canonical_claim,
    claim_aliases,
    extract_github_text,
    extract_linkedin_text,
    find_best_text_evidence,
    find_github_structured_evidence,
    verify_claim_with_rag,
    verify_claims_with_rag,
)


__all__ = [
    # Knowledge layer
    "build_candidate_knowledge",
    "build_recruiter_prompt",

    # RAG engine compatibility
    "normalize_text",
    "tokenize",
    "calculate_text_similarity",
    "claim_matches",
    "canonical_claim",
    "claim_aliases",
    "extract_github_text",
    "extract_linkedin_text",
    "find_best_text_evidence",
    "find_github_structured_evidence",
    "verify_claim_with_rag",
    "verify_claims_with_rag",
]

