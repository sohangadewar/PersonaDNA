from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PersonaDNA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
        "https://personadna-1.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





from io import BytesIO
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

from fastapi.responses import RedirectResponse

from ai.linkedin_oauth import (
    build_linkedin_authorization_url,
    validate_oauth_state,
    exchange_code_for_token,
    fetch_authorized_linkedin_data,
    create_oauth_result,
    consume_oauth_result,
)

from dotenv import load_dotenv

load_dotenv()
# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# COMMON SKILLS
# ==================================================

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
    Extract known skills from the resume text.
    """

    text = resume_text.lower()

    found_skills = []

    for skill in COMMON_SKILLS:
        if skill.lower() in text:
            found_skills.append(skill)

    return found_skills


# ==================================================
# ROOT
# ==================================================


@app.get("/")
def root():
    return {"message": "Welcome to PersonaDNA API 🚀"}


# ==================================================
# RESUME ANALYSIS
# ==================================================


@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    github: str = Form(""),
    linkedin: str = Form(""),
):

    linkedin_evidence = analyze_linkedin_evidence(
    linkedin_url=linkedin,
    profile_data=None,
    consent_granted=False,
)

    print("========== ANALYZE STARTED ==========")

    # --------------------------------------------------
    # 1. Validate PDF
    # --------------------------------------------------

    if resume.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF resume.",
        )

    # --------------------------------------------------
    # 2. Read uploaded file
    # --------------------------------------------------

    file_bytes = await resume.read()

    # --------------------------------------------------
    # 3. Extract PDF text
    # --------------------------------------------------

    try:
        reader = PdfReader(BytesIO(file_bytes))

        resume_text = ""

        for page in reader.pages:
            text = page.extract_text() or ""
            resume_text += text + "\n"

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read the uploaded PDF.",
        ) from exc

    # --------------------------------------------------
    # 4. Validate extracted text
    # --------------------------------------------------

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="The PDF does not contain readable text.",
        )

    # ==================================================
    # CANDIDATE EXTRACTION
    # ==================================================

    skills = extract_skills(resume_text)

    claims = extract_claims(resume_text)

    resume_name = extract_resume_name(resume_text)

    print("Claims:", len(claims))
    print("Skills:", len(skills))

    # ==================================================
    # GITHUB ANALYSIS
    # ==================================================

    github_evidence = analyze_github(github)
    print("\n========== GITHUB DEBUG ==========")

    for repo in github_evidence.get("repositories", []):
        print(
            repo.get("name"),
            "=>",
            repo.get("technologies"),
            "| language:",
            repo.get("language"),
        )

    print("GitHub repositories:", len(github_evidence.get("repositories", [])))

    # ==================================================
    # IDENTITY VERIFICATION
    # ==================================================

    identity = compare_identity(
        resume_name,
        github,
        linkedin,
        github_evidence.get(
            "display_name",
            "",
        ),
    )

    # ==================================================
    # CLAIM EVIDENCE
    # ==================================================

    claims = enrich_claims_with_github(
        claims,
        github_evidence,
    )
    
    claims = enrich_claims_with_linkedin(
    claims,
    linkedin_evidence,
)
    
    linkedin_summary = build_linkedin_summary(
        linkedin_evidence
)
    print("\n========== CLAIM DEBUG ==========")

    for claim in claims:
        if claim.get("claim") in {
            "Python",
            "JavaScript",
            "React",
            "SQL",
            "MongoDB",
            "GitHub",
        }:
            print(
                claim.get("claim"),
                "=>",
                claim.get("evidence"),
                "| status:",
                claim.get("status"),
            )

    claim_stats = calculate_claim_stats(
        claims
    )

    evidence_report = build_evidence_report(
        claims,
        github_evidence,
    )

    print("\n========== EVIDENCE DEBUG ==========")

    for item in evidence_report:
        if item.get("claim") in {
            "Python",
            "JavaScript",
            "React",
            "SQL",
            "MongoDB",
            "GitHub",
        }:
            print(item)

    risk_report = build_risk_report(
        claims,
        evidence_report,
        identity,
    )

    risk_summary = calculate_risk_summary(
        risk_report
    )

    skill_repository_mapping = build_skill_repository_mapping(
        claims,
        github_evidence,
    )

    # ==================================================
    # CANDIDATE INTELLIGENCE
    # ==================================================

    candidate_intelligence = build_candidate_intelligence(
        claims=claims,
        github_evidence=github_evidence,
        identity=identity,
        resume_text=resume_text,
    )

    project_repository_mapping = build_project_repository_mapping(
        claims,
        github_evidence,
    )

    print("========== CANDIDATE INTELLIGENCE DONE ==========")
    print(candidate_intelligence)

    # ==================================================
    # TRUST SCORE
    # ==================================================

    scoring = calculate_trust_score(
        identity,
        github_evidence,
    )

    verified_claims = claim_stats["supported"]

    # ==================================================
    # AI CONFIDENCE
    # ==================================================

    ai_confidence = (
        calculate_confidence(
            resume_text,
            claims,
            github_evidence,
            linkedin,
        )
    )

    # ==================================================
    # STRENGTHS
    # ==================================================

    strengths = []

    strengths.append(
        f"Resume successfully extracted with "
        f"{len(resume_text)} characters of readable text."
    )

    # GitHub evidence
    if github_evidence.get(
        "profile_found",
        False,
    ):
        strengths.append(
            f"GitHub profile found with "
            f"{github_evidence.get('repository_count', 0)} "
            f"public repositories."
        )
    else:
        strengths.append("GitHub profile could not be verified.")

    # GitHub identity
    if identity.get(
        "github_match",
        False,
    ):
        strengths.append("GitHub identity is consistent " "with the resume.")

    # LinkedIn identity
    if identity.get(
        "linkedin_match",
        False,
    ):
        strengths.append("LinkedIn identity is consistent " "with the resume.")

    # Technology evidence
    technology_evidence = github_evidence.get(
        "technology_evidence",
        [],
    )

    if technology_evidence:
        strengths.append(
            f"GitHub repositories provide evidence "
            f"for {len(technology_evidence)} technologies."
        )

    # ==================================================
    # WARNINGS
    # ==================================================

    warnings = []

    if not identity.get(
        "github_match",
        False,
    ):
        warnings.append(
            "GitHub identity does not match " "the name detected in the resume."
        )

    if not identity.get(
        "linkedin_match",
        False,
    ):
        warnings.append(
            "LinkedIn identity does not match " "the name detected in the resume."
        )

    if not github_evidence.get(
        "profile_found",
        False,
    ):
        warnings.append("GitHub profile could not be verified.")

    if (
        claim_stats.get(
            "needs_review",
            0,
        )
        > 0
    ):
        warnings.append(
            f"{claim_stats['needs_review']} "
            f"skill claims require additional evidence."
        )

    return {
        "skill_repository_mapping": skill_repository_mapping,
        "project_repository_mapping": project_repository_mapping,
        "trust_score": scoring["trust_score"],
        "ai_confidence": ai_confidence,
        "verified_claims": verified_claims,
        "risk_level": scoring["risk_level"],
        "recruiter_verdict": scoring["recruiter_verdict"],
        "claim_stats": claim_stats,
        "claims": claims,
        "identity": identity,
        "skills": skills,
        "github_evidence": github_evidence,
        "candidate_intelligence": candidate_intelligence,
        "strengths": strengths,
        "warnings": warnings,
        "resume_file_name": resume.filename,
        "resume_characters": len(resume_text),
        "resume_preview": resume_text[:2000],
        "github": github,
        "linkedin": linkedin,
        "evidence_report": evidence_report,
        "risk_report": risk_report,
        "risk_summary": risk_summary,
        "linkedin_evidence": linkedin_evidence,
        "linkedin_summary": linkedin_summary,
    }


# ============================================================
# LINKEDIN OAUTH
# ============================================================

@app.get("/linkedin/connect")
def linkedin_connect():

    try:
        authorization_url, _ = (
            build_linkedin_authorization_url()
        )

        return RedirectResponse(
            url=authorization_url
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@app.get("/linkedin/callback")
def linkedin_callback(
    code: str = "",
    state: str = "",
    error: str = "",
    error_description: str = "",
):
    """
    LinkedIn OAuth callback.
    """

    if error:

        raise HTTPException(
            status_code=400,
            detail=(
                f"LinkedIn authorization failed: "
                f"{error_description or error}"
            ),
        )

    if not code:

        raise HTTPException(
            status_code=400,
            detail="LinkedIn authorization code is missing.",
        )

    if not validate_oauth_state(
        state
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state.",
        )

    try:

        token_data = (
            exchange_code_for_token(
                code
            )
        )

        access_token = token_data.get(
            "access_token",
            "",
        )

        if not access_token:

            raise RuntimeError(
                "LinkedIn did not return an access token."
            )

        linkedin_data = (
            fetch_authorized_linkedin_data(
                access_token
            )
        )

        # DEVELOPMENT ONLY:
        # Do not expose the access token in the
        # production response.
        result_code = create_oauth_result(
            linkedin_data
        )

        frontend_url = (
            "https://personadna-1.onrender.com"
        )

        return RedirectResponse(
            url=(
                f"{frontend_url}"
                f"?linkedin_result={result_code}"
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
@app.get("/linkedin/result")
def linkedin_result(
    code: str = "",
):
    if not code:
        raise HTTPException(
            status_code=400,
            detail="LinkedIn result code is missing.",
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

    return {
    "https://personadna-1.onrender.com?linkedin_result=": code,
    "linkedin": linkedin_data,
}