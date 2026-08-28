"""
PersonaDNA - Unified RAG Engine
================================

Evidence-based candidate verification and recruiter intelligence engine.

This single module combines:

1. Claim verification
2. GitHub structured evidence matching
3. LinkedIn evidence matching
4. Candidate intelligence
5. Candidate knowledge construction
6. Retrieval from candidate knowledge
7. Recruiter question grounding
8. Project evidence
9. Suspicious claim detection

Design principles
-----------------
- Resume = candidate claim
- GitHub = technical/project evidence
- LinkedIn = professional corroboration
- Unverified != unsupported
- Keyword presence alone is NOT treated as proof
- Structured GitHub evidence is stronger than generic text matching
- Recruiter answers must be grounded in candidate evidence
- Retrieval is deterministic and transparent
- No external vector database required
- No hallucinated candidate facts
- Compatible with PersonaDNA's existing /analyze pipeline
"""

import json
import re
from typing import Any


# ============================================================
# CONFIGURATION
# ============================================================

SUPPORTED_STATUSES = {
    "supported",
    "partially_supported",
    "needs_review",
    "unsupported",
}


# ============================================================
# CLAIM ALIASES
# ============================================================

CLAIM_ALIASES = {

    "ai": {
        "ai",
        "artificial intelligence",
    },

    "artificial intelligence": {
        "ai",
        "artificial intelligence",
    },

    "ml": {
        "ml",
        "machine learning",
        "machine-learning",
    },

    "machine learning": {
        "ml",
        "machine learning",
        "machine-learning",
    },

    "js": {
        "js",
        "javascript",
    },

    "javascript": {
        "js",
        "javascript",
    },

    "ts": {
        "ts",
        "typescript",
    },

    "typescript": {
        "ts",
        "typescript",
    },

    "postgres": {
        "postgres",
        "postgresql",
    },

    "postgresql": {
        "postgres",
        "postgresql",
    },

    "scikit learn": {
        "scikit learn",
        "scikit-learn",
        "sklearn",
    },

    "scikit-learn": {
        "scikit learn",
        "scikit-learn",
        "sklearn",
    },

    "sklearn": {
        "scikit learn",
        "scikit-learn",
        "sklearn",
    },

    "react": {
        "react",
        "reactjs",
        "react.js",
    },

    "reactjs": {
        "react",
        "reactjs",
        "react.js",
    },

    "node": {
        "node",
        "nodejs",
        "node.js",
    },

    "nodejs": {
        "node",
        "nodejs",
        "node.js",
    },

    "fastapi": {
        "fastapi",
    },

    "flask": {
        "flask",
    },

    "python": {
        "python",
    },

    "java": {
        "java",
    },

    "sql": {
        "sql",
    },

    "github": {
        "github",
    },

    "git": {
        "git",
    },
}


# ============================================================
# BASIC HELPERS
# ============================================================

def _safe_string(value: Any) -> str:
    """Safely convert arbitrary values into strings."""

    if value is None:
        return ""

    if isinstance(value, str):
        return value

    return str(value)


