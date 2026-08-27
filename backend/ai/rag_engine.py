"""
PersonaDNA RAG Engine

Responsible for verifying resume claims against:
1. Resume text
2. GitHub evidence
3. LinkedIn evidence

This module is intentionally lightweight so that it works
without requiring a separate vector database.

The main.py file expects:

    verify_claim_with_rag(
        claim=...,
        resume_text=...,
        github_evidence=...,
        linkedin_evidence=...
    )

and expects a dictionary containing:

    status
    confidence
    evidence
    sources
"""

import re
from typing import Any


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text: Any) -> str:
    """
    Convert arbitrary input into normalized searchable text.
    """

    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9+#.\- ]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def tokenize(text: str) -> set[str]:
    """
    Convert text into a set of useful tokens.
    """

    normalized = normalize_text(text)

    if not normalized:
        return set()

    return {
        token
        for token in normalized.split()
        if len(token) > 2
    }


def calculate_text_similarity(
    claim: str,
    evidence: str,
) -> float:
    """
    Simple lexical similarity.

    This is not an LLM hallucination-based score.
    It compares meaningful words from the claim with
    words found in the evidence.
    """

    claim_tokens = tokenize(claim)
    evidence_tokens = tokenize(evidence)

    if not claim_tokens or not evidence_tokens:
        return 0.0

    overlap = claim_tokens.intersection(
        evidence_tokens
    )

    score = len(overlap) / len(claim_tokens)

    return round(
        min(score, 1.0),
        2,
    )


# ============================================================
# EVIDENCE EXTRACTION
# ============================================================

