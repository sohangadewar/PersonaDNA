"""
PersonaDNA - RAG Engine
=======================

Evidence-based claim verification engine.

Purpose
-------
Verifies candidate claims against:

1. Resume
2. GitHub
3. LinkedIn

Design principles
-----------------
- Resume is treated as the candidate's claim.
- GitHub provides technical/project evidence.
- LinkedIn provides secondary professional corroboration.
- "Unverified" is different from "unsupported".
- Evidence is never treated as proof merely because a keyword appears.
- Structured GitHub evidence is preferred over generic text matching.
- Common technology aliases are supported.
- The output remains compatible with PersonaDNA main.py.

No external vector database is required.
"""

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

    "reactjs": {
        "react",
        "reactjs",
        "react.js",
    },
    "react": {
        "react",
        "reactjs",
        "react.js",
    },
}


# ============================================================
# BASIC HELPERS
# ============================================================

def _safe_string(value: Any) -> str:
    """
    Safely convert arbitrary values to string.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value

    return str(value)


def normalize_text(text: Any) -> str:
    """
    Normalize text for matching.
    """

    text = _safe_string(text).lower()

    text = text.replace(
        "machine-learning",
        "machine learning",
    )

    text = text.replace(
        "scikit-learn",
        "scikit learn",
    )

    text = text.replace(
        "react.js",
        "react",
    )

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
    """
    Convert text into meaningful tokens.
    """

    normalized = normalize_text(text)

    if not normalized:
        return set()

    return {
        token
        for token in normalized.split()
        if len(token) > 1
    }


def canonical_claim(claim: Any) -> str:
    """
    Convert a claim into its canonical representation.
    """

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
    """
    Return all known aliases for a claim.
    """

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
    """
    Determine whether a candidate value represents
    the supplied claim.

    Supports aliases such as:

    AI ↔ Artificial Intelligence
    ML ↔ Machine Learning
    JS ↔ JavaScript
    Postgres ↔ PostgreSQL
    """

    target = normalize_text(candidate_value)

    if not target:
        return False

    aliases = claim_aliases(claim)

    if target in aliases:
        return True

    return any(
        alias in target
        for alias in aliases
    )


# ============================================================
# TEXT SIMILARITY
# ============================================================

def calculate_text_similarity(
    claim: str,
    evidence: str,
) -> float:
    """
    Calculate lexical similarity.

    This is deliberately deterministic.
    No LLM-generated confidence is used here.
    """

    claim_tokens = tokenize(claim)
    evidence_tokens = tokenize(evidence)

    if not claim_tokens or not evidence_tokens:
        return 0.0

    overlap = claim_tokens.intersection(
        evidence_tokens
    )

    score = len(overlap) / len(
        claim_tokens
    )

    return round(
        min(score, 1.0),
        2,
    )


# ============================================================
# GENERIC TEXT SEARCH
# ============================================================

def find_best_text_evidence(
    claim: str,
    evidence_text: str,
    source_name: str,
) -> dict:
    """
    Find the strongest sentence supporting a claim.
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

    # Direct alias match is stronger than
    # generic token overlap.
    for alias in aliases:

        if alias and alias in normalized_evidence:

            sentences = re.split(
                r"[.!?\n]+",
                evidence_text,
            )

            best_sentence = ""

            for sentence in sentences:

                sentence_clean = sentence.strip()

                if not sentence_clean:
                    continue

                if alias in normalize_text(
                    sentence_clean
                ):
                    best_sentence = (
                        sentence_clean
                    )
                    break

            return {
                "source": source_name,
                "matched": True,
                "confidence": 85,
                "evidence": (
                    best_sentence
                    or evidence_text[:500]
                )[:500],
            }

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
        "matched": True,
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
    """
    Convert GitHub evidence into searchable text.
    """

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

        value = github_evidence.get(
            key
        )

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

                value = repository.get(
                    key
                )

                if isinstance(
                    value,
                    dict,
                ):
                    parts.extend(
                        _safe_string(key)
                        for key in value.keys()
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

        if isinstance(
            evidence,
            list,
        ):

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
    """
    Convert LinkedIn evidence into searchable text.
    """

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

        value = linkedin_evidence.get(
            key
        )

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

        if isinstance(
            values,
            list,
        ):

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
    Search GitHub's structured evidence.

    Priority:

    1. Repository technologies
    2. Repository language
    3. Repository languages
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

            # Technologies
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

            # Primary language
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

            # Language statistics
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

            # Topics
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
    # Return strong GitHub match
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
                    f"'{repository['name']}' "
                    f"contains evidence for "
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
                    f"contains evidence for '{claim}'."
                )
            )

        repository_count = len(
            matched_repositories
        )

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
            )[:1000],
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
# MAIN VERIFICATION
# ============================================================

