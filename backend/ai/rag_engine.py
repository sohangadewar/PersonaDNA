"""
PersonaDNA - RAG Engine
=======================

Evidence-based candidate claim verification engine.

Sources:
1. Resume
2. GitHub
3. LinkedIn

Rules:
- Resume = candidate's claimed information.
- GitHub = technical/project evidence.
- LinkedIn = secondary professional corroboration.
- External evidence can SUPPORT a claim.
- Evidence does NOT automatically prove a claim is true.
- Strict matching is used to avoid false positives.
"""

import re
from typing import Any, Optional


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
}


# ============================================================
# BASIC HELPERS
# ============================================================

def _safe_string(value: Any) -> str:
    """Safely convert any value to string."""

    if value is None:
        return ""

    if isinstance(value, str):
        return value

    try:
        return str(value)
    except Exception:
        return ""


def safe_confidence(value: Any) -> float:
    """Convert confidence into a safe 0-100 float."""

    try:
        number = float(value)

        if number < 0:
            return 0.0

        if number > 100:
            return 100.0

        return number

    except (TypeError, ValueError):
        return 0.0


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: Any) -> str:
    """
    Normalize text for deterministic matching.

    Important:
    Java != JavaScript
    SQL != SQLAlchemy
    ML != HTML
    """

    text = _safe_string(text).lower().strip()

    # Standard aliases
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

    # Keep letters, numbers and common technical symbols.
    text = re.sub(
        r"[^a-z0-9+#.\- ]+",
        " ",
        text,
    )

    # Remove repeated spaces.
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# TOKENIZATION
# ============================================================

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


# ============================================================
# CANONICAL CLAIM
# ============================================================

def canonical_claim(claim: Any) -> str:
    """Convert a claim to canonical form."""

    normalized = normalize_text(claim)

    if not normalized:
        return ""

    for canonical, aliases in CLAIM_ALIASES.items():

        normalized_aliases = {
            normalize_text(alias)
            for alias in aliases
        }

        if normalized in normalized_aliases:
            return canonical

    return normalized


# ============================================================
# CLAIM ALIASES
# ============================================================

def claim_aliases(claim: Any) -> set[str]:
    """Return all aliases associated with a claim."""

    normalized = normalize_text(claim)

    if not normalized:
        return set()

    canonical = canonical_claim(normalized)

    aliases = CLAIM_ALIASES.get(
        canonical,
        {normalized},
    )

    result = {
        normalize_text(alias)
        for alias in aliases
        if normalize_text(alias)
    }

    result.add(normalized)

    return result


# ============================================================
# CLAIM MATCHING
# ============================================================

def claim_matches(
    claim: Any,
    candidate_value: Any,
) -> bool:
    """
    Strict claim matching.

    Examples:

        Java       != JavaScript
        SQL        != SQLAlchemy
        ML         != HTML

    Supported aliases:

        AI <-> Artificial Intelligence
        ML <-> Machine Learning
        JS <-> JavaScript
        TS <-> TypeScript
        Postgres <-> PostgreSQL
        React <-> ReactJS
    """

    target = normalize_text(candidate_value)

    if not target:
        return False

    aliases = claim_aliases(claim)

    for alias in aliases:

        alias = normalize_text(alias)

        if not alias:
            continue

        # Exact match.
        if target == alias:
            return True

        # Boundary-aware match.
        #
        # This prevents:
        #
        # Java -> JavaScript
        # SQL -> SQLAlchemy
        #
        pattern = (
            rf"(?<![a-z0-9])"
            rf"{re.escape(alias)}"
            rf"(?![a-z0-9])"
        )

        if re.search(pattern, target):
            return True

    return False


# ============================================================
# STRICT TEXT EVIDENCE
# ============================================================

