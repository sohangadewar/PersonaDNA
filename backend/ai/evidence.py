from typing import Any


# ============================================================
# Normalization
# ============================================================

def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def canonical_skill(skill: str) -> str:
    """
    Convert common aliases to one canonical skill name.
    """

    value = normalize_text(skill)

    aliases = {
        "python": "python",

        "java": "java",

        "javascript": "javascript",
        "js": "javascript",

        "typescript": "typescript",
        "ts": "typescript",

        "react": "react",
        "reactjs": "react",
        "react.js": "react",

        "node": "node.js",
        "nodejs": "node.js",
        "node.js": "node.js",

        "express": "express.js",
        "expressjs": "express.js",
        "express.js": "express.js",

        "fastapi": "fastapi",
        "flask": "flask",
        "django": "django",

        "sql": "sql",
        "mysql": "sql",
        "postgres": "sql",
        "postgresql": "sql",
        "sqlite": "sql",

        "mongodb": "mongodb",
        "mongo": "mongodb",
        "mongoose": "mongodb",

        "machine learning": "machine learning",
        "ml": "machine learning",
        "scikit-learn": "machine learning",
        "sklearn": "machine learning",

        "deep learning": "deep learning",
        "tensorflow": "deep learning",
        "pytorch": "deep learning",

        "artificial intelligence": "ai",
        "ai": "ai",

        "data science": "data science",
        "pandas": "data science",
        "numpy": "data science",

        "data analysis": "data analysis",

        "git": "git",
        "github": "github",

        "docker": "docker",

        "aws": "aws",
        "amazon web services": "aws",

        "google cloud": "google cloud",
        "gcp": "google cloud",
    }

    return aliases.get(
        value,
        value,
    )


# ============================================================
# Exact repository evidence
# ============================================================

def repository_has_skill(
    skill: str,
    repository: dict,
) -> tuple[bool, list[str]]:
    """
    Determine whether a repository contains genuine evidence
    for a specific skill.

    Evidence sources:
        - technologies
        - primary language
        - additional languages
    """

    target = canonical_skill(skill)

    evidence_sources = []

    # --------------------------------------------------------
    # Technology evidence
    # --------------------------------------------------------

    technologies = repository.get(
        "technologies",
        [],
    )

    if isinstance(technologies, list):

        for technology in technologies:

            if (
                canonical_skill(
                    str(technology)
                )
                == target
            ):

                evidence_sources.append(
                    "technology"
                )

                break

    # --------------------------------------------------------
    # Primary language
    # --------------------------------------------------------

    language = repository.get(
        "language",
        "",
    )

    if language:

        if (
            canonical_skill(
                str(language)
            )
            == target
        ):

            evidence_sources.append(
                "language"
            )

    # --------------------------------------------------------
    # Language statistics
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

            if (
                canonical_skill(
                    str(language_name)
                )
                == target
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
# Skill → Repository mapping
# ============================================================

def map_skill_to_repositories(
    skill: str,
    repositories: list[dict],
) -> list[dict]:
    """
    Return only repositories that genuinely support
    the requested skill.
    """

    matches = []

    for repository in repositories:

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
                "repository": repository.get(
                    "name",
                    "",
                ),
                "matched_evidence": evidence_sources,
                "language": repository.get(
                    "language",
                    "",
                ),
                "technologies": repository.get(
                    "technologies",
                    [],
                ),
                "languages": repository.get(
                    "languages",
                    {},
                ),
                "has_readme": bool(
                    repository.get(
                        "has_readme",
                        False,
                    )
                ),
                "dependency_files": repository.get(
                    "dependency_files",
                    {},
                ),
            }
        )

    return matches


def build_repository_skill_mapping(
    claims: list[dict],
    github_evidence: dict,
) -> dict:

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    mapping = {}

    for claim in claims:

        if claim.get(
            "type"
        ) != "skill":
            continue

        skill = str(
            claim.get(
                "claim",
                "",
            )
        )

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
        Resume evidence           = 20
        GitHub repository match   = 30
        Exact technology          = 20
        GitHub language           = 15
        Multiple repositories     = 10
        README evidence           = 5

    Maximum = 100.

    Important:
    The existence of a matched repository always creates
    external GitHub evidence.
    """

    score = 0
    reasons = []

    # --------------------------------------------------------
    # Resume
    # --------------------------------------------------------

    if claim.get(
        "evidence",
        {},
    ).get(
        "resume",
        True,
    ):

        score += 20

        reasons.append(
            "Claim appears in the resume."
        )

    # --------------------------------------------------------
    # No GitHub repository match
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
    # GitHub repository evidence
    # --------------------------------------------------------

    score += 30

    reasons.append(
        "Matching GitHub repository evidence was found."
    )

    # --------------------------------------------------------
    # Exact technology
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
    # Language
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
    # Multiple repositories
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
    # Clamp
    # --------------------------------------------------------

    score = min(
        score,
        100,
    )

    # --------------------------------------------------------
    # Level
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
    The single source of truth for claim evidence.

    Every skill claim is evaluated through the same
    repository-matching and scoring functions.
    """

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    report = []

    for claim in claims:

        if claim.get(
            "type"
        ) != "skill":
            continue

        claim_name = str(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        repository_matches = (
            map_skill_to_repositories(
                claim_name,
                repositories,
            )
        )

        strength = calculate_evidence_strength(
            claim,
            repository_matches,
            github_evidence,
        )

        report.append(
            {
                "claim": claim_name,
                "type": "skill",
                "score": strength["score"],
                "level": strength["level"],
                "reasons": strength["reasons"],
                "github_repository_count": len(
                    repository_matches
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
# Claim enrichment
# ============================================================

def enrich_claims_with_github(
    claims: list[dict],
    github_evidence: dict,
) -> list[dict]:

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

        claim.setdefault(
            "evidence",
            {
                "resume": True,
                "github": False,
                "linkedin": False,
            },
        )

        if claim.get(
            "type"
        ) != "skill":

            claim["status"] = "detected"
            continue

        matches = map_skill_to_repositories(
            str(
                claim.get(
                    "claim",
                    "",
                )
            ),
            repositories,
        )

        github_match = bool(
            github_found
            and matches
        )

        claim["evidence"][
            "github"
        ] = github_match

        claim["status"] = (
            "supported"
            if github_match
            else "needs_review"
        )

    return claims


# ============================================================
# Claim statistics
# ============================================================

def calculate_claim_stats(
    claims: list[dict],
) -> dict:

    return {
        "detected": len(
            claims
        ),
        "supported": sum(
            1
            for claim in claims
            if claim.get(
                "status"
            ) == "supported"
        ),
        "needs_review": sum(
            1
            for claim in claims
            if claim.get(
                "status"
            ) == "needs_review"
        ),
    }