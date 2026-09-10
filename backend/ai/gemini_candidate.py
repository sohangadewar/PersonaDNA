from backend.ai.gemini_engine import generate_with_gemini


def generate_candidate_insight(
    candidate_knowledge: str,
) -> str:
    """
    Generate a short recruiter-friendly candidate insight
    using only PersonaDNA evidence.
    """

    if (
        not candidate_knowledge
        or not candidate_knowledge.strip()
    ):
        raise ValueError(
            "Candidate knowledge cannot be empty."
        )

    prompt = f"""
You are PersonaDNA's candidate intelligence assistant.

Use ONLY the candidate knowledge provided below.

Your response MUST be very short.

STRICT RULES:

1. Never invent candidate information.
2. Never calculate or reinterpret the Trust Score.
3. Use the official PersonaDNA Trust Score exactly as provided.
4. Do not treat needs_review claims as false or suspicious.
5. Mention only claims explicitly identified by PersonaDNA.
6. Do not repeat the full resume.
7. Do not list every repository.
8. Do not explain the verification system.
9. Do not provide long reasoning.
10. Do not use markdown tables.
11. Maximum 5 bullet points.
12. Maximum 100 words total.

Return ONLY:

Trust Score: <official score>

Summary:
<one short sentence>

Verified:
<short sentence naming the important verified areas>

Needs Review:
<short sentence naming the most important claims needing verification>

Verdict:
<official recruiter verdict>

===== CANDIDATE KNOWLEDGE =====

{candidate_knowledge}

===== END CANDIDATE KNOWLEDGE =====
"""

    return generate_with_gemini(prompt)