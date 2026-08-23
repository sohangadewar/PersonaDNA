from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from io import BytesIO
import json

from pypdf import PdfReader

from ai.claims import extract_claims
from ai.identity import extract_resume_name, compare_identity
from ai.scoring import calculate_trust_score
from ai.github import analyze_github
from ai.confidence import calculate_confidence

from ai.evidence import (
    build_evidence_report,
    enrich_claims_with_github,
    calculate_claim_stats,
)

from ai.linkedin import (
    analyze_linkedin_evidence,
    enrich_claims_with_linkedin,
    build_linkedin_summary,
)

from ai.risk_engine import (
    build_risk_report,
    calculate_risk_summary,
)

from ai.skill_mapping import build_skill_repository_mapping

from ai.candidate_intelligence import (
    build_candidate_intelligence,
)

from ai.project_matching import (
    build_project_repository_mapping,
)

from ai.linkedin_oauth import (
    build_linkedin_authorization_url,
    validate_oauth_state,
    exchange_code_for_token,
    fetch_authorized_linkedin_data,
    create_oauth_result,
    consume_oauth_result,
)


# ============================================================
# APP
# ============================================================

app = FastAPI(title="PersonaDNA API")


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://personadna-1.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# COMMON SKILLS
# ============================================================

COMMON_SKILLS = [
    # Programming
    "Python",
    "Java",
    "C++",
    "C",
    "JavaScript",
    "TypeScript",
    "Groovy",

    # Frontend
    "React",
    "ReactJS",
    "Redux",
    "HTML",
    "CSS",
    "Tailwind CSS",

    # Backend
    "Node.js",
    "NodeJS",
    "Express.js",
    "ExpressJS",
    "FastAPI",
    "Flask",
    "Django",
    "REST API",
    "REST",

    # Databases
    "SQL",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "Redis",

    # AI / Data
    "Artificial Intelligence",
    "AI",
    "Machine Learning",
    "Deep Learning",
    "Data Science",
    "Data Analysis",

    # Computer Science
    "Data Structures",
    "Algorithms",
    "Object Oriented Programming",
    "Operating Systems",
    "DBMS",
    "Computer Networks",
    "Competitive Programming",

    # Tools / Cloud
    "Git",
    "GitHub",
    "Docker",
    "AWS",
    "Google Cloud",
]


def extract_skills(resume_text: str) -> list[str]:
    """
    Extract known skills from resume text.
    """

    text = resume_text.lower()

    found_skills = []

    for skill in COMMON_SKILLS:
        if skill.lower() in text:
            found_skills.append(skill)

    return found_skills


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Welcome to PersonaDNA API 🚀"
    }


# ============================================================
# RESUME ANALYSIS
# ============================================================

