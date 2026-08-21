def calculate_confidence(
    resume_text: str,
    claims: list[dict],
    github_evidence: dict,
    linkedin: str,
) -> list[int]:
    """
    Calculate a simple analysis-confidence score.

    This measures confidence in the analysis pipeline,
    not the candidate's honesty or trustworthiness.
    """

    confidence = 0

    # --------------------------------------------------
    # Resume text quality
    # --------------------------------------------------

    if resume_text and len(resume_text.strip()) > 500:
        confidence += 30

    elif resume_text and len(resume_text.strip()) > 100:
        confidence += 20

    # --------------------------------------------------
    # Claims extracted
    # --------------------------------------------------

    if claims:

        confidence += 20

    # --------------------------------------------------
    # GitHub profile evidence
    # --------------------------------------------------

    if github_evidence.get(
        "profile_found",
        False,
    ):

        confidence += 30

    # --------------------------------------------------
    # GitHub repositories
    # --------------------------------------------------

    if github_evidence.get(
        "repositories",
        [],
    ):

        confidence += 10

    # --------------------------------------------------
    # LinkedIn URL supplied
    # --------------------------------------------------

    if linkedin and linkedin.strip():

        confidence += 10

    # --------------------------------------------------
    # Clamp
    # --------------------------------------------------

    confidence = min(
        confidence,
        100,
    )

    return [confidence]