import re
from difflib import SequenceMatcher
from urllib.parse import urlparse


# ============================================================
# Normalization
# ============================================================

def normalize_words(name: str) -> list[str]:
    value = str(name or "").lower()

    value = re.sub(
        r"[^a-z\s]",
        " ",
        value,
    )

    return [
        word
        for word in value.split()
        if len(word) > 1
    ]


def normalize_name(name: str) -> str:
    words = normalize_words(name)

    return " ".join(
        sorted(words)
    )


def compact_text(value: str) -> str:
    return re.sub(
        r"[^a-z]",
        "",
        str(value or "").lower(),
    )


# ============================================================
# Name token evidence
# ============================================================

def token_overlap_score(
    first: str,
    second: str,
) -> float:
    """
    Measure meaningful name-word overlap.

    This is more trustworthy than raw character similarity.
    """

    first_words = set(
        normalize_words(first)
    )

    second_words = set(
        normalize_words(second)
    )

    if not first_words or not second_words:
        return 0.0

    shared = (
        first_words
        & second_words
    )

    if not shared:
        return 0.0

    # Score relative to the resume name.
    score = (
        len(shared)
        / len(first_words)
    ) * 100

    return round(
        score,
        2,
    )


# ============================================================
# Character similarity
# ============================================================

def similarity_score(
    first: str,
    second: str,
) -> float:

    first_normalized = normalize_name(
        first
    )

    second_normalized = normalize_name(
        second
    )

    if (
        not first_normalized
        or not second_normalized
    ):
        return 0.0

    return round(
        SequenceMatcher(
            None,
            first_normalized,
            second_normalized,
        ).ratio() * 100,
        2,
    )


# ============================================================
# Conservative name match
# ============================================================

def names_match(
    resume_name: str,
    profile_name: str,
) -> bool:

    if not resume_name or not profile_name:
        return False

    if (
        normalize_name(resume_name)
        == normalize_name(profile_name)
    ):
        return True

    overlap = token_overlap_score(
        resume_name,
        profile_name,
    )

    # Two or more meaningful matching words.
    resume_words = set(
        normalize_words(resume_name)
    )

    profile_words = set(
        normalize_words(profile_name)
    )

    shared_words = (
        resume_words
        & profile_words
    )

    if (
        len(shared_words) >= 2
        and overlap >= 60
    ):
        return True

    # A single meaningful name must be
    # almost exact to qualify.
    if (
        len(resume_words) == 1
        and len(profile_words) == 1
    ):

        return similarity_score(
            resume_name,
            profile_name,
        ) >= 90

    return False


# ============================================================
# Resume name
# ============================================================

def extract_resume_name(
    resume_text: str,
) -> str:

    lines = [
        line.strip()
        for line in resume_text.splitlines()
        if line.strip()
    ]

    return (
        lines[0]
        if lines
        else ""
    )


# ============================================================
# URL username extraction
# ============================================================

def extract_username(
    url: str,
    platform: str = "",
) -> str:

    if not url:
        return ""

    value = str(
        url
    ).strip()

    if not value.startswith(
        (
            "http://",
            "https://",
        )
    ):
        value = "https://" + value

    parsed = urlparse(
        value
    )

    parts = [
        part
        for part in parsed.path.strip("/")
        .split("/")
        if part
    ]

    if not parts:
        return ""

    if (
        platform == "linkedin"
        and len(parts) >= 2
    ):
        return parts[-1]

    return parts[0]


# ============================================================
# Username → name evidence
# ============================================================

def username_name_score(
    resume_name: str,
    username: str,
) -> float:
    """
    Score how much a username corresponds to
    the actual resume name.

    Important:
    Character similarity alone is NOT enough.

    Example:
        Sushant Dilip Yerawar
        sohangadewar

    should remain low because there is no meaningful
    token correspondence.
    """

    if not resume_name or not username:
        return 0.0

    resume_words = normalize_words(
        resume_name
    )

    if not resume_words:
        return 0.0

    username_parts = re.findall(
        r"[a-z]+",
        str(username).lower(),
    )

    if not username_parts:
        return 0.0

    matched_parts = 0

    for part in username_parts:

        # Exact token match
        if part in resume_words:
            matched_parts += 1
            continue

        # Strong prefix match
        for word in resume_words:

            if (
                len(part) >= 4
                and len(word) >= 4
                and (
                    part.startswith(word[:4])
                    or word.startswith(part[:4])
                )
            ):
                matched_parts += 0.5
                break

    score = (
        matched_parts
        / len(resume_words)
    ) * 100

    return round(
        min(score, 100),
        2,
    )


