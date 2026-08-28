from backend.ai.gemini_engine import generate_with_gemini


def generate_candidate_insight(candidate_knowledge: str) -> str:
    """
    Generate a human-readable candidate insight using
    only the evidence already collected by PersonaDNA.
    """

    if not candidate_knowledge or not candidate_knowledge.strip():
        raise ValueError(
            "Candidate knowledge cannot be empty."
        )

    prompt = f"""
You are PersonaDNA's AI candidate analysis assistant.

Analyze the candidate information provided below.

IMPORTANT RULES:
1. Use ONLY the information provided.
2. Do not invent facts, skills, projects, experience, or evidence.
3. Do not change or calculate the candidate's Trust Score.
4. Do not create evidence that is not present.
5. Clearly mention when information is missing or uncertain.
6. Keep the response concise and easy for a recruiter to understand.
7. Focus on evidence-supported strengths and areas that may need review.

===== CANDIDATE KNOWLEDGE =====

{candidate_knowledge}

===== END CANDIDATE KNOWLEDGE =====

Provide a short candidate insight covering:
- Strongly supported skills or areas
- Important projects or technical evidence
- Claims that may need further verification
- Overall profile observation

Do not use markdown tables.
"""

    return generate_with_gemini(prompt)