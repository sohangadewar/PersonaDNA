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
    pattern = (
        r"(?<![A-Za-z0-9+#])"
        + re.escape(term)
        + r"(?![A-Za-z0-9+#])"
    )

    return re.search(
        pattern,
        text,
        re.IGNORECASE,
    ) is not None


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
# Project technologies
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
                found.append(
                    technology
                )

    return found


# ============================================================
# Project name cleaning
# ============================================================

def clean_project_name(
    project_name: str,
) -> str:

    value = normalize_space(
        project_name
    )

    # Remove numbering
    value = re.sub(
        r"^\s*\d+\s*[\.\):\-]\s*",
        "",
        value,
    )

    # Remove bullets
    value = re.sub(
        r"^[\-\*\u2022\u2023\u25CF]+\s*",
        "",
        value,
    )

    # Remove project labels
    value = re.sub(
        r"^(project|projects|personal projects)\s*[:\-]?\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # Stop at obvious metadata
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
            value = value[:match.start()]
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
# Project extraction
# ============================================================

def extract_project_claims(
    resume_text: str,
) -> list[dict]:

    # PDF extraction can destroy the original layout,
    # so inspect both original lines and a normalized form.
    original_text = resume_text or ""

    normalized_text = normalize_space(
        original_text
    )

    projects = []

    # --------------------------------------------------------
    # 1. Look specifically for a Personal Projects section
    # --------------------------------------------------------

    section_match = re.search(
        r"(?:personal\s+projects|projects)"
        r"\s*:\s*"
        r"(.*?)(?="
        r"\b(?:work experience|experience|education|skills|certifications|certificate)\b"
        r"|$)",
        normalized_text,
        re.IGNORECASE,
    )

    if section_match:

        section_text = section_match.group(
            1
        ).strip()

        # Find numbered projects:
        # 1. Food Delivery App
        # 2. PlacementGPT
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

            # Keep useful project text for matching
            project_text = raw_project

            projects.append(
                {
                    "claim": project_name,
                    "type": "project",
                    "status": "detected",
                    "project_text": project_text,
                    "technologies": extract_project_technologies(
                        project_text
                    ),
                }
            )

    # --------------------------------------------------------
    # 2. Look for explicit "Project: X"
    # --------------------------------------------------------

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
                "technologies": extract_project_technologies(
                    raw_project
                ),
            }
        )

    # --------------------------------------------------------
    # 3. Deduplicate
    # --------------------------------------------------------

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
# Main claim extraction
# ============================================================

def extract_claims(
    resume_text: str,
) -> list[dict]:

    claims = []

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    for skill in SKILL_PATTERNS:

        if contains_term(
            resume_text,
            skill,
        ):

            claims.append(
                {
                    "claim": skill,
                    "type": "skill",
                    "status": "detected",
                }
            )

    # --------------------------------------------------------
    # Education
    # --------------------------------------------------------

    for pattern in EDUCATION_PATTERNS:

        match = re.search(
            pattern,
            resume_text,
            re.IGNORECASE,
        )

        if match:

            claims.append(
                {
                    "claim": match.group(0),
                    "type": "education",
                    "status": "detected",
                }
            )

    # --------------------------------------------------------
    # Certifications
    # --------------------------------------------------------

    for pattern in CERTIFICATION_PATTERNS:

        match = re.search(
            pattern,
            resume_text,
            re.IGNORECASE,
        )

        if match:

            claims.append(
                {
                    "claim": match.group(0).title(),
                    "type": "certification",
                    "status": "detected",
                }
            )

    # --------------------------------------------------------
    # Projects
    # --------------------------------------------------------

    claims.extend(
        extract_project_claims(
            resume_text
        )
    )

    return claims