def _safe_string(value: Any) -> str:
    """
    Safely convert values to strings.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value

    return str(value)


def extract_github_text(
    github_evidence: dict,
) -> str:
    """
    Convert GitHub evidence into searchable text.
    """

    if not isinstance(
        github_evidence,
        dict,
    ):
        return ""

    parts = []

    # Basic profile information

    for key in [
        "username",
        "login",
        "display_name",
        "name",
        "bio",
        "company",
        "location",
        "html_url",
    ]:

        value = github_evidence.get(key)

        if value:
            parts.append(
                _safe_string(value)
            )

    # Repository information

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if isinstance(
        repositories,
        list,
    ):

        for repository in repositories:

            if isinstance(
                repository,
                dict,
            ):

                for key in [
                    "name",
                    "description",
                    "language",
                    "topics",
                    "url",
                    "html_url",
                ]:

                    value = repository.get(
                        key
                    )

                    if isinstance(
                        value,
                        list,
                    ):

                        parts.extend(
                            _safe_string(item)
                            for item in value
                        )

                    elif value:

                        parts.append(
                            _safe_string(value)
                        )

            elif repository:

                parts.append(
                    _safe_string(repository)
                )

    # Technology evidence

    technology_evidence = (
        github_evidence.get(
            "technology_evidence",
            [],
        )
    )

    if isinstance(
        technology_evidence,
        list,
    ):

        for item in technology_evidence:

            if isinstance(
                item,
                dict,
            ):

                parts.extend(
                    _safe_string(value)
                    for value in item.values()
                    if value
                )

            elif item:

                parts.append(
                    _safe_string(item)
                )

    # Skill evidence

    skill_evidence = (
        github_evidence.get(
            "skill_evidence",
            [],
        )
    )

    if isinstance(
        skill_evidence,
        list,
    ):

        for item in skill_evidence:

            if isinstance(
                item,
                dict,
            ):

                parts.extend(
                    _safe_string(value)
                    for value in item.values()
                    if value
                )

            elif item:

                parts.append(
                    _safe_string(item)
                )

    return "\n".join(parts)


def extract_linkedin_text(
    linkedin_evidence: dict,
) -> str:
    """
    Convert LinkedIn evidence into searchable text.
    """

    if not isinstance(
        linkedin_evidence,
        dict,
    ):
        return ""

    parts = []

    # Basic profile information

    for key in [
        "display_name",
        "name",
        "first_name",
        "last_name",
        "headline",
        "summary",
        "about",
        "location",
        "industry",
        "profile_url",
        "linkedin_url",
    ]:

        value = linkedin_evidence.get(
            key
        )

        if value:
            parts.append(
                _safe_string(value)
            )

    # Skills

    skills = linkedin_evidence.get(
        "skills",
        [],
    )

    if isinstance(
        skills,
        list,
    ):

        for skill in skills:

            if isinstance(
                skill,
                dict,
            ):

                parts.extend(
                    _safe_string(value)
                    for value in skill.values()
                    if value
                )

            elif skill:

                parts.append(
                    _safe_string(skill)
                )

    # Experience

    experience = linkedin_evidence.get(
        "experience",
        [],
    )

    if isinstance(
        experience,
        list,
    ):

        for item in experience:

            if isinstance(
                item,
                dict,
            ):

                parts.extend(
                    _safe_string(value)
                    for value in item.values()
                    if value
                )

            elif item:

                parts.append(
                    _safe_string(item)
                )

    # Education

    education = linkedin_evidence.get(
        "education",
        [],
    )

    if isinstance(
        education,
        list,
    ):

        for item in education:

            if isinstance(
                item,
                dict,
            ):

                parts.extend(
                    _safe_string(value)
                    for value in item.values()
                    if value
                )

            elif item:

                parts.append(
                    _safe_string(item)
                )

    return "\n".join(parts)


# ============================================================
# EVIDENCE SEARCH
# ============================================================

def find_matching_evidence(
    claim: str,
    evidence_text: str,
    source_name: str,
    structured_evidence: dict | None = None,
) -> dict:
    """
    Find evidence supporting a claim.

    For GitHub, structured repository evidence is checked
    first. This avoids relying only on generic text similarity.
    """

    if structured_evidence is None:
        structured_evidence = {}

    claim_text = _safe_string(
        claim
    ).strip()

    # ========================================================
    # GITHUB STRUCTURED EVIDENCE
    # ========================================================

    if source_name == "github":

        target = normalize_text(
            claim_text
        )

        repositories = structured_evidence.get(
            "repositories",
            [],
        )

        if isinstance(
            repositories,
            list,
        ):

            matched_repositories = []

            for repository in repositories:

                if not isinstance(
                    repository,
                    dict,
                ):
                    continue

                evidence_types = []

                # ------------------------------------------------
                # Technologies
                # ------------------------------------------------

                technologies = repository.get(
                    "technologies",
                    [],
                )

                if isinstance(
                    technologies,
                    list,
                ):

                    for technology in technologies:

                        if normalize_text(
                            technology
                        ) == target:

                            evidence_types.append(
                                "technology"
                            )

                # ------------------------------------------------
                # Primary language
                # ------------------------------------------------

                language = repository.get(
                    "language",
                    "",
                )

                if language:

                    if normalize_text(
                        language
                    ) == target:

                        evidence_types.append(
                            "language"
                        )

                # ------------------------------------------------
                # Language statistics
                # ------------------------------------------------

                languages = repository.get(
                    "languages",
                    {},
                )

                if isinstance(
                    languages,
                    dict,
                ):

                    for language_name in languages.keys():

                        if normalize_text(
                            language_name
                        ) == target:

                            evidence_types.append(
                                "languages"
                            )

                if evidence_types:

                    matched_repositories.append(
                        {
                            "name": repository.get(
                                "name",
                                "",
                            ),
                            "evidence_types": sorted(
                                set(
                                    evidence_types
                                )
                            ),
                        }
                    )

            # ----------------------------------------------------
            # Strong structured GitHub match
            # ----------------------------------------------------

            if matched_repositories:

                evidence_lines = []

                for repository in matched_repositories:

                    repository_name = repository.get(
                        "name",
                        "",
                    )

                    evidence_types = repository.get(
                        "evidence_types",
                        [],
                    )

                    evidence_lines.append(
                        (
                            f"GitHub repository "
                            f"'{repository_name}' "
                            f"contains evidence for "
                            f"'{claim_text}' through "
                            f"{', '.join(evidence_types)}."
                        )
                    )

                return {
                    "source": "github",
                    "matched": True,
                    "confidence": 95,
                    "evidence": " ".join(
                        evidence_lines
                    )[:500],
                    "repositories": [
                        item.get(
                            "name",
                            "",
                        )
                        for item in matched_repositories
                    ],
                }

    # ========================================================
    # GENERIC TEXT EVIDENCE
    # ========================================================

    if not evidence_text.strip():

        return {
            "source": source_name,
            "matched": False,
            "confidence": 0,
            "evidence": "",
        }

    similarity = calculate_text_similarity(
        claim_text,
        evidence_text,
    )

    matched = similarity >= 0.35

    evidence = ""

    if matched:

        claim_tokens = tokenize(
            claim_text
        )

        sentences = re.split(
            r"[.!?\n]+",
            evidence_text,
        )

        best_sentence = ""
        best_score = 0.0

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            sentence_tokens = tokenize(
                sentence
            )

            if not sentence_tokens:
                continue

            overlap = (
                claim_tokens.intersection(
                    sentence_tokens
                )
            )

            sentence_score = (
                len(overlap)
                / max(
                    len(claim_tokens),
                    1,
                )
            )

            if sentence_score > best_score:

                best_score = sentence_score
                best_sentence = sentence

        evidence = best_sentence[:500]

    return {
        "source": source_name,
        "matched": matched,
        "confidence": round(
            similarity * 100
        ),
        "evidence": evidence,
    }

# ============================================================
# MAIN RAG VERIFICATION
# ============================================================

def verify_claim_with_rag(
    claim: str,
    resume_text: str = "",
    github_evidence: dict | None = None,
    linkedin_evidence: dict | None = None,
) -> dict:
    """
    Verify a candidate claim against available evidence.

    Returns:

    {
        "status": "supported",
        "confidence": 85,
        "evidence": [...],
        "sources": [...]
    }

    Possible statuses:

    supported
    partially_supported
    needs_review
    unsupported
    """

    if not claim:

        return {
            "status": "needs_review",
            "confidence": 0,
            "evidence": [],
            "sources": [],
        }

    if github_evidence is None:
        github_evidence = {}

    if linkedin_evidence is None:
        linkedin_evidence = {}

    claim_text = _safe_string(
        claim
    ).strip()

    # --------------------------------------------------------
    # Resume
    # --------------------------------------------------------

    resume_result = find_matching_evidence(
        claim=claim_text,
        evidence_text=resume_text,
        source_name="resume",
    )

    # --------------------------------------------------------
    # GitHub
    # --------------------------------------------------------

    github_text = extract_github_text(
        github_evidence
    )

    github_result = find_matching_evidence(
    claim=claim_text,
    evidence_text=github_text,
    source_name="github",
    structured_evidence=github_evidence,
)

    # --------------------------------------------------------
    # LinkedIn
    # --------------------------------------------------------

    linkedin_text = extract_linkedin_text(
        linkedin_evidence
    )

    linkedin_result = find_matching_evidence(
        claim=claim_text,
        evidence_text=linkedin_text,
        source_name="linkedin",
    )

    results = [
        resume_result,
        github_result,
        linkedin_result,
    ]

    matched_results = [
        result
        for result in results
        if result["matched"]
    ]

    # ========================================================
    # NO EXTERNAL SUPPORT
    # ========================================================

    external_matches = [
        result
        for result in [
            github_result,
            linkedin_result,
        ]
        if result["matched"]
    ]

    # ========================================================
    # STRONG SUPPORT
    # ========================================================

    if len(external_matches) >= 2:

        confidence = max(
            result["confidence"]
            for result in external_matches
        )

        evidence = [
            {
                "source": result["source"],
                "text": result["evidence"],
                "confidence": result[
                    "confidence"
                ],
            }
            for result in external_matches
            if result["evidence"]
        ]

        sources = [
            result["source"]
            for result in external_matches
        ]

        return {
            "status": "supported",
            "confidence": min(
                100,
                max(
                    confidence,
                    85,
                ),
            ),
            "evidence": evidence,
            "sources": sources,
        }

    # ========================================================
    # ONE EXTERNAL SOURCE
    # ========================================================

    if len(external_matches) == 1:

        result = external_matches[0]

        confidence = result[
            "confidence"
        ]

        evidence = []

        if result["evidence"]:

            evidence.append(
                {
                    "source": result[
                        "source"
                    ],
                    "text": result[
                        "evidence"
                    ],
                    "confidence": confidence,
                }
            )

        return {
            "status": (
                "partially_supported"
            ),
            "confidence": max(
                50,
                min(
                    confidence,
                    85,
                ),
            ),
            "evidence": evidence,
            "sources": [
                result["source"]
            ],
        }

    # ========================================================
    # RESUME ONLY
    # ========================================================

    if resume_result["matched"]:

        return {
            "status": "needs_review",
            "confidence": max(
                20,
                min(
                    resume_result[
                        "confidence"
                    ],
                    60,
                ),
            ),
            "evidence": [
                {
                    "source": "resume",
                    "text": resume_result[
                        "evidence"
                    ],
                    "confidence": resume_result[
                        "confidence"
                    ],
                }
            ],
            "sources": [
                "resume"
            ],
        }

    # ========================================================
    # UNSUPPORTED
    # ========================================================

    return {
        "status": "unsupported",
        "confidence": 0,
        "evidence": [],
        "sources": [],
    }


# ============================================================
# BATCH VERIFICATION
# ============================================================

def verify_claims_with_rag(
    claims: list,
    resume_text: str = "",
    github_evidence: dict | None = None,
    linkedin_evidence: dict | None = None,
) -> list:
    """
    Verify multiple claims.

    This helper is optional but useful if you later want
    to move the verification logic out of main.py.
    """

    verified_claims = []

    for claim in claims:

        if isinstance(
            claim,
            dict,
        ):

            claim_text = claim.get(
                "claim",
                "",
            )

        else:

            claim_text = str(
                claim
            )

        result = verify_claim_with_rag(

            claim=claim_text,

            resume_text=resume_text,

            github_evidence=github_evidence,

            linkedin_evidence=linkedin_evidence,

        )

        if isinstance(
            claim,
            dict,
        ):

            updated_claim = dict(
                claim
            )

            updated_claim[
                "rag_status"
            ] = result["status"]

            updated_claim[
                "rag_confidence"
            ] = result["confidence"]

            updated_claim[
                "rag_evidence"
            ] = result["evidence"]

            updated_claim[
                "rag_sources"
            ] = result["sources"]

            verified_claims.append(
                updated_claim
            )

        else:

            verified_claims.append({

                "claim": claim_text,

                "rag_status": result[
                    "status"
                ],

                "rag_confidence": result[
                    "confidence"
                ],

                "rag_evidence": result[
                    "evidence"
                ],

                "rag_sources": result[
                    "sources"
                ],

            })

    return verified_claims