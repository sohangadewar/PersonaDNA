def process_jarvis_command(
    command: str,
    analysis_result: dict,
):

    command = command.lower().strip()

    if "trust score" in command:
        return (
            f"The candidate trust score is "
            f"{analysis_result.get('trust_score', 0)}."
        )

    if "confidence" in command:
        return (
            f"The AI confidence is "
            f"{analysis_result.get('ai_confidence', 0)} percent."
        )

    if "verified claims" in command:
        return (
            f"There are "
            f"{analysis_result.get('verified_claims', 0)} "
            f"verified claims."
        )

    if "risk" in command:
        return (
            f"The current risk level is "
            f"{analysis_result.get('risk_level', 'unknown')}."
        )

    if "verdict" in command:
        return (
            f"The recruiter verdict is "
            f"{analysis_result.get('recruiter_verdict', 'unknown')}."
        )

    if "skills" in command:

        skills = analysis_result.get(
            "skills",
            [],
        )

        return (
            "The candidate skills are "
            + ", ".join(skills)
        )

    return (
        "I can provide the trust score, "
        "AI confidence, verified claims, "
        "risk level, recruiter verdict, "
        "or candidate skills."
    )