# ============================================================
# PersonaDNA - Synthetic Trust Score Test Suite
# ============================================================

from backend.ai.scoring import calculate_trust_score


def make_claim(
    claim,
    claim_type="skill",
    resume=True,
    github=False,
    linkedin=False,
    rag_status="verified",
    rag_confidence=90,
):
    return {
        "claim": claim,
        "type": claim_type,
        "evidence": {
            "resume": resume,
            "github": github,
            "linkedin": linkedin,
        },
        "rag_status": rag_status,
        "rag_confidence": rag_confidence,
    }


def run_test(
    candidate_name,
    identity,
    github_evidence,
    linkedin_evidence,
    claims,
):
    result = calculate_trust_score(
        identity=identity,
        github_evidence=github_evidence,
        claims=claims,
        evidence_report=[],
        linkedin_evidence=linkedin_evidence,
    )

    print("\n")
    print("=" * 65)
    print(f" CANDIDATE: {candidate_name}")
    print("=" * 65)

    print(
        f"Trust Score : {result['trust_score']}/100"
    )

    print(
        f"Risk Level  : {result['risk_level']}"
    )

    print("\nScore Breakdown:")

    for key, value in result[
        "score_breakdown"
    ].items():

        print(
            f"  {key:<25} : {value}"
        )

    print("\nRecruiter Verdict:")
    print(
        f"  {result['recruiter_verdict']}"
    )

    print("=" * 65)

    return result


# ============================================================
# COMMON GITHUB DATA
# ============================================================

STRONG_GITHUB = {
    "profile_found": True,
    "display_name": "Aarav Sharma",
    "repository_count": 8,
    "repositories": [
        "AI Resume Analyzer",
        "FastAPI Backend",
        "ML Prediction System",
        "Portfolio",
        "Data Pipeline",
        "Chatbot",
        "Attendance System",
        "RAG Assistant",
    ],
    "technology_evidence": [
        "Python",
        "FastAPI",
        "Machine Learning",
        "SQL",
        "Git",
    ],
}


WEAK_GITHUB = {
    "profile_found": True,
    "display_name": "Aarav Sharma",
    "repository_count": 1,
    "repositories": [
        "hello-world",
    ],
    "technology_evidence": [],
}


NO_GITHUB = {
    "profile_found": False,
    "display_name": "",
    "repository_count": 0,
    "repositories": [],
    "technology_evidence": [],
}


# ============================================================
# 1. STRONG CANDIDATE
# ============================================================

run_test(

    candidate_name="Strong Verified Candidate",

    identity={
        "github_match": True,
        "linkedin_match": True,
    },

    github_evidence=STRONG_GITHUB,

    linkedin_evidence={
        "authorized_source": True,
        "display_name": "Aarav Sharma",
    },

    claims=[
        make_claim(
            "Python",
            resume=True,
            github=True,
            linkedin=True,
            rag_status="verified",
            rag_confidence=95,
        ),

        make_claim(
            "FastAPI",
            resume=True,
            github=True,
            linkedin=True,
            rag_status="verified",
            rag_confidence=92,
        ),

        make_claim(
            "Machine Learning",
            resume=True,
            github=True,
            linkedin=True,
            rag_status="verified",
            rag_confidence=90,
        ),

        make_claim(
            "Data Science",
            resume=True,
            github=True,
            linkedin=True,
            rag_status="verified",
            rag_confidence=88,
        ),
    ],
)


# ============================================================
# 2. GOOD CANDIDATE - NO LINKEDIN AUTHORIZATION
# ============================================================

run_test(

    candidate_name="Good Candidate - LinkedIn Unavailable",

    identity={
        "github_match": True,
        "linkedin_match": False,
    },

    github_evidence=STRONG_GITHUB,

    linkedin_evidence={
        "authorized_source": False,
    },

    claims=[
        make_claim(
            "Python",
            resume=True,
            github=True,
            linkedin=False,
            rag_status="verified",
            rag_confidence=90,
        ),

        make_claim(
            "FastAPI",
            resume=True,
            github=True,
            linkedin=False,
            rag_status="verified",
            rag_confidence=85,
        ),

        make_claim(
            "Machine Learning",
            resume=True,
            github=True,
            linkedin=False,
            rag_status="verified",
            rag_confidence=80,
        ),
    ],
)


# ============================================================
# 3. MODERATE CANDIDATE
# ============================================================

run_test(

    candidate_name="Moderate Candidate",

    identity={
        "github_match": False,
        "linkedin_match": False,
    },

    github_evidence=WEAK_GITHUB,

    linkedin_evidence={
        "authorized_source": False,
    },

    claims=[
        make_claim(
            "Python",
            resume=True,
            github=True,
            linkedin=False,
            rag_status="verified",
            rag_confidence=70,
        ),

        make_claim(
            "React",
            resume=True,
            github=False,
            linkedin=False,
            rag_status="partially_supported",
            rag_confidence=60,
        ),

        make_claim(
            "Machine Learning",
            resume=True,
            github=False,
            linkedin=False,
            rag_status="needs_review",
            rag_confidence=30,
        ),
    ],
)


# ============================================================
# 4. WEAK CANDIDATE
# ============================================================

run_test(

    candidate_name="Weak Candidate",

    identity={
        "github_match": False,
        "linkedin_match": False,
    },

    github_evidence=NO_GITHUB,

    linkedin_evidence={
        "authorized_source": False,
    },

    claims=[
        make_claim(
            "Python",
            resume=True,
            github=False,
            linkedin=False,
            rag_status="needs_review",
            rag_confidence=30,
        ),

        make_claim(
            "Artificial Intelligence",
            resume=True,
            github=False,
            linkedin=False,
            rag_status="unsupported",
            rag_confidence=10,
        ),

        make_claim(
            "Deep Learning",
            resume=True,
            github=False,
            linkedin=False,
            rag_status="unsupported",
            rag_confidence=5,
        ),
    ],
)


# ============================================================
# 5. HIGH-RISK IDENTITY MISMATCH
# ============================================================

run_test(

    candidate_name="Identity Mismatch Candidate",

    identity={
        "github_match": False,
        "linkedin_match": False,
    },

    github_evidence={
        "profile_found": True,
        "display_name": "Completely Different Person",
        "repository_count": 12,

        "repositories": [
            "AI Project",
            "ML Project",
            "Web App",
            "FastAPI API",
            "Data Science",
            "RAG System",
            "Chatbot",
            "Portfolio",
            "Automation",
            "Dashboard",
            "API Gateway",
            "Prediction Model",
        ],

        "technology_evidence": [
            "Python",
            "FastAPI",
            "Machine Learning",
            "React",
            "SQL",
        ],
    },

    linkedin_evidence={
        "authorized_source": True,
        "display_name": "Another Person",
    },

    claims=[
        make_claim(
            "Python",
            resume=True,
            github=False,
            linkedin=False,
            rag_status="needs_review",
            rag_confidence=30,
        ),

        make_claim(
            "FastAPI",
            resume=True,
            github=False,
            linkedin=False,
            rag_status="unsupported",
            rag_confidence=20,
        ),

        make_claim(
            "Machine Learning",
            resume=True,
            github=False,
            linkedin=False,
            rag_status="unsupported",
            rag_confidence=10,
        ),

        make_claim(
            "Deep Learning",
            resume=True,
            github=False,
            linkedin=False,
            rag_status="unsupported",
            rag_confidence=5,
        ),
    ],
)


print("\n")
print("=" * 65)
print(" PERSONADNA SYNTHETIC SCORING TEST COMPLETED")
print("=" * 65)