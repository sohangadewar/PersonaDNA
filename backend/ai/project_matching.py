from difflib import SequenceMatcher
import re


# ============================================================
# Normalization
# ============================================================

def normalize_text(
    text: str,
) -> str:

    if not text:
        return ""

    text = str(
        text
    ).lower()

    text = re.sub(
        r"[-_/|]+",
        " ",
        text,
    )

    text = re.sub(
        r"[^a-z0-9\s+#.]",
        " ",
        text,
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def normalize_technology(
    technology: str,
) -> str:

    value = normalize_text(
        technology
    )

    aliases = {
        "reactjs": "react",
        "react.js": "react",

        "nodejs": "node.js",
        "node": "node.js",

        "expressjs": "express.js",
        "express": "express.js",

        "js": "javascript",
        "ts": "typescript",

        "mongo": "mongodb",

        "mysql": "sql",
        "postgresql": "sql",
        "postgres": "sql",
        "sqlite": "sql",

        "artificial intelligence": "ai",
    }

    return aliases.get(
        value,
        value,
    )


# ============================================================
# Project name similarity
# ============================================================

def project_name_similarity(
    project_name: str,
    repository_name: str,
) -> float:

    project = normalize_text(
        project_name
    )

    repository = normalize_text(
        repository_name
    )

    if not project or not repository:
        return 0.0

    if project == repository:
        return 100.0

    if (
        project in repository
        or repository in project
    ):
        return 92.0

    project_words = set(
        project.split()
    )

    repository_words = set(
        repository.split()
    )

    common_words = (
        project_words
        & repository_words
    )

    word_score = 0.0

    if project_words:

        word_score = (
            len(common_words)
            / len(project_words)
        ) * 100

    sequence_score = (
        SequenceMatcher(
            None,
            project,
            repository,
        ).ratio()
        * 100
    )

    return round(
        max(
            word_score,
            sequence_score,
        ),
        2,
    )


# ============================================================
# Technology overlap
# ============================================================

def technology_overlap(
    project_technologies,
    repository_technologies,
):

    project_set = {
        normalize_technology(
            item
        )
        for item in project_technologies
    }

    repository_set = {
        normalize_technology(
            item
        )
        for item in repository_technologies
    }

    if not project_set:
        return 0.0, []

    matched = (
        project_set
        & repository_set
    )

    score = (
        len(matched)
        / len(project_set)
    ) * 100

    return (
        round(
            score,
            2,
        ),
        sorted(
            matched
        ),
    )


# ============================================================
# Match one project
# ============================================================

def match_project_to_repository(
    project,
    repository,
):

    project_name = project.get(
        "claim",
        "",
    )

    project_text = project.get(
        "project_text",
        project_name,
    )

    project_technologies = project.get(
        "technologies",
        [],
    )

    repository_name = repository.get(
        "name",
        "",
    )

    repository_technologies = repository.get(
        "technologies",
        [],
    )

    name_score = project_name_similarity(
        project_name,
        repository_name,
    )

    technology_score, matched_technologies = (
        technology_overlap(
            project_technologies,
            repository_technologies,
        )
    )

    description = normalize_text(
        repository.get(
            "description",
            "",
        )
    )

    project_text_normalized = normalize_text(
        project_text
    )

    description_score = 0

    if description:

        project_words = set(
            project_text_normalized.split()
        )

        description_words = set(
            description.split()
        )

        overlap = (
            project_words
            & description_words
        )

        if len(overlap) >= 5:
            description_score = 15

        elif len(overlap) >= 3:
            description_score = 8

    readme_score = (
        5
        if repository.get(
            "has_readme",
            False,
        )
        else 0
    )

    supporting_score = (
        description_score
        + readme_score
    )

    final_score = (
        name_score * 0.55
        + technology_score * 0.30
        + supporting_score
    )

    final_score = round(
        min(
            final_score,
            100,
        ),
        2,
    )

    # Require meaningful project-name evidence.
    if (
        name_score >= 75
        and final_score >= 70
    ):

        status = "matched"
        strength = "strong"

    elif (
        name_score >= 50
        and final_score >= 50
    ):

        status = "possible_match"
        strength = "moderate"

    else:

        status = "needs_review"
        strength = "weak"

    signals = []

    if name_score >= 75:
        signals.append(
            "strong project name similarity"
        )

    elif name_score >= 50:
        signals.append(
            "partial project name similarity"
        )

    if matched_technologies:
        signals.append(
            "technology overlap"
        )

    if description_score:
        signals.append(
            "repository description overlap"
        )

    if readme_score:
        signals.append(
            "repository has README"
        )

    return {
        "resume_project": project_name,
        "github_repository": (
            repository_name
            if status
            in {
                "matched",
                "possible_match",
            }
            else None
        ),
        "match_score": final_score,
        "match_strength": strength,
        "status": status,
        "name_score": name_score,
        "technology_score": technology_score,
        "description_score": description_score,
        "readme_score": readme_score,
        "project_technologies": project_technologies,
        "matched_technologies": matched_technologies,
        "matched_signals": signals,
    }


# ============================================================
# Best repository + alternatives
# ============================================================

def match_project_to_repositories(
    project,
    repositories,
):

    if not repositories:

        return {
            "resume_project": project.get(
                "claim",
                "",
            ),
            "github_repository": None,
            "match_score": 0,
            "match_strength": "weak",
            "status": "needs_review",
            "project_technologies": project.get(
                "technologies",
                [],
            ),
            "matched_technologies": [],
            "matched_signals": [],
            "alternative_matches": [],
        }

    matches = []

    for repository in repositories:

        result = match_project_to_repository(
            project,
            repository,
        )

        # Keep actual repository name for ranking
        result["_repository_name"] = repository.get(
            "name",
            "",
        )

        matches.append(
            result
        )

    matches.sort(
        key=lambda item: item[
            "match_score"
        ],
        reverse=True,
    )

    best = matches[0]

    alternatives = []

    for candidate in matches[1:4]:

        alternatives.append(
            {
                "repository": candidate.get(
                    "_repository_name",
                    "",
                ),
                "score": candidate.get(
                    "match_score",
                    0,
                ),
                "status": candidate.get(
                    "status",
                    "needs_review",
                ),
            }
        )

    best[
        "alternative_matches"
    ] = alternatives

    best.pop(
        "_repository_name",
        None,
    )

    for item in matches:
        item.pop(
            "_repository_name",
            None,
        )

    return best


# ============================================================
# Build all project mappings
# ============================================================

def build_project_repository_mapping(
    claims,
    github_evidence,
):

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    project_claims = [
        claim
        for claim in claims
        if claim.get(
            "type"
        ) == "project"
    ]

    results = []

    for project in project_claims:

        results.append(
            match_project_to_repositories(
                project,
                repositories,
            )
        )

    return results