def normalize_text(text: Any) -> str:
    """
    Normalize text for deterministic retrieval.

    Keeps useful programming characters while
    removing unnecessary punctuation.
    """

    text = _safe_string(text).lower()

    replacements = {
        "machine-learning": "machine learning",
        "scikit-learn": "scikit learn",
        "react.js": "react",
        "node.js": "nodejs",
        "express.js": "express",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

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


def tokenize(text: Any) -> set[str]:
    """Convert text into normalized tokens."""

    normalized = normalize_text(text)

    if not normalized:
        return set()

    return {
        token
        for token in normalized.split()
        if len(token) > 1
    }


def canonical_claim(claim: Any) -> str:
    """Return canonical representation of a claim."""

    normalized = normalize_text(claim)

    for canonical, aliases in CLAIM_ALIASES.items():

        normalized_aliases = {
            normalize_text(alias)
            for alias in aliases
        }

        if normalized in normalized_aliases:
            return canonical

    return normalized


def claim_aliases(claim: Any) -> set[str]:
    """Return all known aliases for a claim."""

    normalized = normalize_text(claim)
    canonical = canonical_claim(normalized)

    aliases = CLAIM_ALIASES.get(
        canonical,
        {normalized},
    )

    return {
        normalize_text(alias)
        for alias in aliases
        if normalize_text(alias)
    }


def claim_matches(
    claim: Any,
    candidate_value: Any,
) -> bool:
    """Exact normalized claim/alias comparison."""

    target = normalize_text(candidate_value)

    if not target:
        return False

    aliases = claim_aliases(claim)

    return target in aliases


def _safe_json(value: Any) -> str:
    """Safely serialize objects into JSON text."""

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


# ============================================================
# TEXT SIMILARITY
# ============================================================

def calculate_text_similarity(
    claim: str,
    evidence: str,
) -> float:
    """
    Deterministic lexical similarity.

    This is NOT treated as proof.
    It is only used to retrieve potentially
    relevant evidence.
    """

    claim_tokens = tokenize(claim)
    evidence_tokens = tokenize(evidence)

    if not claim_tokens or not evidence_tokens:
        return 0.0

    overlap = claim_tokens.intersection(
        evidence_tokens
    )

    score = (
        len(overlap)
        / len(claim_tokens)
    )

    return round(
        min(score, 1.0),
        2,
    )


# ============================================================
# SENTENCE SPLITTING
# ============================================================

def split_into_chunks(
    text: Any,
) -> list[str]:
    """
    Split candidate knowledge into useful
    retrieval chunks.
    """

    text = _safe_string(text).strip()

    if not text:
        return []

    chunks = re.split(
        r"\n+|(?<=[.!?])\s+",
        text,
    )

    cleaned = []

    for chunk in chunks:

        chunk = chunk.strip()

        if len(chunk) >= 10:
            cleaned.append(chunk)

    return cleaned


# ============================================================
# GENERIC EVIDENCE RETRIEVAL
# ============================================================

def retrieve_relevant_evidence(
    query: str,
    candidate_knowledge: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve the most relevant candidate-knowledge chunks.

    This is the retrieval component of PersonaDNA's
    lightweight local RAG system.

    It does NOT invent information.

    Every returned item comes directly from
    candidate knowledge.
    """

    query = _safe_string(query).strip()

    if not query or not candidate_knowledge:
        return []

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    chunks = split_into_chunks(
        candidate_knowledge
    )

    scored_chunks = []

    for chunk in chunks:

        chunk_tokens = tokenize(chunk)

        if not chunk_tokens:
            continue

        overlap = query_tokens.intersection(
            chunk_tokens
        )

        if not overlap:
            continue

        lexical_score = (
            len(overlap)
            / max(
                len(query_tokens),
                1,
            )
        )

        # Small bonus when the complete normalized
        # query appears in the chunk.
        normalized_query = normalize_text(
            query
        )

        normalized_chunk = normalize_text(
            chunk
        )

        phrase_bonus = 0.0

        if (
            normalized_query
            and normalized_query in normalized_chunk
        ):
            phrase_bonus = 0.20

        final_score = min(
            1.0,
            lexical_score + phrase_bonus,
        )

        scored_chunks.append(
            {
                "text": chunk,
                "score": round(
                    final_score,
                    3,
                ),
                "matched_terms": sorted(
                    overlap
                ),
            }
        )

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored_chunks[:top_k]


# ============================================================
# GENERIC TEXT SEARCH
# ============================================================

def find_best_text_evidence(
    claim: str,
    evidence_text: str,
    source_name: str,
) -> dict:
    """
    Retrieve strongest textual evidence.

    Important:
    Generic textual matches are never automatically
    considered proof.
    """

    if not evidence_text:

        return {
            "source": source_name,
            "matched": False,
            "confidence": 0,
            "evidence": "",
        }

    claim_text = _safe_string(
        claim
    ).strip()

    aliases = claim_aliases(
        claim_text
    )

    normalized_evidence = normalize_text(
        evidence_text
    )

    # --------------------------------------------------------
    # Exact alias match
    # --------------------------------------------------------

    for alias in aliases:

        if (
            alias
            and re.search(
                r"(?<!\w)"
                + re.escape(alias)
                + r"(?!\w)",
                normalized_evidence,
            )
        ):

            sentences = split_into_chunks(
                evidence_text
            )

            for sentence in sentences:

                normalized_sentence = normalize_text(
                    sentence
                )

                if re.search(
                    r"(?<!\w)"
                    + re.escape(alias)
                    + r"(?!\w)",
                    normalized_sentence,
                ):

                    return {
                        "source": source_name,
                        "matched": True,
                        "confidence": 85,
                        "evidence": sentence[:500],
                    }

    # --------------------------------------------------------
    # Lexical retrieval
    # --------------------------------------------------------

    similarity = calculate_text_similarity(
        claim_text,
        evidence_text,
    )

    if similarity < 0.35:

        return {
            "source": source_name,
            "matched": False,
            "confidence": round(
                similarity * 100
            ),
            "evidence": "",
        }

    claim_tokens = tokenize(
        claim_text
    )

    sentences = split_into_chunks(
        evidence_text
    )

    best_sentence = ""
    best_score = 0.0

    for sentence in sentences:

        sentence_tokens = tokenize(
            sentence
        )

        overlap = claim_tokens.intersection(
            sentence_tokens
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

    return {
        "source": source_name,
        "matched": bool(best_sentence),
        "confidence": min(
            80,
            round(similarity * 100),
        ),
        "evidence": best_sentence[:500],
    }


# ============================================================
# GITHUB EXTRACTION
# ============================================================

def extract_github_text(
    github_evidence: dict,
) -> str:
    """Convert structured GitHub data into searchable text."""

    if not isinstance(
        github_evidence,
        dict,
    ):
        return ""

    parts = []

    profile_keys = [
        "username",
        "login",
        "display_name",
        "name",
        "bio",
        "company",
        "location",
        "html_url",
    ]

    for key in profile_keys:

        value = github_evidence.get(key)

        if value:
            parts.append(
                _safe_string(value)
            )

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if isinstance(
        repositories,
        list,
    ):

        for repository in repositories:

            if not isinstance(
                repository,
                dict,
            ):
                continue

            for key in [
                "name",
                "description",
                "language",
                "languages",
                "technologies",
                "topics",
                "url",
                "html_url",
            ]:

                value = repository.get(key)

                if isinstance(
                    value,
                    dict,
                ):

                    parts.extend(
                        _safe_string(k)
                        for k in value.keys()
                    )

                elif isinstance(
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

    for key in [
        "technology_evidence",
        "skill_evidence",
    ]:

        evidence = github_evidence.get(
            key,
            [],
        )

        if not isinstance(
            evidence,
            list,
        ):
            continue

        for item in evidence:

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
# LINKEDIN EXTRACTION
# ============================================================

def extract_linkedin_text(
    linkedin_evidence: dict,
) -> str:
    """Convert LinkedIn evidence into searchable text."""

    if not isinstance(
        linkedin_evidence,
        dict,
    ):
        return ""

    parts = []

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

        value = linkedin_evidence.get(key)

        if value:
            parts.append(
                _safe_string(value)
            )

    for key in [
        "skills",
        "experience",
        "education",
    ]:

        values = linkedin_evidence.get(
            key,
            [],
        )

        if not isinstance(
            values,
            list,
        ):
            continue

        for item in values:

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
# GITHUB STRUCTURED MATCHING
# ============================================================

def find_github_structured_evidence(
    claim: str,
    github_evidence: dict,
) -> dict:
    """
    Search structured GitHub evidence.

    Priority:

    1. Technologies
    2. Primary language
    3. Languages
    4. Topics
    5. technology_evidence
    6. skill_evidence
    """

    if not isinstance(
        github_evidence,
        dict,
    ):

        return {
            "matched": False,
            "confidence": 0,
            "evidence": "",
            "repositories": [],
        }

    matched_repositories = []

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if isinstance(
        repositories,
        list,
    ):

        for repository in repositories:

            if not isinstance(
                repository,
                dict,
            ):
                continue

            repository_name = _safe_string(
                repository.get(
                    "name",
                    "",
                )
            )

            evidence_types = set()

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

                    if claim_matches(
                        claim,
                        technology,
                    ):

                        evidence_types.add(
                            "technology"
                        )

            # ------------------------------------------------
            # Primary language
            # ------------------------------------------------

            language = repository.get(
                "language",
                "",
            )

            if language and claim_matches(
                claim,
                language,
            ):

                evidence_types.add(
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

                    if claim_matches(
                        claim,
                        language_name,
                    ):

                        evidence_types.add(
                            "languages"
                        )

            # ------------------------------------------------
            # Topics
            # ------------------------------------------------

            topics = repository.get(
                "topics",
                [],
            )

            if isinstance(
                topics,
                list,
            ):

                for topic in topics:

                    if claim_matches(
                        claim,
                        topic,
                    ):

                        evidence_types.add(
                            "topic"
                        )

            if evidence_types:

                matched_repositories.append(
                    {
                        "name": repository_name,
                        "evidence_types": sorted(
                            evidence_types
                        ),
                    }
                )

    # ========================================================
    # Global GitHub evidence
    # ========================================================

    global_evidence_types = set()

    for key in [
        "technology_evidence",
        "skill_evidence",
    ]:

        evidence = github_evidence.get(
            key,
            [],
        )

        if not isinstance(
            evidence,
            list,
        ):
            continue

        for item in evidence:

            if isinstance(
                item,
                dict,
            ):

                values = item.values()

            else:

                values = [item]

            for value in values:

                if claim_matches(
                    claim,
                    value,
                ):

                    global_evidence_types.add(
                        key
                    )

    # ========================================================
    # Build result
    # ========================================================

    if (
        matched_repositories
        or global_evidence_types
    ):

        evidence_lines = []

        for repository in matched_repositories:

            evidence_lines.append(
                (
                    f"GitHub repository "
                    f"'{repository['name']}' contains "
                    f"structured evidence for "
                    f"'{claim}' through "
                    f"{', '.join(repository['evidence_types'])}."
                )
            )

        for evidence_type in sorted(
            global_evidence_types
        ):

            evidence_lines.append(
                (
                    f"GitHub {evidence_type.replace('_', ' ')} "
                    f"contains structured evidence for "
                    f"'{claim}'."
                )
            )

        repository_count = len(
            matched_repositories
        )

        # ----------------------------------------------------
        # Confidence is evidence strength,
        # NOT probability that candidate is truthful.
        # ----------------------------------------------------

        if repository_count >= 2:
            confidence = 98

        elif repository_count == 1:
            confidence = 95

        elif global_evidence_types:
            confidence = 90

        else:
            confidence = 0

        return {
            "matched": True,
            "confidence": confidence,
            "evidence": " ".join(
                evidence_lines
            )[:1500],
            "repositories": [
                item["name"]
                for item in matched_repositories
            ],
        }

    return {
        "matched": False,
        "confidence": 0,
        "evidence": "",
        "repositories": [],
    }


# ============================================================
# CLAIM VERIFICATION
# ============================================================

def verify_claim_with_rag(
    claim: str,
    resume_text: str = "",
    github_evidence: dict | None = None,
    linkedin_evidence: dict | None = None,
) -> dict:
    """
    Verify one candidate claim.

    Status semantics
    ----------------

    supported
        Strong structured external evidence exists.

    partially_supported
        Credible external evidence exists but
        does not meet the strongest corroboration
        threshold.

    needs_review
        Claim appears in resume but external
        corroboration is missing.

    unsupported
        Claim cannot be found in available evidence.

    Important:
    LinkedIn + generic keyword matching is NOT
    automatically treated as strong proof.
    """

    if not claim:

        return {
            "status": "needs_review",
            "confidence": 0,
            "evidence": [],
            "sources": [],
        }

    github_evidence = (
        github_evidence
        if isinstance(
            github_evidence,
            dict,
        )
        else {}
    )

    linkedin_evidence = (
        linkedin_evidence
        if isinstance(
            linkedin_evidence,
            dict,
        )
        else {}
    )

    claim_text = _safe_string(
        claim
    ).strip()

    # ========================================================
    # RESUME
    # ========================================================

    resume_result = find_best_text_evidence(
        claim=claim_text,
        evidence_text=resume_text,
        source_name="resume",
    )

    # ========================================================
    # GITHUB STRUCTURED
    # ========================================================

    github_structured = (
        find_github_structured_evidence(
            claim=claim_text,
            github_evidence=github_evidence,
        )
    )

    if github_structured["matched"]:

        github_result = {
            "source": "github",
            "matched": True,
            "confidence": github_structured[
                "confidence"
            ],
            "evidence": github_structured[
                "evidence"
            ],
            "repositories": github_structured[
                "repositories"
            ],
            "structured": True,
        }

    else:

        github_result = {
            "source": "github",
            "matched": False,
            "confidence": 0,
            "evidence": "",
            "repositories": [],
            "structured": False,
        }

    # ========================================================
    # LINKEDIN
    # ========================================================

    linkedin_text = extract_linkedin_text(
        linkedin_evidence
    )

    linkedin_result = find_best_text_evidence(
        claim=claim_text,
        evidence_text=linkedin_text,
        source_name="linkedin",
    )

    # ========================================================
    # EXTERNAL EVIDENCE
    # ========================================================

    github_match = github_result["matched"]
    linkedin_match = linkedin_result["matched"]

    github_confidence = github_result[
        "confidence"
    ]

    linkedin_confidence = linkedin_result[
        "confidence"
    ]

    evidence = []

    if github_match and github_result.get(
        "evidence"
    ):

        evidence.append(
            {
                "source": "github",
                "text": github_result[
                    "evidence"
                ],
                "confidence": github_confidence,
                "structured": True,
                "repositories": github_result.get(
                    "repositories",
                    [],
                ),
            }
        )

    if linkedin_match and linkedin_result.get(
        "evidence"
    ):

        evidence.append(
            {
                "source": "linkedin",
                "text": linkedin_result[
                    "evidence"
                ],
                "confidence": linkedin_confidence,
                "structured": False,
            }
        )

    # ========================================================
    # STATUS DECISION
    # ========================================================

    # --------------------------------------------------------
    # CASE 1:
    # Strong structured GitHub evidence
    # --------------------------------------------------------

    if (
        github_match
        and github_confidence >= 90
    ):

        if linkedin_match:

            return {
                "status": "supported",
                "confidence": min(
                    100,
                    max(
                        95,
                        github_confidence,
                    ),
                ),
                "evidence": evidence,
                "sources": [
                    "github",
                    "linkedin",
                ],
            }

        return {
            "status": "supported",
            "confidence": github_confidence,
            "evidence": evidence,
            "sources": [
                "github"
            ],
        }

    # --------------------------------------------------------
    # CASE 2:
    # LinkedIn corroboration only
    # --------------------------------------------------------

    if linkedin_match:

        return {
            "status": "partially_supported",
            "confidence": max(
                75,
                min(
                    85,
                    linkedin_confidence,
                ),
            ),
            "evidence": evidence,
            "sources": [
                "linkedin"
            ],
        }

    # --------------------------------------------------------
    # CASE 3:
    # Resume only
    # --------------------------------------------------------

    if resume_result["matched"]:

        return {
            "status": "needs_review",
            "confidence": max(
                20,
                min(
                    60,
                    resume_result[
                        "confidence"
                    ],
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

    # --------------------------------------------------------
    # CASE 4:
    # Nothing found
    # --------------------------------------------------------

    return {
        "status": "unsupported",
        "confidence": 0,
        "evidence": [],
        "sources": [],
    }


# ============================================================
# BATCH CLAIM VERIFICATION
# ============================================================

def verify_claims_with_rag(
    claims: list,
    resume_text: str = "",
    github_evidence: dict | None = None,
    linkedin_evidence: dict | None = None,
) -> list:
    """Verify multiple claims."""

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

            verified_claims.append(
                {
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
                }
            )

    return verified_claims


# ============================================================
# EVIDENCE STRENGTH
# ============================================================

def calculate_evidence_strength(
    claim: dict,
    github_evidence: dict | None = None,
    linkedin_evidence: dict | None = None,
) -> dict:
    """
    Calculate evidence strength.

    Unlike the old implementation, this function
    can use the actual RAG result attached to a claim.

    Resume alone is never considered strong evidence.
    """

    github_evidence = github_evidence or {}
    linkedin_evidence = linkedin_evidence or {}

    rag_status = claim.get(
        "rag_status",
        "unverified",
    )

    rag_confidence = claim.get(
        "rag_confidence",
        0,
    )

    sources = claim.get(
        "rag_sources",
        [],
    )

    if not isinstance(
        sources,
        list,
    ):
        sources = []

    # --------------------------------------------------------
    # Use RAG result when available
    # --------------------------------------------------------

    if rag_status == "supported":

        return {
            "score": min(
                100,
                max(
                    80,
                    int(
                        rag_confidence
                        or 80
                    ),
                ),
            ),
            "strength": "strong",
            "sources": sources,
        }

    if rag_status == "partially_supported":

        return {
            "score": min(
                79,
                max(
                    50,
                    int(
                        rag_confidence
                        or 50
                    ),
                ),
            ),
            "strength": "moderate",
            "sources": sources,
        }

    if rag_status == "needs_review":

        return {
            "score": min(
                49,
                max(
                    20,
                    int(
                        rag_confidence
                        or 20
                    ),
                ),
            ),
            "strength": "weak",
            "sources": sources,
        }

    return {
        "score": 0,
        "strength": "none",
        "sources": [],
    }


# ============================================================
# PROJECT EVIDENCE
# ============================================================

def extract_project_evidence(
    claims,
) -> list[dict]:
    """Extract project claims."""

    projects = []

    for claim in claims or []:

        if not isinstance(
            claim,
            dict,
        ):
            continue

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
                "rag_status": claim.get(
                    "rag_status",
                    "unverified",
                ),
                "rag_confidence": claim.get(
                    "rag_confidence",
                    0,
                ),
                "rag_sources": claim.get(
                    "rag_sources",
                    [],
                ),
            }
        )

    return projects


# ============================================================
# SUSPICIOUS CLAIM DETECTION
# ============================================================

def detect_suspicious_claims(
    claims,
    identity,
    github_evidence,
):
    """
    Detect claims requiring recruiter attention.

    This does NOT call a candidate dishonest.
    It only identifies insufficient or conflicting evidence.
    """

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

        if not isinstance(
            claim,
            dict,
        ):
            continue

        if claim.get(
            "type"
        ) != "skill":

            continue

        rag_status = claim.get(
            "rag_status",
            "unverified",
        )

        rag_sources = claim.get(
            "rag_sources",
            [],
        )

        if not isinstance(
            rag_sources,
            list,
        ):
            rag_sources = []

        reasons = []

        if rag_status == "unsupported":

            reasons.append(
                "The claimed skill was not found in the available evidence."
            )

        elif rag_status == "needs_review":

            reasons.append(
                "The skill appears in the resume but lacks external corroboration."
            )

        elif rag_status == "partially_supported":

            reasons.append(
                "External evidence exists, but stronger corroboration is recommended."
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
                not rag_sources
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
                    "rag_status": rag_status,
                    "rag_sources": rag_sources,
                }
            )

    return suspicious


# ============================================================
# CANDIDATE INTELLIGENCE
# ============================================================

def build_candidate_intelligence(
    claims,
    github_evidence,
    identity,
    resume_text,
    linkedin_evidence=None,
):
    """
    Build candidate intelligence from the complete
    evidence set.
    """

    claims = claims or []
    github_evidence = github_evidence or {}
    identity = identity or {}
    resume_text = resume_text or ""
    linkedin_evidence = (
        linkedin_evidence or {}
    )

    # --------------------------------------------------------
    # Ensure claims have RAG results
    # --------------------------------------------------------

    enriched_claims = []

    for claim in claims:

        if not isinstance(
            claim,
            dict,
        ):
            continue

        current_claim = dict(
            claim
        )

        if not current_claim.get(
            "rag_status"
        ):

            result = verify_claim_with_rag(
                claim=current_claim.get(
                    "claim",
                    "",
                ),
                resume_text=resume_text,
                github_evidence=github_evidence,
                linkedin_evidence=linkedin_evidence,
            )

            current_claim[
                "rag_status"
            ] = result["status"]

            current_claim[
                "rag_confidence"
            ] = result["confidence"]

            current_claim[
                "rag_evidence"
            ] = result["evidence"]

            current_claim[
                "rag_sources"
            ] = result["sources"]

        enriched_claims.append(
            current_claim
        )

    # --------------------------------------------------------
    # Claim evidence
    # --------------------------------------------------------

    claim_evidence = []

    for claim in enriched_claims:

        if claim.get(
            "type"
        ) != "skill":

            continue

        evidence_result = (
            calculate_evidence_strength(
                claim=claim,
                github_evidence=github_evidence,
                linkedin_evidence=linkedin_evidence,
            )
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
                "score": evidence_result[
                    "score"
                ],
                "strength": evidence_result[
                    "strength"
                ],
                "sources": evidence_result[
                    "sources"
                ],
                "rag_status": claim.get(
                    "rag_status",
                    "unverified",
                ),
                "rag_confidence": claim.get(
                    "rag_confidence",
                    0,
                ),
            }
        )

    # --------------------------------------------------------
    # Overall evidence score
    # --------------------------------------------------------

    total_claims = len(
        claim_evidence
    )

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

    if overall_evidence_score >= 80:

        evidence_level = "strong"

    elif overall_evidence_score >= 50:

        evidence_level = "moderate"

    elif overall_evidence_score > 0:

        evidence_level = "weak"

    else:

        evidence_level = "none"

    suspicious_claims = (
        detect_suspicious_claims(
            claims=enriched_claims,
            identity=identity,
            github_evidence=github_evidence,
        )
    )

    # --------------------------------------------------------
    # Supported / review statistics
    # --------------------------------------------------------

    supported_count = sum(
        1
        for claim in enriched_claims
        if claim.get(
            "rag_status"
        )
        == "supported"
    )

    partial_count = sum(
        1
        for claim in enriched_claims
        if claim.get(
            "rag_status"
        )
        == "partially_supported"
    )

    review_count = sum(
        1
        for claim in enriched_claims
        if claim.get(
            "rag_status"
        )
        == "needs_review"
    )

    unsupported_count = sum(
        1
        for claim in enriched_claims
        if claim.get(
            "rag_status"
        )
        == "unsupported"
    )

    return {
        "overall_evidence_score": overall_evidence_score,
        "evidence_level": evidence_level,

        "claim_evidence": claim_evidence,

        "project_evidence": (
            extract_project_evidence(
                enriched_claims
            )
        ),

        "suspicious_claims": suspicious_claims,

        "suspicious_claim_count": len(
            suspicious_claims
        ),

        "supported_claim_count": supported_count,
        "partially_supported_claim_count": partial_count,
        "needs_review_claim_count": review_count,
        "unsupported_claim_count": unsupported_count,

        "github_profile_found": bool(
            github_evidence.get(
                "profile_found",
                False,
            )
        ),

        "github_identity_match": bool(
            identity.get(
                "github_match",
                False,
            )
        ),

        "linkedin_identity_match": bool(
            identity.get(
                "linkedin_match",
                False,
            )
        ),
    }


# ============================================================
# CANDIDATE KNOWLEDGE
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
    Build the candidate's complete knowledge base.

    This is the source document used by the retrieval
    layer when recruiters ask questions.
    """

    sections = []

    # --------------------------------------------------------
    # Resume
    # --------------------------------------------------------

    sections.append(
        "===== RESUME TEXT ====="
    )

    sections.append(
        (resume_text or "").strip()
    )

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    sections.append(
        "\n===== IDENTITY ====="
    )

    sections.append(
        _safe_json(identity)
    )

    # --------------------------------------------------------
    # Claims
    # --------------------------------------------------------

    sections.append(
        "\n===== EXTRACTED CLAIMS ====="
    )

    if claims:

        for index, claim in enumerate(
            claims,
            start=1,
        ):

            if not isinstance(
                claim,
                dict,
            ):
                continue

            claim_text = claim.get(
                "claim",
                "",
            )

            status = claim.get(
                "rag_status",
                "unverified",
            )

            confidence = claim.get(
                "rag_confidence",
                0,
            )

            sources = claim.get(
                "rag_sources",
                [],
            )

            sections.append(
                (
                    f"{index}. "
                    f'"{claim_text}" '
                    f"— RAG status: {status}; "
                    f"confidence: {confidence}; "
                    f"sources: {sources}"
                )
            )

    else:

        sections.append(
            "No claims were extracted from the resume."
        )

    # --------------------------------------------------------
    # GitHub
    # --------------------------------------------------------

    sections.append(
        "\n===== GITHUB EVIDENCE ====="
    )

    sections.append(
        _safe_json(github_evidence)
    )

    # --------------------------------------------------------
    # LinkedIn
    # --------------------------------------------------------

    sections.append(
        "\n===== LINKEDIN EVIDENCE ====="
    )

    sections.append(
        _safe_json(linkedin_evidence)
    )

    # --------------------------------------------------------
    # Candidate Intelligence
    # --------------------------------------------------------

    sections.append(
        "\n===== CANDIDATE INTELLIGENCE ====="
    )

    sections.append(
        _safe_json(candidate_intelligence)
    )

    # --------------------------------------------------------
    # Skill Mapping
    # --------------------------------------------------------

    sections.append(
        "\n===== SKILL TO REPOSITORY MAPPING ====="
    )

    sections.append(
        _safe_json(
            skill_repository_mapping
        )
    )

    # --------------------------------------------------------
    # Project Mapping
    # --------------------------------------------------------

    sections.append(
        "\n===== PROJECT TO REPOSITORY MAPPING ====="
    )

    sections.append(
        _safe_json(
            project_repository_mapping
        )
    )

    return "\n".join(
        sections
    )


# ============================================================
# RECRUITER QUERY NORMALIZATION
# ============================================================

def expand_recruiter_query(
    question: str,
) -> str:
    """
    Add useful retrieval terms to common recruiter
    questions without inventing candidate facts.
    """

    question = _safe_string(
        question
    ).strip()

    normalized = normalize_text(
        question
    )

    expansions = []

    question_groups = {

        "skills": [
            "skill",
            "skills",
            "technology",
            "technologies",
            "tech stack",
            "technical",
            "programming",
        ],

        "projects": [
            "project",
            "projects",
            "built",
            "developed",
            "worked on",
        ],

        "experience": [
            "experience",
            "work experience",
            "worked",
            "internship",
            "role",
        ],

        "github": [
            "github",
            "repository",
            "repositories",
            "repo",
            "repos",
            "code",
        ],

        "education": [
            "education",
            "degree",
            "college",
            "university",
            "academic",
        ],

        "identity": [
            "identity",
            "name",
            "profile",
            "linkedin",
        ],
    }

    for group_terms in question_groups.values():

        if any(
            term in normalized
            for term in group_terms
        ):

            expansions.extend(
                group_terms[:4]
            )

    return " ".join(
        [
            question,
            *expansions,
        ]
    )


# ============================================================
# RECRUITER QUESTION RETRIEVAL
# ============================================================

def retrieve_for_recruiter(
    question: str,
    candidate_knowledge: str,
    top_k: int = 7,
) -> dict:
    """
    Retrieve evidence relevant to a recruiter question.

    Returns:

    - original question
    - expanded query
    - retrieved evidence
    - retrieval confidence
    - grounded flag
    """

    if not question:

        return {
            "question": "",
            "query": "",
            "retrieved": [],
            "retrieval_confidence": 0,
            "grounded": False,
        }

    expanded_query = (
        expand_recruiter_query(
            question
        )
    )

    retrieved = retrieve_relevant_evidence(
        query=expanded_query,
        candidate_knowledge=candidate_knowledge,
        top_k=top_k,
    )

    if not retrieved:

        return {
            "question": question,
            "query": expanded_query,
            "retrieved": [],
            "retrieval_confidence": 0,
            "grounded": False,
        }

    highest_score = retrieved[0][
        "score"
    ]

    if highest_score >= 0.70:

        retrieval_confidence = 90

    elif highest_score >= 0.50:

        retrieval_confidence = 75

    elif highest_score >= 0.35:

        retrieval_confidence = 60

    else:

        retrieval_confidence = 40

    return {
        "question": question,
        "query": expanded_query,
        "retrieved": retrieved,
        "retrieval_confidence": retrieval_confidence,
        "grounded": True,
    }


# ============================================================
# RECRUITER PROMPT BUILDER
# ============================================================

def build_recruiter_prompt(
    question: str,
    candidate_knowledge: str,
) -> str:
    """
    Build a grounded recruiter prompt.

    The LLM is explicitly prohibited from using
    information outside the retrieved candidate evidence.
    """

    retrieval = retrieve_for_recruiter(
        question=question,
        candidate_knowledge=candidate_knowledge,
        top_k=7,
    )

    retrieved = retrieval.get(
        "retrieved",
        [],
    )

    if not retrieved:

        evidence_text = (
            "No relevant candidate evidence "
            "was retrieved."
        )

    else:

        evidence_blocks = []

        for index, item in enumerate(
            retrieved,
            start=1,
        ):

            evidence_blocks.append(
                (
                    f"[Evidence {index}] "
                    f"(retrieval score: "
                    f"{item['score']})\n"
                    f"{item['text']}"
                )
            )

        evidence_text = "\n\n".join(
            evidence_blocks
        )

    return (
        "You are PersonaDNA's evidence-grounded "
        "recruiting assistant.\n\n"

        "Your job is to answer the recruiter's "
        "question using ONLY the retrieved candidate "
        "evidence below.\n\n"

        "STRICT RULES:\n"
        "1. Do not invent candidate information.\n"
        "2. Do not assume a skill merely because it "
        "is common for the candidate's role.\n"
        "3. Do not treat a keyword as proof.\n"
        "4. Clearly distinguish verified evidence "
        "from resume claims.\n"
        "5. If evidence is insufficient, say "
        "'The available evidence is insufficient.'\n"
        "6. Never fabricate GitHub repositories, "
        "projects, experience, education, or skills.\n"
        "7. Prefer structured GitHub evidence over "
        "generic textual matches.\n"
        "8. Keep the answer concise and recruiter-friendly.\n\n"

        "===== RETRIEVAL INFORMATION =====\n"
        f"Retrieval confidence: "
        f"{retrieval.get('retrieval_confidence', 0)}\n"
        f"Grounded: "
        f"{retrieval.get('grounded', False)}\n\n"

        "===== RETRIEVED CANDIDATE EVIDENCE =====\n"
        f"{evidence_text}\n\n"

        "===== RECRUITER QUESTION =====\n"
        f"{question}\n\n"

        "===== REQUIRED ANSWER =====\n"
    )


# ============================================================
# DIRECT RECRUITER ANSWER CONTEXT
# ============================================================

def answer_recruiter_question_context(
    question: str,
    candidate_knowledge: str,
) -> dict:
    """
    Retrieve candidate evidence for a recruiter question.

    This function does not call an LLM.

    It returns grounded context that can safely be
    passed to Gemini/OpenAI or another generation layer.
    """

    retrieval = retrieve_for_recruiter(
        question=question,
        candidate_knowledge=candidate_knowledge,
        top_k=7,
    )

    if not retrieval["grounded"]:

        return {
            "status": "insufficient_evidence",
            "answer": (
                "The available candidate evidence "
                "is insufficient to answer this question."
            ),
            "question": question,
            "retrieval": retrieval,
        }

    evidence_lines = []

    for item in retrieval["retrieved"]:

        evidence_lines.append(
            item["text"]
        )

    return {
        "status": "grounded",
        "answer": "\n".join(
            evidence_lines
        ),
        "question": question,
        "retrieval": retrieval,
    }


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

def build_rag_knowledge(
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
    Backward-compatible alias.
    """

    return build_candidate_knowledge(
        resume_text=resume_text,
        claims=claims,
        github_evidence=github_evidence,
        linkedin_evidence=linkedin_evidence,
        candidate_intelligence=candidate_intelligence,
        skill_repository_mapping=skill_repository_mapping,
        project_repository_mapping=project_repository_mapping,
        identity=identity,
    )


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "PersonaDNA Unified RAG Engine loaded successfully."
    )

    test_claim = "Python"

    test_github = {
        "profile_found": True,
        "repositories": [
            {
                "name": "test-project",
                "language": "Python",
                "technologies": [
                    "Python",
                    "FastAPI",
                ],
                "topics": [
                    "ai",
                ],
            }
        ],
    }

    result = verify_claim_with_rag(
        claim=test_claim,
        resume_text="Experienced in Python.",
        github_evidence=test_github,
        linkedin_evidence={},
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )