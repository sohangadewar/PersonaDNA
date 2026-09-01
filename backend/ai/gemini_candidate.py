from backend.ai.gemini_engine import generate_with_gemini


def generate_candidate_insight(
    candidate_knowledge: str,
) -> str:
    """
    Generate a human-readable candidate insight using
    only evidence already collected by PersonaDNA.
    """

    if (
        not candidate_knowledge
        or not candidate_knowledge.strip()
    ):
        raise ValueError(
            "Candidate knowledge cannot be empty."
        )

    prompt = f"""
You are PersonaDNA's AI candidate analysis assistant.

Analyze the candidate information provided below.

IMPORTANT RULES:

1. Use ONLY the information provided in candidate knowledge.
2. Do not invent facts, skills, projects, experience, or evidence.
3. Do not change or calculate the candidate's Trust Score.
4. Do not create evidence that is not present.
5. Clearly mention when information is missing or uncertain.
6. Keep the response concise and easy for a recruiter to understand.
7. Focus on evidence-supported strengths and areas that may need review.

TRUST SCORE RULES:

8. "overall_evidence_score" is NOT the PersonaDNA Trust Score.
9. Never call "overall_evidence_score" the Trust Score.
10. The Trust Score must ONLY come from the official PersonaDNA scoring system.
11. If an official Trust Score is provided in candidate knowledge, use that exact value.
12. If the official Trust Score is NOT provided in candidate knowledge, do not mention a Trust Score.
13. Never calculate, estimate, infer, reinterpret, or replace the official Trust Score.
14. Never derive the Trust Score from verified claims, evidence score, AI confidence, risk level, or any other field.
15. If both "trust_score" and "overall_evidence_score" are present, treat them as completely different values.
16. "trust_score" is the official PersonaDNA Trust Score.
17. "overall_evidence_score" is only an evidence-strength metric and must never be presented as the Trust Score.

===== CANDIDATE KNOWLEDGE =====

{candidate_knowledge}

===== END CANDIDATE KNOWLEDGE =====

Provide a short candidate insight covering:

- Official PersonaDNA Trust Score, ONLY if explicitly provided
- Strongly supported skills or areas
- Important projects or technical evidence
- Claims that may need further verification
- Overall profile observation

Do not use markdown tables.
Do not invent missing information.
Do not calculate any score.
"""

    return generate_with_gemini(
        prompt
    )