def verify_claim_with_rag(
    claim: str,
    resume_text: str = "",
    github_evidence: dict | None = None,
    linkedin_evidence: dict | None = None,
) -> dict:
    """
    Verify one candidate claim.

    Status semantics:

    supported
        Strong external corroboration.

    partially_supported
        One credible external source.

    needs_review
        Claim appears in resume but lacks external
        corroboration.

    unsupported
        Claim was not found in available evidence.
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

    # ========================================================
    # Resume
    # ========================================================

    resume_result = find_best_text_evidence(
        claim=claim_text,
        evidence_text=resume_text,
        source_name="resume",
    )

    # ========================================================
    # GitHub
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
            "confidence": github_structured["confidence"],
            "evidence": github_structured["evidence"],
            "repositories": github_structured["repositories"],
        }

    else:

        github_result = {
            "source": "github",
            "matched": False,
            "confidence": 0,
            "evidence": "",
            "repositories": [],
        }

    # ========================================================
    # LinkedIn
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
    # External evidence
    # ========================================================

    external_results = [
        github_result,
        linkedin_result,
    ]

    external_matches = [
        result
        for result in external_results
        if result.get("matched")
    ]

    # ========================================================
    # Strong support
    # ========================================================

    if len(external_matches) >= 2:

        confidence = max(
            result["confidence"]
            for result in external_matches
        )

        evidence = []

        for result in external_matches:

            if result.get("evidence"):

                evidence.append(
                    {
                        "source": result["source"],
                        "text": result["evidence"],
                        "confidence": result[
                            "confidence"
                        ],
                    }
                )

        return {
            "status": "supported",
            "confidence": min(
                100,
                max(
                    confidence,
                    90,
                ),
            ),
            "evidence": evidence,
            "sources": [
                result["source"]
                for result in external_matches
            ],
        }

    # ========================================================
    # One external source
    # ========================================================

    if len(external_matches) == 1:

        result = external_matches[0]

        confidence = result[
            "confidence"
        ]

        evidence = []

        if result.get("evidence"):

            evidence.append(
                {
                    "source": result["source"],
                    "text": result["evidence"],
                    "confidence": confidence,
                }
            )

        # Strong structured GitHub evidence
        # is stronger than generic textual evidence.
        if (
            result["source"] == "github"
            and confidence >= 90
        ):

            status = "supported"

        else:

            status = "partially_supported"

        return {
            "status": status,
            "confidence": min(
                100,
                max(
                    75,
                    confidence,
                ),
            ),
            "evidence": evidence,
            "sources": [
                result["source"]
            ],
        }

    # ========================================================
    # Resume only
    # ========================================================

    if resume_result["matched"]:

        return {
            "status": "needs_review",
            "confidence": max(
                20,
                min(
                    resume_result["confidence"],
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
    # Unsupported
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
# CANDIDATE EVIDENCE RETRIEVAL
# ============================================================

def retrieve_candidate_evidence(
    query: str,
    candidate_knowledge: str,
) -> dict:
    """
    Retrieve relevant evidence from the candidate knowledge base.

    Lightweight lexical retrieval used by PersonaDNA's RAG
    sanity check and recruiter verification layer.
    """

    if not query or not str(query).strip():
        return {
            "query": query,
            "evidence": [],
            "chunks": [],
        }

    if not candidate_knowledge or not str(candidate_knowledge).strip():
        return {
            "query": query,
            "evidence": [],
            "chunks": [],
        }

    query_text = normalize_text(query)
    knowledge_text = str(candidate_knowledge)

    query_tokens = tokenize(query_text)

    if not query_tokens:
        return {
            "query": query,
            "evidence": [],
            "chunks": [],
        }

    # --------------------------------------------------------
    # Split candidate knowledge into searchable chunks
    # --------------------------------------------------------

    raw_chunks = re.split(
        r"\n\s*\n|(?<=[.!?])\s+",
        knowledge_text,
    )

    chunks = [
        chunk.strip()
        for chunk in raw_chunks
        if chunk and chunk.strip()
    ]

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

        score = (
            len(overlap)
            / max(len(query_tokens), 1)
        )

        scored_chunks.append(
            {
                "text": chunk[:1000],
                "score": round(
                    min(score, 1.0),
                    2,
                ),
                "matched_terms": sorted(
                    overlap
                ),
            }
        )

    # --------------------------------------------------------
    # Highest relevance first
    # --------------------------------------------------------

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # Keep retrieval lightweight
    top_chunks = scored_chunks[:5]

    return {
        "query": query,
        "evidence": top_chunks,
        "chunks": top_chunks,
        "count": len(top_chunks),
    }