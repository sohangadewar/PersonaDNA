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

    pattern = r"(?<![A-Za-z0-9+#])" + re.escape(term) + r"(?![A-Za-z0-9+#])"

    return (
        re.search(
            pattern,
            text or "",
            re.IGNORECASE,
        )
        is not None
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
                found.append(technology)

    return found


# ============================================================
# Project name cleaning
# ============================================================


def clean_project_name(
    project_name: str,
) -> str:

    value = normalize_space(project_name)

    value = re.sub(
        r"^\s*\d+\s*[\.\):\-]\s*",
        "",
        value,
    )

    value = re.sub(
        r"^[\-\*\u2022\u2023\u25CF]+\s*",
        "",
        value,
    )

    value = re.sub(
        r"^(project|projects|personal projects)" r"\s*[:\-]?\s*",
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
            value = value[: match.start()]
            break

    value = value.strip(" :-|.,;")

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

    original_text = resume_text or ""

    normalized_text = normalize_space(original_text)

    projects = []

    section_match = re.search(
        r"(?:personal\s+projects|projects)"
        r"\s*:\s*"
        r"(.*?)(?="
        r"\b(?:work experience|experience|education|"
        r"skills|certifications|certificate)\b"
        r"|$)",
        normalized_text,
        re.IGNORECASE,
    )

    if section_match:

        section_text = section_match.group(1).strip()

        numbered_matches = re.findall(
            r"(?:^|\s)" r"(\d+)" r"\.\s*" r"(.+?)" r"(?=\s+\d+\.\s+|$)",
            section_text,
            re.IGNORECASE,
        )

        for _, raw_project in numbered_matches:

            raw_project = raw_project.strip()

            project_name = clean_project_name(raw_project)

            if not project_name:
                continue

            projects.append(
                {
                    "claim": project_name,
                    "type": "project",
                    "status": "detected",
                    "project_text": raw_project,
                    "technologies": (extract_project_technologies(raw_project)),
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

        project_name = clean_project_name(raw_project)

        if not project_name:
            continue

        projects.append(
            {
                "claim": project_name,
                "type": "project",
                "status": "detected",
                "project_text": raw_project,
                "technologies": (extract_project_technologies(raw_project)),
            }
        )

    unique = {}

    for project in projects:

        key = normalize_space(project["claim"]).lower()

        if key not in unique:
            unique[key] = project

    return list(unique.values())


# ============================================================
# Certification extraction
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

    section_text = section_match.group(1).strip()

    entries = re.split(
        r"\s*(?:\||•|▪|◦|●|\n)\s*" r"|\s+(?=\d+[\.\):\-]\s+)",
        section_text,
    )

    for entry in entries:

        entry = normalize_space(entry)

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
            r"\b(?:credential\s*)?(?:id|ID)" r"\s*[:#\-]?\s*\S+",
            "",
            entry,
            flags=re.IGNORECASE,
        )

        entry = re.sub(
            r"\b(?:credential\s*)?(?:url|link)" r"\s*[:\-]?\s*\S+",
            "",
            entry,
            flags=re.IGNORECASE,
        )

        entry = normalize_space(entry)

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

        key = normalize_space(certification["claim"]).lower()

        if key not in unique:
            unique[key] = certification

    return list(unique.values())


# ============================================================
# Main claim extraction
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
                    "claim": skill,
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
                    "claim": normalize_space(match.group(0)),
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

    claims.extend(extract_certification_claims(text))

    # --------------------------------------------------------
    # Projects
    # --------------------------------------------------------

    claims.extend(extract_project_claims(text))

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

    return list(unique.values())
