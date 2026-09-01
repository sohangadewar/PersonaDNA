import re

from typing import Any


# ============================================================
# CONFIGURATION
# ============================================================

SKILL_ALIASES = {
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

    "react.js": {
        "react",
        "reactjs",
        "react.js",
    },

    "fastapi": {
        "fastapi",
    },

    "flask": {
        "flask",
    },

    "sql": {
        "sql",
    },

    "python": {
        "python",
    },

    "java": {
        "java",
    },

    "c": {
        "c",
    },

    "html": {
        "html",
        "html5",
    },

    "css": {
        "css",
        "css3",
    },

    "git": {
        "git",
    },

    "github": {
        "github",
    },

    "google cloud": {
        "google cloud",
        "gcp",
        "google-cloud",
    },

    "rag": {
        "rag",
        "retrieval augmented generation",
        "retrieval-augmented generation",
    },

    "langchain": {
        "langchain",
    },

    "data science": {
        "data science",
    },

    "rest api": {
        "rest api",
        "rest",
        "restful api",
    },

    "rest": {
        "rest",
        "rest api",
        "restful api",
    },
}


# ============================================================
# BASIC HELPERS
# ============================================================

def _safe_string(value: Any) -> str:
    """
    Safely convert any value to string.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value

    try:
        return str(value)

    except Exception:
        return ""


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(text: Any) -> str:
    """
    Normalize text for deterministic matching.
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

    text = text.replace(
        "google-cloud",
        "google cloud",
    )

    text = text.replace(
        "retrieval-augmented-generation",
        "retrieval augmented generation",
    )

    # Keep letters, numbers, +, #, ., -, and spaces
    text = re.sub(
        r"[^a-z0-9+#.\- ]+",
        " ",
        text,
    )

    # Remove repeated spaces
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# CANONICAL SKILL
# ============================================================

def canonical_skill(skill: Any) -> str:
    """
    Convert a skill into one canonical representation.
    """

    normalized = normalize_text(skill)

    if not normalized:
        return ""

    for canonical, aliases in SKILL_ALIASES.items():

        normalized_aliases = {
            normalize_text(alias)
            for alias in aliases
        }

        if normalized in normalized_aliases:
            return canonical

    return normalized


# ============================================================
# SKILL ALIASES
# ============================================================

