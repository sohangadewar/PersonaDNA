import re


# ============================================================
# NAME NORMALIZATION
# ============================================================

def normalize_name(name: str) -> str:
    """
    Normalize a person's name for identity comparison.

    Examples:
        GADEWAR SOHAN -> gadewar sohan
        Sohan Gadewar -> gadewar sohan
        Gadewar, Sohan -> gadewar sohan
    """

    name = str(name or "").strip().lower()

    if not name:
        return ""

    # Remove email addresses
    name = re.sub(
        r"\b[\w.+-]+@[\w.-]+\.\w+\b",
        " ",
        name,
    )

    # Remove URLs
    name = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        name,
    )

    # Replace punctuation with spaces
    name = re.sub(
        r"[^a-z0-9\s]",
        " ",
        name,
    )

    # Remove extra whitespace
    parts = [
        part
        for part in name.split()
        if part
    ]

    # Name order does not matter
    return " ".join(sorted(parts))


# ============================================================
# NAME TOKEN EXTRACTION
# ============================================================

def _name_tokens(name: str) -> set[str]:
    normalized = normalize_name(name)

    if not normalized:
        return set()

    return set(normalized.split())


# ============================================================
# RESUME NAME EXTRACTION
# ============================================================

def extract_resume_name(resume_text: str) -> str:
    """
    Extract candidate name from the beginning of the resume.
    """

    if not resume_text:
        return ""

    lines = [
        line.strip()
        for line in resume_text.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    ignored_patterns = [
        r"@",
        r"https?://",
        r"www\.",
        r"\bresume\b",
        r"\bcurriculum vitae\b",
        r"\bobjective\b",
        r"\bsummary\b",
        r"\bprofile\b",
        r"\beducation\b",
        r"\bskills\b",
        r"\bexperience\b",
        r"\bprojects\b",
        r"\bcertifications?\b",
        r"\bcontact\b",
        r"\bphone\b",
        r"\bmobile\b",
        r"\blinkedin\b",
        r"\bgithub\b",
    ]

    # Check first 15 meaningful lines
    for line in lines[:15]:

        candidate = re.sub(
            r"[^A-Za-z\s.'-]",
            " ",
            line,
        )

        candidate = " ".join(
            candidate.split()
        ).strip()

        if not candidate:
            continue

        lower_candidate = candidate.lower()

        # Skip headings/contact information
        if any(
            re.search(
                pattern,
                lower_candidate,
            )
            for pattern in ignored_patterns
        ):
            continue

        words = candidate.split()

        # Normal candidate name: 2-4 words
        if not 2 <= len(words) <= 4:
            continue

        if len(candidate) > 60:
            continue

        # Avoid phone numbers
        if re.search(
            r"\d{5,}",
            line,
        ):
            continue

        if not re.search(
            r"[A-Za-z]",
            candidate,
        ):
            continue

        return candidate

    # Fallback
    first_line = re.sub(
        r"[^A-Za-z\s.'-]",
        " ",
        lines[0],
    )

    return " ".join(
        first_line.split()
    ).strip()


# ============================================================
# GENERIC NAME MATCHING
# ============================================================

def names_match(
    name_a: str,
    name_b: str,
) -> bool:

    normalized_a = normalize_name(name_a)
    normalized_b = normalize_name(name_b)

    if not normalized_a or not normalized_b:
        return False

    return normalized_a == normalized_b


# ============================================================
# IDENTITY COMPARISON
# ============================================================

def compare_identity(
    resume_name: str,
    github: str = "",
    linkedin: str = "",
    github_display_name: str = "",
) -> dict:
    """
    Compare resume identity with GitHub and LinkedIn identity.

    Name order does not matter.

    Example:
        Resume: Sohan Gadewar
        GitHub: Gadewar Sohan

        Result:
            github_match = True
    """

    resume_normalized = normalize_name(
        resume_name
    )

    github_normalized = normalize_name(
        github_display_name
    )

    linkedin_normalized = normalize_name(
        linkedin
    )

    github_match = names_match(
        resume_name,
        github_display_name,
    )

    linkedin_match = names_match(
        resume_name,
        linkedin,
    )

    github_username_score = (
        100
        if github_match
        else 0
    )

    linkedin_username_score = (
        100
        if linkedin_match
        else 0
    )

    return {
        "resume_name": resume_name,
        "github_username": github,
        "linkedin_username": linkedin,
        "github_display_name": github_display_name,

        "github_match": github_match,
        "linkedin_match": linkedin_match,

        "github_username_score": github_username_score,
        "linkedin_username_score": linkedin_username_score,

        "resume_normalized": resume_normalized,
        "github_normalized": github_normalized,
        "linkedin_normalized": linkedin_normalized,
    }