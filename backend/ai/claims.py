import re


# ============================================================
# Helpers
# ============================================================

def normalize_space(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text or "",
    ).strip()


def contains_term(
    text: str,
    term: str,
) -> bool:
    """
    Strict technology/skill matching.

    Examples:
        Java       -> matches "Java"
        Java       -> DOES NOT match "JavaScript"
        SQL        -> matches "SQL"
        SQL        -> DOES NOT match "SQLAlchemy"
        JavaScript -> matches "JavaScript"
    """

    text = text or ""
    term = normalize_space(term)

    if not text or not term:
        return False

    pattern = (
        r"(?<![A-Za-z0-9+#])"
        + re.escape(term)
        + r"(?![A-Za-z0-9+#])"
    )

    return (
        re.search(
            pattern,
            text,
            re.IGNORECASE,
        )
        is not None
    )


def value_matches_skill(
    candidate_value,
    skill: str,
) -> bool:
    """
    Safely checks one GitHub value against a claimed skill.

    Handles strings, lists, tuples, sets and dictionaries.
    """

    if candidate_value is None:
        return False

    if isinstance(candidate_value, dict):
        values = list(candidate_value.keys())

        for value in candidate_value.values():
            if isinstance(value, (str, int, float)):
                values.append(str(value))

        return any(
            value_matches_skill(value, skill)
            for value in values
        )

    if isinstance(candidate_value, (list, tuple, set)):
        return any(
            value_matches_skill(value, skill)
            for value in candidate_value
        )

    return contains_term(
        str(candidate_value),
        skill,
    )


# ============================================================
# Skills
# ============================================================

SKILL_PATTERNS = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Node.js",
    "FastAPI",
    "Flask",
    "Django",
    "SQL",
    "MongoDB",
    "PostgreSQL",
    "Machine Learning",
    "Deep Learning",
    "Artificial Intelligence",
    "AI",
    "Data Science",
    "Data Analysis",
    "Git",
    "GitHub",
    "Docker",
    "AWS",
    "Google Cloud",
]


# ============================================================
# Canonical Skill Names
# ============================================================

CANONICAL_SKILLS = {
    "AI": "Artificial Intelligence",
    "Artificial Intelligence": "Artificial Intelligence",

    "ML": "Machine Learning",
    "Machine Learning": "Machine Learning",

    "JS": "JavaScript",
    "JavaScript": "JavaScript",

    "TS": "TypeScript",
    "TypeScript": "TypeScript",

    "Postgres": "PostgreSQL",
    "PostgreSQL": "PostgreSQL",
}


def canonicalize_skill(skill: str) -> str:
    normalized = normalize_space(skill)

    for name, canonical in CANONICAL_SKILLS.items():

        if normalized.lower() == name.lower():
            return canonical

    return normalized


# ============================================================
# Education
# ============================================================

EDUCATION_PATTERNS = [
    r"\bB\.?\s*Tech\b",
    r"\bBachelor of Technology\b",
    r"\bM\.?\s*Tech\b",
    r"\bMaster of Technology\b",
    r"\bB\.?\s*Sc\b",
    r"\bM\.?\s*Sc\b",
    r"\bMBA\b",
    r"\bIntermediate\b",
    r"\b12th\b",
    r"\b10th\b",
]


# ============================================================
# Certifications
# ============================================================

CERTIFICATION_PATTERNS = [
    r"\bcertificate\b",
    r"\bcertification\b",
    r"\bcertified\b",
]


# ============================================================
# Project Technologies
# ============================================================

PROJECT_TECHNOLOGIES = [
    "Python",
    "Java",
    "C++",
    "C",
    "JavaScript",
    "TypeScript",
    "React",
    "ReactJS",
    "Node.js",
    "NodeJS",
    "Express.js",
    "ExpressJS",
    "FastAPI",
    "Flask",
    "Django",
    "SQL",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "Redis",
    "Docker",
    "AWS",
    "Google Cloud",
    "AI",
    "Artificial Intelligence",
    "Machine Learning",
    "Deep Learning",
    "Pandas",
    "NumPy",
    "Scikit-learn",
]


def extract_project_technologies(
    text: str,
) -> list[str]:

    found = []

    for technology in PROJECT_TECHNOLOGIES:

        if contains_term(
            text,
            technology,
        ):

            if technology not in found:
                found.append(technology)

    return found


# ============================================================
# Project Name Cleaning
# ============================================================