def find_best_text_evidence(
    claim: str,
    evidence_text: str,
    source_name: str,
) -> dict:
    """
    Find strict evidence for a claim.

    Important:
    - Java does NOT match JavaScript.
    - SQL does NOT match SQLAlchemy.
    - ML does NOT match HTML.
    - Similar words are NOT treated as evidence.
    - Only exact claim/alias matches are accepted.
    """

    if not evidence_text:
        return {
            "source": source_name,
            "matched": False,
            "confidence": 0,
            "evidence": "",
        }

    claim_text = _safe_string(claim).strip()

    if not claim_text:
        return {
            "source": source_name,
            "matched": False,
            "confidence": 0,
            "evidence": "",
        }

    aliases = claim_aliases(claim_text)

    # --------------------------------------------------------
    # SPLIT INTO SENTENCES / LINES
    # --------------------------------------------------------

    sentences = re.split(
        r"[.!?\n]+",
        _safe_string(evidence_text),
    )

    # --------------------------------------------------------
    # STRICT EXACT / ALIAS MATCH
    # --------------------------------------------------------

    for sentence in sentences:

        sentence_clean = sentence.strip()

        if not sentence_clean:
            continue

        normalized_sentence = normalize_text(
            sentence_clean
        )

        for alias in aliases:

            normalized_alias = normalize_text(alias)

            if not normalized_alias:
                continue

            # ------------------------------------------------
            # BOUNDARY-AWARE MATCH
            # ------------------------------------------------

            pattern = (
                rf"(?<![a-z0-9])"
                rf"{re.escape(normalized_alias)}"
                rf"(?![a-z0-9])"
            )

            if re.search(
                pattern,
                normalized_sentence,
            ):
                return {
                    "source": source_name,
                    "matched": True,
                    "confidence": 85,
                    "evidence": sentence_clean[:500],
                }

    # --------------------------------------------------------
    # NO EXACT MATCH
    # --------------------------------------------------------

    return {
        "source": source_name,
        "matched": False,
        "confidence": 0,
        "evidence": "",
    }
# ============================================================
# GITHUB TEXT EXTRACTION
# ============================================================

def extract_github_text(
    github_evidence: dict,
) -> str:
    """Convert GitHub structured data into searchable text."""

    if not isinstance(github_evidence, dict):
        return ""

    parts = []

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # REPOSITORIES
    # --------------------------------------------------------

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if isinstance(repositories, list):

        for repository in repositories:

            if not isinstance(repository, dict):
                continue

            repository_keys = [
                "name",
                "description",
                "language",
                "languages",
                "technologies",
                "topics",
                "url",
                "html_url",
            ]

            for key in repository_keys:

                value = repository.get(key)

                if isinstance(value, dict):

                    for nested_key in value.keys():
                        parts.append(
                            _safe_string(nested_key)
                        )

                elif isinstance(value, list):

                    for item in value:

                        if item:
                            parts.append(
                                _safe_string(item)
                            )

                elif value:

                    parts.append(
                        _safe_string(value)
                    )

    # --------------------------------------------------------
    # GLOBAL EVIDENCE
    # --------------------------------------------------------

    for key in [
        "technology_evidence",
        "skill_evidence",
    ]:

        evidence = github_evidence.get(
            key,
            [],
        )

        if not isinstance(evidence, list):
            continue

        for item in evidence:

            if isinstance(item, dict):

                for value in item.values():

                    if value:
                        parts.append(
                            _safe_string(value)
                        )

            elif item:

                parts.append(
                    _safe_string(item)
                )

    return "\n".join(parts)


# ============================================================
# LINKEDIN TEXT EXTRACTION
# ============================================================