# ============================================================
# Identity status
# ============================================================

def identity_status(
    confidence: float,
    github_match: bool,
    linkedin_match: bool,
) -> str:

    if (
        github_match
        and linkedin_match
    ):
        return "verified"

    if (
        github_match
        or linkedin_match
    ):
        return "partially_verified"

    if confidence >= 65:
        return "probable_match"

    if confidence >= 40:
        return "needs_review"

    return "mismatch"


def identity_recommendation(
    status: str,
) -> str:

    if status == "verified":
        return (
            "GitHub and LinkedIn identities are consistent "
            "with the resume identity."
        )

    if status == "partially_verified":
        return (
            "At least one external profile is consistent "
            "with the resume identity."
        )

    if status == "probable_match":
        return (
            "Identity appears reasonably similar, but "
            "additional verification is recommended."
        )

    if status == "needs_review":
        return (
            "Verify profile ownership before attributing "
            "external evidence to the candidate."
        )

    return (
        "External profile identities do not sufficiently "
        "match the resume identity."
    )


# ============================================================
# Main identity comparison
# ============================================================

def compare_identity(
    resume_name: str,
    github_url: str,
    linkedin_url: str,
    github_display_name: str = "",
) -> dict:

    # --------------------------------------------------------
    # Extract usernames
    # --------------------------------------------------------

    github_username = extract_username(
        github_url,
        "github",
    )

    linkedin_username = extract_username(
        linkedin_url,
        "linkedin",
    )

    # --------------------------------------------------------
    # GitHub display-name evidence
    # --------------------------------------------------------

    github_display_token_score = (
        token_overlap_score(
            resume_name,
            github_display_name,
        )
    )

    github_display_similarity = (
        similarity_score(
            resume_name,
            github_display_name,
        )
    )

    github_display_match = names_match(
        resume_name,
        github_display_name,
    )

    # Display names are the strongest GitHub signal.
    if github_display_match:

        github_display_score = max(
            github_display_token_score,
            github_display_similarity,
        )

    else:

        # If there is no genuine name-token agreement,
        # do not let character similarity inflate the score.
        github_display_score = (
            github_display_token_score * 0.70
            + github_display_similarity * 0.30
        )

        if (
            github_display_token_score == 0
        ):
            github_display_score = min(
                github_display_score,
                25.0,
            )

    # --------------------------------------------------------
    # GitHub username evidence
    # --------------------------------------------------------

    github_username_score = username_name_score(
        resume_name,
        github_username,
    )

    github_username_match = (
        github_username_score >= 75
    )

    # --------------------------------------------------------
    # Combined GitHub identity
    # --------------------------------------------------------

    if github_display_match:

        github_identity_score = max(
            github_display_score,
            85.0,
        )

    else:

        github_identity_score = round(
            (
                github_display_score * 0.75
            )
            + (
                github_username_score * 0.25
            ),
            2,
        )

    github_match = (
        github_display_match
        or (
            github_username_match
            and github_display_score >= 60
        )
    )

    # --------------------------------------------------------
    # LinkedIn username evidence
    # --------------------------------------------------------

    linkedin_score = username_name_score(
        resume_name,
        linkedin_username,
    )

    linkedin_match = (
        linkedin_score >= 75
    )

    # --------------------------------------------------------
    # Overall identity confidence
    # --------------------------------------------------------

    available_scores = []

    if github_username:
        available_scores.append(
            github_identity_score
        )

    if linkedin_username:
        available_scores.append(
            linkedin_score
        )

    if available_scores:

        identity_confidence = round(
            sum(
                available_scores
            )
            / len(
                available_scores
            ),
            2,
        )

    else:

        identity_confidence = 0.0

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    status = identity_status(
        identity_confidence,
        github_match,
        linkedin_match,
    )

    recommendation = (
        identity_recommendation(
            status
        )
    )

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {
        "resume_name": resume_name,

        "github_username": github_username,

        "github_display_name": (
            github_display_name
        ),

        "linkedin_username": (
            linkedin_username
        ),

        "github_username_score": (
            github_username_score
        ),

        "github_display_score": (
            round(
                github_display_score,
                2,
            )
        ),

        "github_identity_score": (
            github_identity_score
        ),

        "linkedin_identity_score": (
            linkedin_score
        ),

        "github_display_match": (
            github_display_match
        ),

        "github_username_match": (
            github_username_match
        ),

        "github_match": github_match,

        "linkedin_match": linkedin_match,

        "identity_confidence": (
            identity_confidence
        ),

        "identity_status": status,

        "recommendation": recommendation,
    }