def clean_project_name(
    project_name: str,
) -> str:

    value = normalize_space(
        project_name
    )

    value = re.sub(
        r"^\s*\d+\s*[\.\):\-]\s*",
        "",
        value,
    )

    value = re.sub(
        r"^[\-\*•‣●]+\s*",
        "",
        value,
    )

    value = re.sub(
        r"^(project|projects|personal projects)"
        r"\s*[:\-]?\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )

    stop_patterns = [
        r"\bwebsite\b",
        r"\bgithub link\b",
        r"\blinkedin\b",
        r"\bbackend\b",
        r"\bfrontend\b",
        r"\bdescription\b",
        r"\bdeveloped\b",
        r"\bbuilt\b",
        r"\busing\b",
        r"\btech stack\b",
    ]

    for pattern in stop_patterns:

        match = re.search(
            pattern,
            value,
            re.IGNORECASE,
        )

        if match:

            value = value[
                :match.start()
            ]

            break

    value = value.strip(
        " :-|.,;"
    )

    if not value:
        return ""

    if len(value) > 80:
        return ""

    ignored = {
        "project",
        "projects",
        "personal projects",
        "experience",
        "work experience",
        "skills",
        "education",
    }

    if value.lower() in ignored:
        return ""

    return value


# ============================================================
# Project Extraction
# ============================================================

def extract_project_claims(
    resume_text: str,
) -> list[dict]:

    original_text = resume_text or ""

    normalized_text = normalize_space(
        original_text
    )

    projects = []

    section_match = re.search(
        r"(?:personal\s+projects|projects)"
        r"\s*:\s*"
        r"(.*?)"
        r"(?="
        r"\b(?:work experience|experience|education|"
        r"skills|certifications|certificate)\b"
        r"|$)",
        normalized_text,
        re.IGNORECASE,
    )

    if section_match:

        section_text = (
            section_match
            .group(1)
            .strip()
        )

        numbered_matches = re.findall(
            r"(?:^|\s)"
            r"(\d+)"
            r"\.\s*"
            r"(.+?)"
            r"(?=\s+\d+\.\s+|$)",
            section_text,
            re.IGNORECASE,
        )

        for _, raw_project in numbered_matches:

            raw_project = raw_project.strip()

            project_name = clean_project_name(
                raw_project
            )

            if not project_name:
                continue

            projects.append(
                {
                    "claim": project_name,
                    "type": "project",
                    "status": "detected",
                    "project_text": raw_project,
                    "technologies": (
                        extract_project_technologies(
                            raw_project
                        )
                    ),
                }
            )

    explicit_matches = re.findall(
        r"(?:project|project name)"
        r"\s*[:\-]\s*"
        r"([A-Za-z0-9][A-Za-z0-9 _\-]{2,80})",
        original_text,
        re.IGNORECASE,
    )

    for raw_project in explicit_matches:

        project_name = clean_project_name(
            raw_project
        )

        if not project_name:
            continue

        projects.append(
            {
                "claim": project_name,
                "type": "project",
                "status": "detected",
                "project_text": raw_project,
                "technologies": (
                    extract_project_technologies(
                        raw_project
                    )
                ),
            }
        )

    unique = {}

    for project in projects:

        key = normalize_space(
            project["claim"]
        ).lower()

        if key not in unique:
            unique[key] = project

    return list(
        unique.values()
    )


# ============================================================
# Certification Extraction
# ============================================================

def extract_certification_claims(
    resume_text: str,
) -> list[dict]:

    text = resume_text or ""

    certifications = []

    section_match = re.search(
        r"(?:certifications?|certificates?|credentials?)"
        r"\s*[:\-]?\s*"
        r"(.*?)"
        r"(?="
        r"\b(?:projects?|personal projects|education|"
        r"experience|work experience|skills|technical skills)\b"
        r"|$)",
        normalize_space(text),
        re.IGNORECASE,
    )

    if not section_match:
        return certifications

    section_text = (
        section_match
        .group(1)
        .strip()
    )

    entries = re.split(
        r"\s*(?:\||•|▪|◦|●|\n)\s*"
        r"|\s+(?=\d+[\.\):\-]\s+)",
        section_text,
    )

    for entry in entries:

        entry = normalize_space(
            entry
        )

        if not entry:
            continue

        entry = re.sub(
            r"^\s*\d+\s*[\.\):\-]\s*",
            "",
            entry,
        )

        entry = re.sub(
            r"^[\-\*•▪◦●]+\s*",
            "",
            entry,
        )

        entry = re.sub(
            r"\b(?:credential\s*)?(?:id|ID)"
            r"\s*[:#\-]?\s*\S+",
            "",
            entry,
            flags=re.IGNORECASE,
        )

        entry = re.sub(
            r"\b(?:credential\s*)?(?:url|link)"
            r"\s*[:\-]?\s*\S+",
            "",
            entry,
            flags=re.IGNORECASE,
        )

        entry = normalize_space(
            entry
        )

        if not entry:
            continue

        if entry.lower() in {
            "certificate",
            "certificates",
            "certification",
            "certifications",
            "credentials",
        }:
            continue

        if len(entry) > 180:
            continue

        certifications.append(
            {
                "claim": entry,
                "type": "certification",
                "status": "detected",
                "evidence": {
                    "resume": True,
                    "github": False,
                    "linkedin": False,
                },
            }
        )

    unique = {}

    for certification in certifications:

        key = normalize_space(
            certification["claim"]
        ).lower()

        if key not in unique:
            unique[key] = certification

    return list(
        unique.values()
    )


# ============================================================
# Main Claim Extraction
# ============================================================

def extract_claims(
    resume_text: str,
) -> list[dict]:

    text = resume_text or ""

    claims = []

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    for skill in SKILL_PATTERNS:

        if contains_term(
            text,
            skill,
        ):

            claims.append(
                {
                    "claim": canonicalize_skill(
                        skill
                    ),
                    "type": "skill",
                    "status": "detected",
                    "evidence": {
                        "resume": True,
                        "github": False,
                        "linkedin": False,
                    },
                }
            )

    # --------------------------------------------------------
    # Education
    # --------------------------------------------------------

    for pattern in EDUCATION_PATTERNS:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            claims.append(
                {
                    "claim": normalize_space(
                        match.group(0)
                    ),
                    "type": "education",
                    "status": "detected",
                    "evidence": {
                        "resume": True,
                        "github": False,
                        "linkedin": False,
                    },
                }
            )

    # --------------------------------------------------------
    # Certifications
    # --------------------------------------------------------

    claims.extend(
        extract_certification_claims(
            text
        )
    )

    # --------------------------------------------------------
    # Projects
    # --------------------------------------------------------

    claims.extend(
        extract_project_claims(
            text
        )
    )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    unique = {}

    for claim in claims:

        if not isinstance(
            claim,
            dict,
        ):
            continue

        claim_name = normalize_space(
            str(
                claim.get(
                    "claim",
                    "",
                )
            )
        )

        if not claim_name:
            continue

        claim_type = normalize_space(
            str(
                claim.get(
                    "type",
                    "",
                )
            )
        ).lower()

        key = (
            claim_type,
            claim_name.lower(),
        )

        if key not in unique:

            claim["claim"] = claim_name

            claim.setdefault(
                "status",
                "detected",
            )

            claim.setdefault(
                "evidence",
                {
                    "resume": True,
                    "github": False,
                    "linkedin": False,
                },
            )

            unique[key] = claim

    return list(
        unique.values()
    )


# ============================================================
# GitHub Repository Helpers
# ============================================================

def get_repository_name(
    repository: dict,
) -> str:

    if not isinstance(
        repository,
        dict,
    ):
        return ""

    return normalize_space(
        str(
            repository.get(
                "name",
                repository.get(
                    "repository",
                    "",
                ),
            )
        )
    )


def get_repository_values(
    repository: dict,
) -> list:

    """
    Collect only meaningful GitHub repository
    technology-related fields.

    Important:
    We keep values separate so Java does not
    accidentally match JavaScript.
    """

    if not isinstance(
        repository,
        dict,
    ):
        return []

    values = []

    fields = [
        "technology",
        "technologies",
        "language",
        "languages",
        "topics",
        "skills",
    ]

    for field in fields:

        value = repository.get(
            field
        )

        if value is None:
            continue

        if isinstance(
            value,
            dict,
        ):

            values.extend(
                str(key)
                for key in value.keys()
            )

        elif isinstance(
            value,
            (list, tuple, set),
        ):

            values.extend(
                str(item)
                for item in value
            )

        else:

            values.append(
                str(value)
            )

    return values


# ============================================================
# GitHub Claim Matching
# ============================================================

def match_github_claim(
    claim: str,
    github_evidence: dict,
) -> dict:
    """
    Strictly match a claim against the actual GitHub
    repository technology/language evidence.

    Important:
    Do NOT trust precomputed repository_matches because
    those may contain false substring matches.

    Examples:
        Java       != JavaScript
        SQL        != SQLAlchemy
    """

    result = {
        "verified": False,
        "repositories": [],
        "repository_matches": [],
        "technology_matches": [],
    }

    if not isinstance(
        github_evidence,
        dict,
    ):
        return result

    claim = canonicalize_skill(claim)

    if not claim:
        return result

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if isinstance(
        repositories,
        dict,
    ):
        repositories = list(
            repositories.values()
        )

    if not isinstance(
        repositories,
        list,
    ):
        repositories = []

    # --------------------------------------------------------
    # Match ONLY against actual repository fields
    # --------------------------------------------------------

    for repository in repositories:

        if not isinstance(
            repository,
            dict,
        ):
            continue

        repository_name = get_repository_name(
            repository
        )

        matched_values = []

        # --------------------------------------------
        # Technology
        # --------------------------------------------

        technology = repository.get(
            "technology"
        )

        if technology is not None:

            if value_matches_skill(
                technology,
                claim,
            ):
                matched_values.append(
                    str(technology)
                )

        # --------------------------------------------
        # Technologies
        # --------------------------------------------

        technologies = repository.get(
            "technologies"
        )

        if technologies is not None:

            if isinstance(
                technologies,
                dict,
            ):
                technology_values = list(
                    technologies.keys()
                )
            elif isinstance(
                technologies,
                (list, tuple, set),
            ):
                technology_values = list(
                    technologies
                )
            else:
                technology_values = [
                    technologies
                ]

            for value in technology_values:

                value = str(value)

                if contains_term(
                    value,
                    claim,
                ):
                    if value not in matched_values:
                        matched_values.append(
                            value
                        )

        # --------------------------------------------
        # Primary language
        # --------------------------------------------

        language = repository.get(
            "language"
        )

        if language is not None:

            if contains_term(
                str(language),
                claim,
            ):
                if str(language) not in matched_values:
                    matched_values.append(
                        str(language)
                    )

        # --------------------------------------------
        # Language statistics
        # --------------------------------------------

        languages = repository.get(
            "languages"
        )

        if isinstance(
            languages,
            dict,
        ):

            for language_name in languages.keys():

                language_name = str(
                    language_name
                )

                if contains_term(
                    language_name,
                    claim,
                ):
                    if (
                        language_name
                        not in matched_values
                    ):
                        matched_values.append(
                            language_name
                        )

        elif isinstance(
            languages,
            (list, tuple, set),
        ):

            for language_name in languages:

                language_name = str(
                    language_name
                )

                if contains_term(
                    language_name,
                    claim,
                ):
                    if (
                        language_name
                        not in matched_values
                    ):
                        matched_values.append(
                            language_name
                        )

        # --------------------------------------------
        # Topics
        # --------------------------------------------

        topics = repository.get(
            "topics"
        )

        if topics is not None:

            if isinstance(
                topics,
                (list, tuple, set),
            ):
                topic_values = topics
            else:
                topic_values = [
                    topics
                ]

            for topic in topic_values:

                topic = str(topic)

                if contains_term(
                    topic,
                    claim,
                ):
                    if topic not in matched_values:
                        matched_values.append(
                            topic
                        )

        # --------------------------------------------
        # Skills
        # --------------------------------------------

        skills = repository.get(
            "skills"
        )

        if skills is not None:

            if isinstance(
                skills,
                (list, tuple, set),
            ):
                skill_values = skills
            else:
                skill_values = [
                    skills
                ]

            for skill in skill_values:

                skill = str(skill)

                if contains_term(
                    skill,
                    claim,
                ):
                    if skill not in matched_values:
                        matched_values.append(
                            skill
                        )

        # --------------------------------------------
        # Save only genuine matches
        # --------------------------------------------

        if matched_values:

            result["verified"] = True

            if repository_name:

                if (
                    repository_name
                    not in result[
                        "repositories"
                    ]
                ):
                    result[
                        "repositories"
                    ].append(
                        repository_name
                    )

            result[
                "repository_matches"
            ].append(
                {
                    "repository": repository_name,
                    "matched_evidence": (
                        matched_values
                    ),
                }
            )

            for value in matched_values:

                if (
                    value
                    not in result[
                        "technology_matches"
                    ]
                ):
                    result[
                        "technology_matches"
                    ].append(
                        value
                    )

    # --------------------------------------------------------
    # Global technology evidence
    # --------------------------------------------------------

    global_evidence = github_evidence.get(
        "technology_evidence",
        [],
    )

    if isinstance(
        global_evidence,
        dict,
    ):
        global_evidence = list(
            global_evidence.keys()
        )

    if isinstance(
        global_evidence,
        (list, tuple, set),
    ):

        for technology in global_evidence:

            technology = str(
                technology
            )

            if contains_term(
                technology,
                claim,
            ):

                result["verified"] = True

                if (
                    technology
                    not in result[
                        "technology_matches"
                    ]
                ):
                    result[
                        "technology_matches"
                    ].append(
                        technology
                    )

    # --------------------------------------------------------
    # Global skill evidence
    # --------------------------------------------------------

    skill_evidence = github_evidence.get(
        "skill_evidence",
        [],
    )

    if isinstance(
        skill_evidence,
        dict,
    ):
        skill_evidence = list(
            skill_evidence.keys()
        )

    if isinstance(
        skill_evidence,
        (list, tuple, set),
    ):

        for skill in skill_evidence:

            skill = str(skill)

            if contains_term(
                skill,
                claim,
            ):

                result["verified"] = True

                if (
                    skill
                    not in result[
                        "technology_matches"
                    ]
                ):
                    result[
                        "technology_matches"
                    ].append(
                        skill
                    )

    return result