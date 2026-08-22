import re
from typing import Any


# ============================================================
# NAME NORMALIZATION
# ============================================================

def normalize_name(name: str) -> str:
    """
    Normalize a person's name for identity comparison.

    Examples:
        GADEWAR SOHAN -> gadewar sohan
        Sohan Gadewar -> gadewar sohan
    """

    name = str(name or "").strip().lower()

    name = re.sub(
        r"[^a-z0-9\s]",
        " ",
        name,
    )

    parts = [
        part
        for part in name.split()
        if part
    ]

    return " ".join(sorted(parts))


# ============================================================
# RESUME NAME EXTRACTION
# ============================================================

def extract_resume_name(resume_text: str) -> str:
    """
    Extract the candidate name from the beginning of the resume.

    PersonaDNA resumes normally contain the name near the
    beginning of the document.
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

    # First meaningful line is normally the candidate name.
    first_line = lines[0]

    # Remove common unwanted characters.
    first_line = re.sub(
        r"[^A-Za-z\s.'-]",
        " ",
        first_line,
    )

    first_line = " ".join(
        first_line.split()
    )

    return first_line.strip()


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
    Compare resume identity with authorized external
    profile names.

    Name order does not matter.

    Example:
        GADEWAR SOHAN
        Sohan Gadewar

    Both normalize to:
        gadewar sohan
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

    # ==================================================
    # GITHUB IDENTITY
    # ==================================================

    github_match = False

    if (
        resume_normalized
        and github_normalized
    ):
        github_match = (
            resume_normalized
            == github_normalized
        )

    # ==================================================
    # LINKEDIN IDENTITY
    # ==================================================

    linkedin_match = False

    if (
        resume_normalized
        and linkedin_normalized
    ):
        linkedin_match = (
            resume_normalized
            == linkedin_normalized
        )

    # ==================================================
    # SCORES
    # ==================================================

    github_username_score = (
        100 if github_match else 0
    )

    linkedin_username_score = (
        100 if linkedin_match else 0
    )

    return {
        "resume_name": resume_name,

        "github_username": github,

        "linkedin_username": linkedin,

        "github_display_name": github_display_name,

        "github_match": github_match,

        "linkedin_match": linkedin_match,

        "github_username_score": (
            github_username_score
        ),

        "linkedin_username_score": (
            linkedin_username_score
        ),

        "resume_normalized": (
            resume_normalized
        ),

        "github_normalized": (
            github_normalized
        ),

        "linkedin_normalized": (
            linkedin_normalized
        ),
    }