def skill_aliases(skill: Any) -> set[str]:
    """
    Return all known aliases for a skill.
    """

    normalized = normalize_text(skill)

    if not normalized:
        return set()

    canonical = canonical_skill(normalized)

    aliases = SKILL_ALIASES.get(
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
# EXACT SKILL MATCHING
# ============================================================

def skill_matches(
    claimed_skill: Any,
    observed_skill: Any,
) -> bool:
    """
    Strict skill matching.

    Important:

        Java != JavaScript
        SQL != SQLAlchemy
        C != CSS

    Known aliases are supported.
    """

    observed = normalize_text(observed_skill)

    if not observed:
        return False

    aliases = skill_aliases(claimed_skill)

    for alias in aliases:

        alias = normalize_text(alias)

        if not alias:
            continue

        # Exact match
        if observed == alias:
            return True

        # Boundary-aware match
        pattern = (
            rf"(?<![a-z0-9])"
            rf"{re.escape(alias)}"
            rf"(?![a-z0-9])"
        )

        if re.search(
            pattern,
            observed,
        ):
            return True

    return False


# ============================================================
# EXACT REPOSITORY EVIDENCE
# ============================================================

def repository_has_skill(
    skill: str,
    repository: dict,
) -> tuple[bool, list[str]]:
    """
    Determine whether a repository contains evidence
    for a specific skill.

    Evidence sources:

        - technologies
        - primary language
        - additional languages
    """

    if not isinstance(
        repository,
        dict,
    ):
        return False, []

    evidence_sources = []

    # --------------------------------------------------------
    # TECHNOLOGY EVIDENCE
    # --------------------------------------------------------

    technologies = repository.get(
        "technologies",
        [],
    )

    if isinstance(
        technologies,
        list,
    ):

        for technology in technologies:

            if skill_matches(
                skill,
                technology,
            ):

                evidence_sources.append(
                    "technology"
                )

                break

    # --------------------------------------------------------
    # PRIMARY LANGUAGE
    # --------------------------------------------------------

    language = repository.get(
        "language",
        "",
    )

    if language:

        if skill_matches(
            skill,
            language,
        ):

            evidence_sources.append(
                "language"
            )

    # --------------------------------------------------------
    # LANGUAGE STATISTICS
    # --------------------------------------------------------

    languages = repository.get(
        "languages",
        {},
    )

    if isinstance(
        languages,
        dict,
    ):

        for language_name in languages.keys():

            if skill_matches(
                skill,
                language_name,
            ):

                evidence_sources.append(
                    "languages"
                )

                break

    evidence_sources = sorted(
        set(evidence_sources)
    )

    return (
        bool(evidence_sources),
        evidence_sources,
    )


# ============================================================
# SKILL → REPOSITORY MAPPING
# ============================================================

def map_skill_to_repositories(
    skill: str,
    repositories: list[dict],
) -> list[dict]:
    """
    Return only repositories that genuinely support
    the requested skill.
    """

    if not isinstance(
        repositories,
        list,
    ):
        return []

    matches = []

    for repository in repositories:

        if not isinstance(
            repository,
            dict,
        ):
            continue

        matched, evidence_sources = (
            repository_has_skill(
                skill,
                repository,
            )
        )

        if not matched:
            continue

        matches.append(
            {
                "repository": _safe_string(
                    repository.get(
                        "name",
                        "",
                    )
                ),

                "matched_evidence": (
                    evidence_sources
                ),

                "language": _safe_string(
                    repository.get(
                        "language",
                        "",
                    )
                ),

                "technologies": (
                    repository.get(
                        "technologies",
                        [],
                    )
                    if isinstance(
                        repository.get(
                            "technologies",
                            [],
                        ),
                        list,
                    )
                    else []
                ),

                "languages": (
                    repository.get(
                        "languages",
                        {},
                    )
                    if isinstance(
                        repository.get(
                            "languages",
                            {},
                        ),
                        dict,
                    )
                    else {}
                ),

                "has_readme": bool(
                    repository.get(
                        "has_readme",
                        False,
                    )
                ),

                "dependency_files": (
                    repository.get(
                        "dependency_files",
                        {},
                    )
                    if isinstance(
                        repository.get(
                            "dependency_files",
                            {},
                        ),
                        dict,
                    )
                    else {}
                ),
            }
        )

    return matches


# ============================================================
# BUILD REPOSITORY SKILL MAPPING
# ============================================================

def build_repository_skill_mapping(
    claims: list[dict],
    github_evidence: dict,
) -> dict:
    """
    Build:

        skill → repositories

    mapping.
    """

    if not isinstance(
        claims,
        list,
    ):
        return {}

    if not isinstance(
        github_evidence,
        dict,
    ):
        return {}

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    mapping = {}

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

        skill = _safe_string(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        if not skill:
            continue

        mapping[skill] = (
            map_skill_to_repositories(
                skill,
                repositories,
            )
        )

    return mapping


# ============================================================
# AUTHORITATIVE EVIDENCE SCORE
# ============================================================

def calculate_evidence_strength(
    claim: dict,
    repository_matches: list[dict],
    github_evidence: dict,
) -> dict:
    """
    Single authoritative evidence scoring model.

    Score:

        Resume evidence          = 20
        GitHub repository match  = 30
        Exact technology         = 20
        GitHub language          = 15
        Multiple repositories    = 10
        README evidence          = 5

    Maximum = 100.

    This score measures evidence strength.
    It does NOT automatically prove the candidate's claim.
    """

    score = 0
    reasons = []

    # --------------------------------------------------------
    # RESUME
    # --------------------------------------------------------

    claim_evidence = claim.get(
        "evidence",
        {},
    )

    if not isinstance(
        claim_evidence,
        dict,
    ):
        claim_evidence = {}

    resume_evidence = claim_evidence.get(
        "resume",
        True,
    )

    if resume_evidence:
        score += 20

        reasons.append(
            "Claim appears in the resume."
        )

    # --------------------------------------------------------
    # GITHUB PROFILE
    # --------------------------------------------------------

    github_profile_found = bool(
        github_evidence.get(
            "profile_found",
            True,
        )
    )

    # --------------------------------------------------------
    # NO REPOSITORY MATCH
    # --------------------------------------------------------

    if not repository_matches:

        return {
            "score": score,
            "level": (
                "Weak"
                if score > 0
                else "None"
            ),
            "reasons": reasons,
        }

    # --------------------------------------------------------
    # GITHUB REPOSITORY EVIDENCE
    # --------------------------------------------------------

    if github_profile_found:

        score += 30

        reasons.append(
            "Matching GitHub repository evidence was found."
        )

    # --------------------------------------------------------
    # EXACT TECHNOLOGY
    # --------------------------------------------------------

    technology_matches = sum(
        1
        for repository in repository_matches
        if "technology"
        in repository.get(
            "matched_evidence",
            [],
        )
    )

    if technology_matches > 0:

        score += 20

        reasons.append(
            "The exact technology was found in repository metadata."
        )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language_matches = sum(
        1
        for repository in repository_matches
        if (
            "language"
            in repository.get(
                "matched_evidence",
                [],
            )
            or
            "languages"
            in repository.get(
                "matched_evidence",
                [],
            )
        )
    )

    if language_matches > 0:

        score += 15

        reasons.append(
            "Repository language supports the claim."
        )

    # --------------------------------------------------------
    # MULTIPLE REPOSITORIES
    # --------------------------------------------------------

    if len(repository_matches) >= 2:

        score += 10

        reasons.append(
            "The claim is supported across multiple repositories."
        )

    # --------------------------------------------------------
    # README
    # --------------------------------------------------------

    if any(
        repository.get(
            "has_readme",
            False,
        )
        for repository in repository_matches
    ):

        score += 5

        reasons.append(
            "Supporting repository contains a README."
        )

    # --------------------------------------------------------
    # CLAMP
    # --------------------------------------------------------

    score = min(
        score,
        100,
    )

    # --------------------------------------------------------
    # LEVEL
    # --------------------------------------------------------

    if score >= 80:
        level = "Strong"

    elif score >= 60:
        level = "Moderate"

    elif score >= 20:
        level = "Weak"

    else:
        level = "None"

    return {
        "score": score,
        "level": level,
        "reasons": reasons,
    }


# ============================================================
# AUTHORITATIVE EVIDENCE REPORT
# ============================================================

def build_evidence_report(
    claims: list[dict],
    github_evidence: dict,
) -> list[dict]:
    """
    Single source of truth for GitHub skill evidence.

    Every skill claim uses the same:

        claim
            ↓
        repository matching
            ↓
        evidence scoring
            ↓
        evidence report
    """

    if not isinstance(
        claims,
        list,
    ):
        return []

    if not isinstance(
        github_evidence,
        dict,
    ):
        github_evidence = {}

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    report = []

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

        claim_name = _safe_string(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        if not claim_name:
            continue

        repository_matches = (
            map_skill_to_repositories(
                claim_name,
                repositories,
            )
        )

        strength = (
            calculate_evidence_strength(
                claim=claim,
                repository_matches=repository_matches,
                github_evidence=github_evidence,
            )
        )

        report.append(
            {
                "claim": claim_name,

                "type": "skill",

                "score": strength[
                    "score"
                ],

                "level": strength[
                    "level"
                ],

                "reasons": strength[
                    "reasons"
                ],

                "github_repository_count": (
                    len(repository_matches)
                ),

                "github_repositories": [
                    item.get(
                        "repository",
                        "",
                    )
                    for item in repository_matches
                ],
            }
        )

    return report


# ============================================================
# CLAIM ENRICHMENT
# ============================================================

def enrich_claims_with_github(
    claims: list[dict],
    github_evidence: dict,
) -> list[dict]:
    """
    Add GitHub evidence to claims.

    Important:
    This function only records evidence.

    It does NOT make the final verification decision.
    RAG performs final claim verification.
    """

    if not isinstance(
        claims,
        list,
    ):
        return []

    if not isinstance(
        github_evidence,
        dict,
    ):
        github_evidence = {}

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    github_found = bool(
        github_evidence.get(
            "profile_found",
            False,
        )
    )

    for claim in claims:

        if not isinstance(
            claim,
            dict,
        ):
            continue

        # ----------------------------------------------------
        # Preserve existing evidence
        # ----------------------------------------------------

        evidence = claim.get(
            "evidence",
            {},
        )

        if not isinstance(
            evidence,
            dict,
        ):
            evidence = {}

        evidence.setdefault(
            "resume",
            True,
        )

        evidence.setdefault(
            "github",
            False,
        )

        evidence.setdefault(
            "linkedin",
            False,
        )

        claim["evidence"] = evidence

        # ----------------------------------------------------
        # Non-skill claims
        # ----------------------------------------------------

        if claim.get(
            "type"
        ) != "skill":

            claim.setdefault(
                "status",
                "detected",
            )

            continue

        # ----------------------------------------------------
        # Repository matching
        # ----------------------------------------------------

        skill = _safe_string(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        matches = (
            map_skill_to_repositories(
                skill,
                repositories,
            )
        )

        github_match = bool(
            github_found
            and matches
        )

        # ----------------------------------------------------
        # Record GitHub evidence
        # ----------------------------------------------------

        evidence[
            "github"
        ] = github_match

        claim[
            "evidence"
        ] = evidence

        # ----------------------------------------------------
        # Do not decide final verification here
        # ----------------------------------------------------

        claim[
            "status"
        ] = "detected"

    return claims


# ============================================================
# CLAIM STATISTICS
# ============================================================

def calculate_claim_stats(
    claims: list[dict],
) -> dict:
    """
    Calculate final claim statistics.

    Supports:

        supported
        partially_supported
        needs_review
        unsupported
    """

    if not isinstance(
        claims,
        list,
    ):
        return {
            "detected": 0,
            "supported": 0,
            "partially_supported": 0,
            "needs_review": 0,
            "unsupported": 0,
        }

    supported_statuses = {
        "supported",
        "verified",
        "confirmed",
    }

    partial_statuses = {
        "partially_supported",
        "partial",
    }

    needs_review_statuses = {
        "needs_review",
        "review",
    }

    unsupported_statuses = {
        "unsupported",
    }

    supported = 0
    partially_supported = 0
    needs_review = 0
    unsupported = 0

    for claim in claims:

        if not isinstance(
            claim,
            dict,
        ):
            continue

        status = str(
            claim.get(
                "status",
                claim.get(
                    "rag_status",
                    "",
                ),
            )
        ).lower().strip()

        if status in supported_statuses:

            supported += 1

        elif status in partial_statuses:

            partially_supported += 1

        elif status in needs_review_statuses:

            needs_review += 1

        elif status in unsupported_statuses:

            unsupported += 1

    return {
        "detected": len(claims),

        "supported": supported,

        "partially_supported": (
            partially_supported
        ),

        "needs_review": needs_review,

        "unsupported": unsupported,
    }