def extract_linkedin_text(
    linkedin_evidence: dict,
) -> str:
    """Convert LinkedIn data into searchable text."""

    if not isinstance(linkedin_evidence, dict):
        return ""

    parts = []

    # --------------------------------------------------------
    # PROFILE FIELDS
    # --------------------------------------------------------

    profile_keys = [
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
    ]

    for key in profile_keys:

        value = linkedin_evidence.get(key)

        if value:
            parts.append(
                _safe_string(value)
            )

    # --------------------------------------------------------
    # LIST FIELDS
    # --------------------------------------------------------

    for key in [
        "skills",
        "experience",
        "education",
    ]:

        values = linkedin_evidence.get(
            key,
            [],
        )

        if isinstance(values, list):

            for item in values:

                if isinstance(item, dict):

                    for value in item.values():

                        if value:
                            parts.append(
                                _safe_string(value)
                            )

                elif item:

                    parts.append(
                        _safe_string(item)
                    )

        elif values:

            parts.append(
                _safe_string(values)
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
    3. Language statistics
    4. Topics
    5. technology_evidence
    6. skill_evidence
    """

    if not isinstance(github_evidence, dict):
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

    if isinstance(repositories, list):

        for repository in repositories:

            if not isinstance(repository, dict):
                continue

            repository_name = _safe_string(
                repository.get(
                    "name",
                    "",
                )
            )

            evidence_types = set()

            # ------------------------------------------------
            # TECHNOLOGIES
            # ------------------------------------------------

            technologies = repository.get(
                "technologies",
                [],
            )

            if isinstance(technologies, list):

                for technology in technologies:

                    if claim_matches(
                        claim,
                        technology,
                    ):
                        evidence_types.add(
                            "technology"
                        )

            # ------------------------------------------------
            # PRIMARY LANGUAGE
            # ------------------------------------------------

            language = repository.get(
                "language",
                "",
            )

            if language:

                if claim_matches(
                    claim,
                    language,
                ):
                    evidence_types.add(
                        "language"
                    )

            # ------------------------------------------------
            # LANGUAGE STATISTICS
            # ------------------------------------------------

            languages = repository.get(
                "languages",
                {},
            )

            if isinstance(languages, dict):

                for language_name in languages.keys():

                    if claim_matches(
                        claim,
                        language_name,
                    ):
                        evidence_types.add(
                            "languages"
                        )

            # ------------------------------------------------
            # TOPICS
            # ------------------------------------------------

            topics = repository.get(
                "topics",
                [],
            )

            for topic in topics:

                if claim_matches(
                    claim,
                    topic,
                ):
                    evidence_types.add("topic")

            # ------------------------------------------------
            # SAVE REPOSITORY MATCH
            # ------------------------------------------------

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
    # GLOBAL GITHUB EVIDENCE
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

        if not isinstance(evidence, list):
            continue

        for item in evidence:

            if isinstance(item, dict):
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
    # BUILD RESULT
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
                    f"GitHub "
                    f"{evidence_type.replace('_', ' ')} "
                    f"contains evidence for "
                    f"'{claim}'."
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
# SINGLE CLAIM VERIFICATION
# ============================================================

def verify_claim_with_rag(
    claim: str,
    resume_text: str = "",
    github_evidence: Optional[dict] = None,
    linkedin_evidence: Optional[dict] = None,
) -> dict:
    """
    Verify one candidate claim.

    Status meanings:

    supported:
        Credible external evidence exists.

    partially_supported:
        Some external evidence exists but is limited.

    needs_review:
        Claim exists in resume but external verification
        is insufficient.

    unsupported:
        No meaningful evidence was found.
    """

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

    claim_text = _safe_string(
        claim
    ).strip()

    # ========================================================
    # EMPTY CLAIM
    # ========================================================

    if not claim_text:

        return {
            "status": "needs_review",
            "confidence": 0,
            "evidence": [],
            "sources": [],
        }

    # ========================================================
    # 1. RESUME
    # ========================================================

    resume_result = find_best_text_evidence(
        claim=claim_text,
        evidence_text=resume_text,
        source_name="resume",
    )

    # ========================================================
    # 2. GITHUB
    # ========================================================

    github_structured = (
        find_github_structured_evidence(
            claim=claim_text,
            github_evidence=github_evidence,
        )
    )

    if github_structured.get(
        "matched",
        False,
    ):

        github_result = {
            "source": "github",
            "matched": True,
            "confidence": safe_confidence(
                github_structured.get(
                    "confidence",
                    0,
                )
            ),
            "evidence": github_structured.get(
                "evidence",
                "",
            ),
            "repositories": github_structured.get(
                "repositories",
                [],
            ),
        }

    else:

        # ----------------------------------------------------
        # FALLBACK: STRICT GITHUB TEXT SEARCH
        # ----------------------------------------------------

        github_text = extract_github_text(
            github_evidence
        )

        github_text_result = (
            find_best_text_evidence(
                claim=claim_text,
                evidence_text=github_text,
                source_name="github",
            )
        )

        github_result = {
            "source": "github",
            "matched": github_text_result.get(
                "matched",
                False,
            ),
            "confidence": safe_confidence(
                github_text_result.get(
                    "confidence",
                    0,
                )
            ),
            "evidence": github_text_result.get(
                "evidence",
                "",
            ),
            "repositories": [],
        }

    # ========================================================
    # 3. LINKEDIN
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
    # 4. EXTERNAL RESULTS
    # ========================================================

    external_results = [
        github_result,
        linkedin_result,
    ]

    external_matches = [
        result
        for result in external_results
        if result.get(
            "matched",
            False,
        )
    ]

    # ========================================================
    # 5. BUILD EVIDENCE
    # ========================================================

    evidence = []

    for result in external_matches:

        evidence_text = _safe_string(
            result.get(
                "evidence",
                "",
            )
        )

        if evidence_text:

            evidence.append(
                {
                    "source": result.get(
                        "source",
                        "",
                    ),
                    "text": evidence_text,
                    "confidence": safe_confidence(
                        result.get(
                            "confidence",
                            0,
                        )
                    ),
                }
            )

    sources = [
        result.get(
            "source",
            "",
        )
        for result in external_matches
    ]

    # ========================================================
    # 6. EXTERNAL EVIDENCE EXISTS
    # ========================================================

    if external_matches:

        confidences = [
            safe_confidence(
                result.get(
                    "confidence",
                    0,
                )
            )
            for result in external_matches
        ]

        highest_confidence = max(
            confidences,
            default=0,
        )

        # ----------------------------------------------------
        # SINGLE SOURCE
        # ----------------------------------------------------

        if len(external_matches) == 1:

            confidence = highest_confidence

        # ----------------------------------------------------
        # MULTIPLE SOURCES
        # ----------------------------------------------------

        else:

            average_confidence = (
                sum(confidences)
                / len(confidences)
            )

            confidence = max(
                highest_confidence,
                average_confidence,
            )

            # Corroboration bonus.
            confidence += 10

            confidence = min(
                confidence,
                100,
            )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if confidence >= 75:

            status = "supported"

        elif confidence >= 50:

            status = "partially_supported"

        else:

            status = "needs_review"

        return {
            "status": status,
            "confidence": round(
                confidence
            ),
            "evidence": evidence,
            "sources": sources,
        }

    # ========================================================
    # 7. RESUME ONLY
    # ========================================================

    if resume_result.get(
        "matched",
        False,
    ):

        resume_confidence = safe_confidence(
            resume_result.get(
                "confidence",
                0,
            )
        )

        return {
            "status": "needs_review",
            "confidence": round(
                max(
                    20,
                    min(
                        resume_confidence,
                        60,
                    ),
                )
            ),
            "evidence": [
                {
                    "source": "resume",
                    "text": resume_result.get(
                        "evidence",
                        "",
                    ),
                    "confidence": resume_confidence,
                }
            ],
            "sources": [
                "resume"
            ],
        }

    # ========================================================
    # 8. NOTHING FOUND
    # ========================================================

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
    github_evidence: Optional[dict] = None,
    linkedin_evidence: Optional[dict] = None,
) -> list:
    """Verify multiple claims."""

    verified_claims = []

    if not isinstance(claims, list):
        return verified_claims

    for claim in claims:

        try:

            # ------------------------------------------------
            # Extract claim text
            # ------------------------------------------------

            if isinstance(claim, dict):

                claim_text = _safe_string(
                    claim.get(
                        "claim",
                        "",
                    )
                ).strip()

            else:

                claim_text = _safe_string(
                    claim
                ).strip()

            # ------------------------------------------------
            # Verify
            # ------------------------------------------------

            result = verify_claim_with_rag(
                claim=claim_text,
                resume_text=resume_text,
                github_evidence=github_evidence,
                linkedin_evidence=linkedin_evidence,
            )

            print(
                "RAG RAW RESULT:",
                repr(result),
            )

            # ------------------------------------------------
            # Update original claim
            # ------------------------------------------------

            if isinstance(claim, dict):

                updated_claim = dict(
                    claim
                )

                updated_claim[
                    "rag_status"
                ] = result.get(
                    "status",
                    "needs_review",
                )

                updated_claim[
                    "rag_confidence"
                ] = result.get(
                    "confidence",
                    0,
                )

                updated_claim[
                    "rag_evidence"
                ] = result.get(
                    "evidence",
                    [],
                )

                updated_claim[
                    "rag_sources"
                ] = result.get(
                    "sources",
                    [],
                )

                verified_claims.append(
                    updated_claim
                )

            else:

                verified_claims.append(
                    {
                        "claim": claim_text,
                        "rag_status": result.get(
                            "status",
                            "needs_review",
                        ),
                        "rag_confidence": result.get(
                            "confidence",
                            0,
                        ),
                        "rag_evidence": result.get(
                            "evidence",
                            [],
                        ),
                        "rag_sources": result.get(
                            "sources",
                            [],
                        ),
                    }
                )

        except Exception as exc:

            # ------------------------------------------------
            # One bad claim must not crash pipeline.
            # ------------------------------------------------

            print(
                f"RAG verification error: "
                f"{claim!r}"
            )

            print(
                "Error:",
                repr(exc),
            )

            if isinstance(
                claim,
                dict,
            ):

                failed_claim = dict(
                    claim
                )

                failed_claim[
                    "rag_status"
                ] = "needs_review"

                failed_claim[
                    "rag_confidence"
                ] = 0

                failed_claim[
                    "rag_evidence"
                ] = []

                failed_claim[
                    "rag_sources"
                ] = []

                verified_claims.append(
                    failed_claim
                )

            else:

                verified_claims.append(
                    {
                        "claim": _safe_string(
                            claim
                        ),
                        "rag_status": "needs_review",
                        "rag_confidence": 0,
                        "rag_evidence": [],
                        "rag_sources": [],
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
    Lightweight lexical RAG retrieval.

    Searches candidate knowledge and returns
    the five most relevant chunks.
    """

    query_text = _safe_string(
        query
    ).strip()

    knowledge_text = _safe_string(
        candidate_knowledge
    ).strip()

    # --------------------------------------------------------
    # EMPTY QUERY
    # --------------------------------------------------------

    if not query_text:

        return {
            "query": query,
            "evidence": [],
            "chunks": [],
            "count": 0,
        }

    # --------------------------------------------------------
    # EMPTY KNOWLEDGE
    # --------------------------------------------------------

    if not knowledge_text:

        return {
            "query": query,
            "evidence": [],
            "chunks": [],
            "count": 0,
        }

    query_tokens = tokenize(
        query_text
    )

    if not query_tokens:

        return {
            "query": query,
            "evidence": [],
            "chunks": [],
            "count": 0,
        }

    # ========================================================
    # SPLIT KNOWLEDGE INTO CHUNKS
    # ========================================================

    raw_chunks = re.split(
        r"\n\s*\n|(?<=[.!?])\s+",
        knowledge_text,
    )

    chunks = [
        chunk.strip()
        for chunk in raw_chunks
        if chunk and chunk.strip()
    ]

    # ========================================================
    # SCORE CHUNKS
    # ========================================================

    scored_chunks = []

    for chunk in chunks:

        chunk_tokens = tokenize(
            chunk
        )

        if not chunk_tokens:
            continue

        overlap = query_tokens.intersection(
            chunk_tokens
        )

        if not overlap:
            continue

        score = (
            len(overlap)
            / max(
                len(query_tokens),
                1,
            )
        )

        scored_chunks.append(
            {
                "text": chunk[:1000],
                "score": round(
                    min(
                        score,
                        1.0,
                    ),
                    2,
                ),
                "matched_terms": sorted(
                    overlap
                ),
            }
        )

    # ========================================================
    # SORT
    # ========================================================

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # ========================================================
    # TOP FIVE
    # ========================================================

    top_chunks = scored_chunks[:5]

    return {
        "query": query,
        "evidence": top_chunks,
        "chunks": top_chunks,
        "count": len(top_chunks),
    }


# ============================================================
# OPTIONAL ALIAS
# ============================================================

def verify_candidate_claims(
    claims: list,
    resume_text: str = "",
    github_evidence: Optional[dict] = None,
    linkedin_evidence: Optional[dict] = None,
) -> list:
    """Compatibility alias."""

    return verify_claims_with_rag(
        claims=claims,
        resume_text=resume_text,
        github_evidence=github_evidence,
        linkedin_evidence=linkedin_evidence,
    )


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("PERSONADNA RAG ENGINE TEST")
    print("=" * 60)

    test_claims = [
        {
            "claim": "Python",
            "type": "skill",
        },
        {
            "claim": "Java",
            "type": "skill",
        },
        {
            "claim": "JavaScript",
            "type": "skill",
        },
        {
            "claim": "SQL",
            "type": "skill",
        },
        {
            "claim": "React",
            "type": "skill",
        },
        {
            "claim": "FastAPI",
            "type": "skill",
        },
        {
            "claim": "Flask",
            "type": "skill",
        },
        {
            "claim": "Machine Learning",
            "type": "skill",
        },
        {
            "claim": "AI",
            "type": "skill",
        },
    ]

    test_resume = """
    Gadewar Sohan is a Data Science student.

    Skills include Python, Java, JavaScript, React,
    FastAPI, Flask, SQL, PostgreSQL, AI and Machine Learning.
    """

    test_github = {

        "username": "sohangadewar",

        "bio": "AI developer and Data Science student",

        "repositories": [

            {
                "name": "PersonaDNA",

                "language": "Python",

                "technologies": [
                    "Python",
                    "FastAPI",
                    "AI",
                ],

                "topics": [
                    "artificial-intelligence",
                    "rag",
                ],
            },

            {
                "name": "Smart-Attendance-System",

                "language": "JavaScript",

                "technologies": [
                    "JavaScript",
                    "Flask",
                ],
            },
        ],
    }

    test_linkedin = {

        "display_name": "Gadewar Sohan",

        "headline": "Data Science Student and AI Developer",

        "skills": [
            "Python",
            "Artificial Intelligence",
        ],
    }

    results = verify_claims_with_rag(
        claims=test_claims,
        resume_text=test_resume,
        github_evidence=test_github,
        linkedin_evidence=test_linkedin,
    )

    print()
    print("=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)

    for index, result in enumerate(
        results,
        start=1,
    ):

        print()

        print(
            f"CLAIM #{index}: "
            f"{result.get('claim')}"
        )

        print(
            "RAG Status:",
            result.get(
                "rag_status"
            ),
        )

        print(
            "RAG Confidence:",
            result.get(
                "rag_confidence"
            ),
        )

        print(
            "RAG Sources:",
            result.get(
                "rag_sources"
            ),
        )

    print()
    print("=" * 60)
    print("RAG ENGINE TEST COMPLETE")
    print("=" * 60)