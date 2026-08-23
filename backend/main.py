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
    Extract known skills from the resume text.
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

            linkedin_profile_data = json.loads(
                linkedin_profile
            )

            # ------------------------------------------------
            # Frontend may send:
            #
            # {
            #     "code": "...",
            #     "linkedin": {
            #         "name": "Gadewar Sohan"
            #     }
            # }
            #
            # We only need the actual LinkedIn data.
            # ------------------------------------------------

            if isinstance(
                linkedin_profile_data,
                dict,
            ):

                if isinstance(
                    linkedin_profile_data.get(
                        "linkedin"
                    ),
                    dict,
                ):

                    linkedin_profile_data = (
                        linkedin_profile_data[
                            "linkedin"
                        ]
                    )

        except json.JSONDecodeError:

            linkedin_profile_data = None

    # ========================================================
    # LINKEDIN DEBUG
    # ========================================================

    print("\n========== LINKEDIN DEBUG ==========")

    print(
        "LinkedIn URL:",
        linkedin,
    )

    print(
        "LinkedIn profile data:",
        linkedin_profile_data,
    )

    print(
        "LinkedIn authorized data:",
        bool(linkedin_profile_data),
    )

    # ========================================================
    # LINKEDIN EVIDENCE
    # ========================================================

    linkedin_evidence = analyze_linkedin_evidence(
        linkedin_url=linkedin,
        profile_data=linkedin_profile_data,
        consent_granted=bool(
            linkedin_profile_data
        ),
    )

    print(
        "LinkedIn evidence status:",
        linkedin_evidence.get(
            "evidence_status"
        ),
    )

    print(
        "LinkedIn display name:",
        linkedin_evidence.get(
            "display_name"
        ),
    )

    print(
        "LinkedIn authorized source:",
        linkedin_evidence.get(
            "authorized_source"
        ),
    )

    # ========================================================
    # 2. VALIDATE PDF
    # ========================================================

    if resume.content_type != "application/pdf":

        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF resume.",
        )

    # ========================================================
    # 3. READ UPLOADED FILE
    # ========================================================

    file_bytes = await resume.read()

    # ========================================================
    # 4. EXTRACT PDF TEXT
    # ========================================================

    try:

        reader = PdfReader(
            BytesIO(file_bytes)
        )

        resume_text = ""

        for page in reader.pages:

            text = page.extract_text() or ""

            resume_text += (
                text + "\n"
            )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail="Could not read the uploaded PDF.",
        ) from exc

    # ========================================================
    # 5. VALIDATE EXTRACTED TEXT
    # ========================================================

    if not resume_text.strip():

        raise HTTPException(
            status_code=400,
            detail="The PDF does not contain readable text.",
        )

    # ========================================================
    # CANDIDATE EXTRACTION
    # ========================================================

    skills = extract_skills(
        resume_text
    )

    claims = extract_claims(
        resume_text
    )

    resume_name = extract_resume_name(
        resume_text
    )

    print("\n========== CANDIDATE DEBUG ==========")

    print(
        "Resume name:",
        resume_name,
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
    # GITHUB ANALYSIS
    # ========================================================

    github_evidence = analyze_github(
        github
    )

    print("\n========== GITHUB DEBUG ==========")

    for repo in github_evidence.get(
        "repositories",
        [],
    ):

        print(
            repo.get("name"),
            "=>",
            repo.get("technologies"),
            "| language:",
            repo.get("language"),
        )

    print(
        "GitHub repositories:",
        len(
            github_evidence.get(
                "repositories",
                [],
            )
        ),
    )

    print(
        "GitHub display name:",
        github_evidence.get(
            "display_name",
            "",
        ),
    )

    # ========================================================
    # IDENTITY VERIFICATION
    # ========================================================

    linkedin_identity_name = ""

    # --------------------------------------------------------
    # Get LinkedIn name from authorized profile data
    # --------------------------------------------------------

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

        # ----------------------------------------------------
        # Fallback to first_name + last_name
        # ----------------------------------------------------

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
                for part in [
                    first_name,
                    last_name,
                ]
                if part
            ).strip()

    # --------------------------------------------------------
    # Final fallback to normalized LinkedIn evidence
    # --------------------------------------------------------

    if not linkedin_identity_name:

        linkedin_identity_name = str(
            linkedin_evidence.get(
                "display_name",
                "",
            )
        ).strip()

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Never use the LinkedIn URL as the person's name.
    # --------------------------------------------------------

    identity = compare_identity(
        resume_name=resume_name,
        github=github,
        linkedin=linkedin_identity_name,
        github_display_name=github_evidence.get(
            "display_name",
            "",
        ),
    )

    # ========================================================
    # IDENTITY DEBUG
    # ========================================================

    print("\n========== IDENTITY DEBUG ==========")

    print(
        "Resume name:",
        resume_name,
    )

    print(
        "GitHub name:",
        github_evidence.get(
            "display_name",
            "",
        ),
    )

    print(
        "LinkedIn name:",
        linkedin_identity_name,
    )

    print(
        "GitHub match:",
        identity.get(
            "github_match"
        ),
    )

    print(
        "LinkedIn match:",
        identity.get(
            "linkedin_match"
        ),
    )

    print(
        "GitHub score:",
        identity.get(
            "github_username_score"
        ),
    )

    print(
        "LinkedIn score:",
        identity.get(
            "linkedin_username_score"
        ),
    )

    # ========================================================
    # CLAIM EVIDENCE
    # ========================================================

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

    # ========================================================
    # CLAIM DEBUG
    # ========================================================

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

    # ========================================================
    # CLAIM STATS
    # ========================================================

    claim_stats = calculate_claim_stats(
        claims
    )

    # ========================================================
    # EVIDENCE REPORT
    # ========================================================

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

    # ========================================================
    # RISK REPORT
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
    # SKILL → REPOSITORY MAPPING
    # ========================================================

    skill_repository_mapping = (
        build_skill_repository_mapping(
            claims,
            github_evidence,
        )
    )

    # ========================================================
    # CANDIDATE INTELLIGENCE
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
    # PROJECT → REPOSITORY MAPPING
    # ========================================================

    project_repository_mapping = (
        build_project_repository_mapping(
            claims,
            github_evidence,
        )
    )

    print(
        "\n========== CANDIDATE INTELLIGENCE DONE =========="
    )

    print(
        candidate_intelligence
    )

    # ========================================================
    # TRUST SCORE
    # ========================================================

    scoring = calculate_trust_score(
        identity,
        github_evidence,
    )

    verified_claims = claim_stats[
        "supported"
    ]

    # ========================================================
    # AI CONFIDENCE
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

    # ========================================================
    # STRENGTHS
    # ========================================================

    strengths = []

    strengths.append(
        f"Resume successfully extracted with "
        f"{len(resume_text)} characters of readable text."
    )

    # --------------------------------------------------------
    # GitHub evidence
    # --------------------------------------------------------

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

        strengths.append(
            "GitHub profile could not be verified."
        )

    # --------------------------------------------------------
    # GitHub identity
    # --------------------------------------------------------

    if identity.get(
        "github_match",
        False,
    ):

        strengths.append(
            "GitHub identity is consistent "
            "with the resume."
        )

    # --------------------------------------------------------
    # LinkedIn identity
    # --------------------------------------------------------

    if identity.get(
        "linkedin_match",
        False,
    ):

        strengths.append(
            "LinkedIn identity is consistent "
            "with the resume."
        )

    # --------------------------------------------------------
    # LinkedIn authorization
    # --------------------------------------------------------

    if linkedin_evidence.get(
        "authorized_source",
        False,
    ):

        strengths.append(
            "LinkedIn profile was connected "
            "through an authorized integration."
        )

    # --------------------------------------------------------
    # Technology evidence
    # --------------------------------------------------------

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
    # WARNINGS
    # ========================================================

    warnings = []

    # --------------------------------------------------------
    # GitHub identity warning
    # --------------------------------------------------------

    if not identity.get(
        "github_match",
        False,
    ):

        warnings.append(
            "GitHub identity does not match "
            "the name detected in the resume."
        )

    # --------------------------------------------------------
    # LinkedIn identity warning
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # LinkedIn authorization warning
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GitHub profile warning
    # --------------------------------------------------------

    if not github_evidence.get(
        "profile_found",
        False,
    ):

        warnings.append(
            "GitHub profile could not be verified."
        )

    # --------------------------------------------------------
    # Claim warnings
    # --------------------------------------------------------

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

    # ========================================================
    # FINAL LINKEDIN STATUS
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

    print("\n========== FINAL LINKEDIN STATUS ==========")

    print(
        "Authorized:",
        linkedin_evidence.get(
            "authorized_source",
            False,
        ),
    )

    print(
        "Identity match:",
        identity.get(
            "linkedin_match",
            False,
        ),
    )

    print(
        "LinkedIn verified:",
        linkedin_verified,
    )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        # ----------------------------------------------------
        # Core scoring
        # ----------------------------------------------------

        "trust_score": scoring[
            "trust_score"
        ],

        "ai_confidence": ai_confidence,

        "verified_claims": verified_claims,

        "risk_level": scoring[
            "risk_level"
        ],

        "recruiter_verdict": scoring[
            "recruiter_verdict"
        ],

        # ----------------------------------------------------
        # Claims
        # ----------------------------------------------------

        "claim_stats": claim_stats,

        "claims": claims,

        "skills": skills,

        # ----------------------------------------------------
        # Identity
        # ----------------------------------------------------

        "identity": identity,

        # ----------------------------------------------------
        # GitHub
        # ----------------------------------------------------

        "github_evidence": github_evidence,

        "github": github,

        # ----------------------------------------------------
        # LinkedIn
        # ----------------------------------------------------

        "linkedin": linkedin,

        "linkedin_evidence": linkedin_evidence,

        "linkedin_summary": linkedin_summary,

        "linkedin_verified": linkedin_verified,

        # ----------------------------------------------------
        # Reports
        # ----------------------------------------------------

        "evidence_report": evidence_report,

        "risk_report": risk_report,

        "risk_summary": risk_summary,

        # ----------------------------------------------------
        # Intelligence
        # ----------------------------------------------------

        "candidate_intelligence": candidate_intelligence,

        "skill_repository_mapping": (
            skill_repository_mapping
        ),

        "project_repository_mapping": (
            project_repository_mapping
        ),

        # ----------------------------------------------------
        # Strengths / warnings
        # ----------------------------------------------------

        "strengths": strengths,

        "warnings": warnings,

        # ----------------------------------------------------
        # Resume information
        # ----------------------------------------------------

        "resume_file_name": resume.filename,

        "resume_characters": len(
            resume_text
        ),

        "resume_preview": (
            resume_text[:2000]
        ),
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
    """
    LinkedIn OAuth callback.
    """

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

    if not validate_oauth_state(
        state
    ):

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

    linkedin_data = (
        consume_oauth_result(
            code
        )
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

    print(
        "LinkedIn data:",
        linkedin_data,
    )

    return {
        "code": code,
        "linkedin": linkedin_data,
    }