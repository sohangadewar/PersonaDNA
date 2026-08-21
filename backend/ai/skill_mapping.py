def normalize_skill(skill: str) -> str:
    """
    Normalize skill names so equivalent technologies
    can be compared reliably.
    """

    skill = str(skill).strip().lower()

    aliases = {
        "reactjs": "react",
        "react.js": "react",

        "nodejs": "node.js",
        "node": "node.js",

        "javascript": "javascript",
        "js": "javascript",

        "typescript": "typescript",
        "ts": "typescript",

        "mongodb": "mongodb",
        "mongo": "mongodb",

        "mysql": "sql",
        "postgresql": "sql",
        "postgres": "sql",

        "artificial intelligence": "ai",
        "machine learning": "ai",

        "scikit-learn": "scikit-learn",
        "sklearn": "scikit-learn",

        "google cloud": "google cloud",
        "gcp": "google cloud",
    }

    return aliases.get(skill, skill)


def build_skill_repository_mapping(
    claims: list[dict],
    github_evidence: dict,
) -> list[dict]:
    """
    Map resume skill claims to GitHub repositories
    containing technical evidence for those skills.
    """

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    mapping = []

    for claim in claims:

        if claim.get("type") != "skill":
            continue

        skill = str(
            claim.get("claim", "")
        ).strip()

        if not skill:
            continue

        normalized_skill = normalize_skill(
            skill
        )

        matching_repositories = []

        for repo in repositories:

            technologies = repo.get(
                "technologies",
                [],
            )

            normalized_technologies = [
                normalize_skill(
                    technology
                )
                for technology in technologies
            ]

            if (
                normalized_skill
                in normalized_technologies
            ):
                matching_repositories.append(
                    {
                        "repository": repo.get(
                            "name"
                        ),
                        "technologies": technologies,
                        "language": repo.get(
                            "language"
                        ),
                        "has_readme": repo.get(
                            "has_readme",
                            False,
                        ),
                    }
                )

        repository_count = len(
            matching_repositories
        )

        if repository_count >= 3:
            evidence_strength = "strong"

        elif repository_count >= 1:
            evidence_strength = "moderate"

        else:
            evidence_strength = "weak"

        mapping.append(
            {
                "skill": skill,
                "normalized_skill": normalized_skill,
                "resume_claim": True,
                "repository_count": repository_count,
                "repositories": matching_repositories,
                "evidence_strength": evidence_strength,
            }
        )

    return mapping