@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    github: str = Form(""),
    linkedin: str = Form(""),
    linkedin_profile: str = Form(""),
):

    print("\n")
    print("==============================================")
    print("        PERSONADNA ANALYSIS STARTED")
    print("==============================================")

    # ========================================================
    # 1. LINKEDIN AUTHORIZED DATA
    # ========================================================

    linkedin_profile_data = None

    if linkedin_profile:

        try:

            parsed_linkedin = json.loads(
                linkedin_profile
            )

            if isinstance(
                parsed_linkedin,
                dict,
            ):

                if isinstance(
                    parsed_linkedin.get("linkedin"),
                    dict,
                ):

                    linkedin_profile_data = (
                        parsed_linkedin["linkedin"]
                    )

                else:

                    linkedin_profile_data = (
                        parsed_linkedin
                    )

        except (
            json.JSONDecodeError,
            TypeError,
        ):

            linkedin_profile_data = None

    # ========================================================
    # 2. LINKEDIN EVIDENCE
    # ========================================================

    linkedin_evidence = analyze_linkedin_evidence(
        linkedin_url=linkedin,
        profile_data=linkedin_profile_data,
        consent_granted=bool(
            linkedin_profile_data
        ),
    )

    print("\n========== LINKEDIN DEBUG ==========")

    print(
        "LinkedIn URL:",
        linkedin,
    )

    print(
        "LinkedIn authorized:",
        bool(linkedin_profile_data),
    )

    print(
        "LinkedIn display name:",
        linkedin_evidence.get(
            "display_name",
            "",
        ),
    )

    print(
        "LinkedIn authorized source:",
        linkedin_evidence.get(
            "authorized_source",
            False,
        ),
    )

    # ========================================================
    # 3. VALIDATE PDF
    # ========================================================

    if resume.content_type != "application/pdf":

        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF resume.",
        )

    # ========================================================
    # 4. READ PDF
    # ========================================================

    file_bytes = await resume.read()

    try:

        reader = PdfReader(
            BytesIO(file_bytes)
        )

        resume_text = ""

        for page in reader.pages:

            resume_text += (
                page.extract_text() or ""
            )

            resume_text += "\n"

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail="Could not read the uploaded PDF.",
        ) from exc

    # ========================================================
    # 5. VALIDATE TEXT
    # ========================================================

    if not resume_text.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "The PDF does not contain readable text."
            ),
        )

    # ========================================================
    # 6. RESUME EXTRACTION
    # ========================================================

    resume_name = extract_resume_name(
        resume_text
    )

    claims = extract_claims(
        resume_text
    )

    skills = extract_skills(
        resume_text
    )

    print("\n========== RESUME DEBUG ==========")

    print(
        "Resume name:",
        repr(resume_name),
    )

    print(
        "Claims:",
        len(claims),
    )

    print(
        "Skills:",
        len(skills),
    )

    # ========================================================
    # 7. GITHUB ANALYSIS
    # ========================================================

    github_evidence = analyze_github(
        github
    )

    print("\n========== GITHUB DEBUG ==========")

    print(
        "GitHub username:",
        github,
    )

    print(
        "GitHub profile found:",
        github_evidence.get(
            "profile_found",
            False,
        ),
    )

    print(
        "GitHub display name:",
        github_evidence.get(
            "display_name",
            "",
        ),
    )

    print(
        "GitHub repository count:",
        github_evidence.get(
            "repository_count",
            0,
        ),
    )

    # ========================================================
    # 8. LINKEDIN IDENTITY NAME
    # ========================================================

    linkedin_identity_name = ""

    if isinstance(
        linkedin_profile_data,
        dict,
    ):

        linkedin_identity_name = str(
            linkedin_profile_data.get(
                "name",
                "",
            )
        ).strip()

        if not linkedin_identity_name:

            first_name = str(
                linkedin_profile_data.get(
                    "first_name",
                    "",
                )
            ).strip()

            last_name = str(
                linkedin_profile_data.get(
                    "last_name",
                    "",
                )
            ).strip()

            linkedin_identity_name = " ".join(
                part
                for part in (
                    first_name,
                    last_name,
                )
                if part
            ).strip()

    # Fallback
    if not linkedin_identity_name:

        linkedin_identity_name = str(
            linkedin_evidence.get(
                "display_name",
                "",
            )
        ).strip()

    print(
        "LinkedIn identity name:",
        repr(linkedin_identity_name),
    )

    # ========================================================
    # 9. IDENTITY COMPARISON
    # ========================================================

    identity = compare_identity(
        resume_name=resume_name,
        github=github,
        linkedin=linkedin_identity_name,
        github_display_name=github_evidence.get(
            "display_name",
            "",
        ),
    )

    print("\n========== IDENTITY DEBUG ==========")

    print(
        "Resume:",
        identity.get(
            "resume_normalized",
            "",
        ),
    )

    print(
        "GitHub:",
        identity.get(
            "github_normalized",
            "",
        ),
    )

    print(
        "LinkedIn:",
        identity.get(
            "linkedin_normalized",
            "",
        ),
    )

    print(
        "GitHub match:",
        identity.get(
            "github_match",
            False,
        ),
    )

    print(
        "LinkedIn match:",
        identity.get(
            "linkedin_match",
            False,
        ),
    )

    # ========================================================
    # 10. ENRICH CLAIMS
    # ========================================================

    claims = enrich_claims_with_github(
        claims,
        github_evidence,
    )

    claims = enrich_claims_with_linkedin(
        claims,
        linkedin_evidence,
    )

    # ========================================================
    # 11. LINKEDIN SUMMARY
    # ========================================================

    linkedin_summary = build_linkedin_summary(
        linkedin_evidence
    )

    # ========================================================
    # 12. CLAIM STATS
    # ========================================================

    claim_stats = calculate_claim_stats(
        claims
    )

    print("\n========== CLAIM STATS ==========")

    print(
        "Detected:",
        claim_stats.get(
            "detected",
            0,
        ),
    )

    print(
        "Supported:",
        claim_stats.get(
            "supported",
            0,
        ),
    )

    print(
        "Needs review:",
        claim_stats.get(
            "needs_review",
            0,
        ),
    )

    # ========================================================
    # 13. EVIDENCE REPORT
    # ========================================================

    evidence_report = build_evidence_report(
        claims,
        github_evidence,
    )

    # ========================================================
    # 14. RISK REPORT
    # ========================================================

    risk_report = build_risk_report(
        claims,
        evidence_report,
        identity,
    )

    risk_summary = calculate_risk_summary(
        risk_report
    )

    # ========================================================
    # 15. SKILL → REPOSITORY MAPPING
    # ========================================================

    skill_repository_mapping = (
        build_skill_repository_mapping(
            claims,
            github_evidence,
        )
    )

    # ========================================================
    # 16. CANDIDATE INTELLIGENCE
    # ========================================================

    candidate_intelligence = (
        build_candidate_intelligence(
            claims=claims,
            github_evidence=github_evidence,
            identity=identity,
            resume_text=resume_text,
        )
    )

    # ========================================================
    # 17. PROJECT → REPOSITORY MAPPING
    # ========================================================

    project_repository_mapping = (
        build_project_repository_mapping(
            claims,
            github_evidence,
        )
    )

    # ========================================================
    # 18. TRUST SCORE
    # ========================================================

    scoring = calculate_trust_score(
        identity,
        github_evidence,
    )

    print("\n========== TRUST SCORE ==========")

    print(
        "Trust score:",
        scoring.get(
            "trust_score",
            0,
        ),
    )

    print(
        "Risk:",
        scoring.get(
            "risk_level",
            "Medium",
        ),
    )

    print(
        "Verdict:",
        scoring.get(
            "recruiter_verdict",
            "",
        ),
    )

    print(
        "Breakdown:",
        scoring.get(
            "score_breakdown",
            {},
        ),
    )

    # ========================================================
    # 19. VERIFIED CLAIMS
    # ========================================================

    verified_claims = claim_stats.get(
        "supported",
        0,
    )

    # ========================================================
    # 20. AI CONFIDENCE
    # ========================================================

    ai_confidence = calculate_confidence(
        resume_text,
        claims,
        github_evidence,
        linkedin,
    )

    if isinstance(
        ai_confidence,
        list,
    ):

        ai_confidence = (
            ai_confidence[0]
            if ai_confidence
            else 0
        )

    if isinstance(
        ai_confidence,
        dict,
    ):

        ai_confidence = ai_confidence.get(
            "score",
            0,
        )

    try:

        ai_confidence = int(
            float(
                ai_confidence
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        ai_confidence = 0

    ai_confidence = min(
        100,
        max(
            0,
            ai_confidence,
        ),
    )

    # ========================================================
    # 21. STRENGTHS
    # ========================================================

    strengths = []

    strengths.append(
        f"Resume successfully extracted with "
        f"{len(resume_text)} characters of readable text."
    )

    if github_evidence.get(
        "profile_found",
        False,
    ):

        strengths.append(
            f"GitHub profile found with "
            f"{github_evidence.get('repository_count', 0)} "
            f"public repositories."
        )

    if identity.get(
        "github_match",
        False,
    ):

        strengths.append(
            "GitHub identity is consistent "
            "with the resume."
        )

    if identity.get(
        "linkedin_match",
        False,
    ):

        strengths.append(
            "LinkedIn identity is consistent "
            "with the resume."
        )

    if linkedin_evidence.get(
        "authorized_source",
        False,
    ):

        strengths.append(
            "LinkedIn profile was connected "
            "through an authorized integration."
        )

    technology_evidence = (
        github_evidence.get(
            "technology_evidence",
            [],
        )
    )

    if technology_evidence:

        strengths.append(
            f"GitHub repositories provide evidence "
            f"for {len(technology_evidence)} technologies."
        )

    # ========================================================
    # 22. WARNINGS
    # ========================================================

    warnings = []

    if not identity.get(
        "github_match",
        False,
    ):

        warnings.append(
            "GitHub identity does not match "
            "the name detected in the resume."
        )

    if (
        linkedin_evidence.get(
            "authorized_source",
            False,
        )
        and not identity.get(
            "linkedin_match",
            False,
        )
    ):

        warnings.append(
            "LinkedIn identity does not match "
            "the name detected in the resume."
        )

    if (
        linkedin
        and not linkedin_evidence.get(
            "authorized_source",
            False,
        )
    ):

        warnings.append(
            "LinkedIn profile was supplied, "
            "but authorized LinkedIn evidence "
            "is not available."
        )

    if not github_evidence.get(
        "profile_found",
        False,
    ):

        warnings.append(
            "GitHub profile could not be verified."
        )

    if claim_stats.get(
        "needs_review",
        0,
    ) > 0:

        warnings.append(
            f"{claim_stats['needs_review']} "
            f"skill claims require additional evidence."
        )

    # ========================================================
    # 23. LINKEDIN VERIFIED
    # ========================================================

    linkedin_verified = (
        linkedin_evidence.get(
            "authorized_source",
            False,
        )
        and identity.get(
            "linkedin_match",
            False,
        )
    )

    # ========================================================
    # 24. FINAL DEBUG
    # ========================================================

    print("\n========== FINAL PERSONADNA RESULT ==========")

    print(
        "Resume name:",
        repr(resume_name),
    )

    print(
        "GitHub:",
        repr(
            github_evidence.get(
                "display_name",
                "",
            )
        ),
    )

    print(
        "LinkedIn:",
        repr(linkedin_identity_name),
    )

    print(
        "GitHub match:",
        identity.get(
            "github_match",
            False,
        ),
    )

    print(
        "LinkedIn match:",
        identity.get(
            "linkedin_match",
            False,
        ),
    )

    print(
        "Trust score:",
        scoring.get(
            "trust_score",
            0,
        ),
    )

    print(
        "AI confidence:",
        ai_confidence,
    )

    print(
        "Verified claims:",
        verified_claims,
    )

    print(
        "============================================")

    # ========================================================
    # 25. FINAL RESPONSE
    # ========================================================

    return {

        # Core scoring
        "trust_score": scoring.get(
            "trust_score",
            0,
        ),

        "ai_confidence": ai_confidence,

        "verified_claims": verified_claims,

        "risk_level": scoring.get(
            "risk_level",
            "Medium",
        ),

        "recruiter_verdict": scoring.get(
            "recruiter_verdict",
            "Manual Verification Recommended",
        ),

        "score_breakdown": scoring.get(
            "score_breakdown",
            {},
        ),

        # Claims
        "claim_stats": claim_stats,

        "claims": claims,

        "skills": skills,

        # Identity
        "identity": identity,

        # GitHub
        "github_evidence": github_evidence,

        "github": github,

        # LinkedIn
        "linkedin": linkedin,

        "linkedin_evidence": linkedin_evidence,

        "linkedin_summary": linkedin_summary,

        "linkedin_verified": linkedin_verified,

        # Reports
        "evidence_report": evidence_report,

        "risk_report": risk_report,

        "risk_summary": risk_summary,

        # Intelligence
        "candidate_intelligence": candidate_intelligence,

        "skill_repository_mapping": (
            skill_repository_mapping
        ),

        "project_repository_mapping": (
            project_repository_mapping
        ),

        # Strengths / warnings
        "strengths": strengths,

        "warnings": warnings,

        # Resume
        "resume_file_name": resume.filename,

        "resume_characters": len(
            resume_text
        ),

        "resume_preview": resume_text[:2000],
    }

# ============================================================
# LINKEDIN OAUTH — CONNECT
# ============================================================

@app.get("/linkedin/connect")
def linkedin_connect():

    try:

        authorization_url, _ = (
            build_linkedin_authorization_url()
        )

        print(
            "\nLinkedIn authorization URL generated."
        )

        return RedirectResponse(
            url=authorization_url
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# LINKEDIN OAUTH — CALLBACK
# ============================================================

@app.get("/linkedin/callback")
def linkedin_callback(
    code: str = "",
    state: str = "",
    error: str = "",
    error_description: str = "",
):

    print(
        "\n========== LINKEDIN CALLBACK =========="
    )

    # --------------------------------------------------------
    # LinkedIn returned an error
    # --------------------------------------------------------

    if error:

        raise HTTPException(
            status_code=400,
            detail=(
                f"LinkedIn authorization failed: "
                f"{error_description or error}"
            ),
        )

    # --------------------------------------------------------
    # Missing authorization code
    # --------------------------------------------------------

    if not code:

        raise HTTPException(
            status_code=400,
            detail=(
                "LinkedIn authorization "
                "code is missing."
            ),
        )

    # --------------------------------------------------------
    # Validate OAuth state
    # --------------------------------------------------------

    if not validate_oauth_state(state):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid or expired OAuth state."
            ),
        )

    try:

        # ----------------------------------------------------
        # Exchange authorization code
        # ----------------------------------------------------

        token_data = exchange_code_for_token(
            code
        )

        access_token = token_data.get(
            "access_token",
            "",
        )

        if not access_token:

            raise RuntimeError(
                "LinkedIn did not return "
                "an access token."
            )

        # ----------------------------------------------------
        # Fetch authorized LinkedIn data
        # ----------------------------------------------------

        linkedin_data = (
            fetch_authorized_linkedin_data(
                access_token
            )
        )

        print(
            "LinkedIn authorized data received."
        )

        print(
            "LinkedIn data:",
            linkedin_data,
        )

        # ----------------------------------------------------
        # Create temporary result code
        # ----------------------------------------------------

        result_code = create_oauth_result(
            linkedin_data
        )

        # ----------------------------------------------------
        # Redirect to frontend
        # ----------------------------------------------------

        frontend_url = (
            "https://personadna-1.onrender.com"
        )

        redirect_url = (
            f"{frontend_url}"
            f"?linkedin_result={result_code}"
        )

        print(
            "Redirecting to frontend."
        )

        return RedirectResponse(
            url=redirect_url
        )

    except Exception as exc:

        print(
            "LinkedIn OAuth error:",
            str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# LINKEDIN OAUTH — RESULT
# ============================================================

@app.get("/linkedin/result")
def linkedin_result(
    code: str = "",
):

    if not code:

        raise HTTPException(
            status_code=400,
            detail=(
                "LinkedIn result "
                "code is missing."
            ),
        )

    linkedin_data = consume_oauth_result(
        code
    )

    if not linkedin_data:

        raise HTTPException(
            status_code=400,
            detail=(
                "LinkedIn result is invalid "
                "or has already been used."
            ),
        )

    print(
        "\n========== LINKEDIN RESULT =========="
    )

    print(
        "LinkedIn result successfully consumed."
    )

    return {
        "code": code,
        "linkedin": linkedin_data,
    }