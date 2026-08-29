from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from io import BytesIO
import json


from pypdf import PdfReader


# ============================================================
# CORE ANALYSIS MODULES
# ============================================================

from backend.ai.claims import (
    extract_claims,
)

from backend.ai.identity import (
    extract_resume_name,
    compare_identity,
)

from backend.ai.scoring import (
    calculate_trust_score,
)

from backend.ai.github import (
    analyze_github,
)

from backend.ai.confidence import (
    calculate_confidence,
)


# ============================================================
# EVIDENCE
# ============================================================

from backend.ai.evidence import (
    build_evidence_report,
    enrich_claims_with_github,
    calculate_claim_stats,
)


# ============================================================
# LINKEDIN
# ============================================================

from backend.ai.linkedin import (
    analyze_linkedin_evidence,
    enrich_claims_with_linkedin,
    build_linkedin_summary,
)


# ============================================================
# RISK ENGINE
# ============================================================

from backend.ai.risk_engine import (
    build_risk_report,
    calculate_risk_summary,
)


# ============================================================
# SKILL MAPPING
# ============================================================

from backend.ai.skill_mapping import (
    build_skill_repository_mapping,
)


# ============================================================
# CANDIDATE INTELLIGENCE
# ============================================================

from backend.ai.candidate_intelligence import (
    build_candidate_intelligence,
)


# ============================================================
# GEMINI CANDIDATE INSIGHT
# ============================================================

from backend.ai.gemini_candidate import (
    generate_candidate_insight,
)


# ============================================================
# PROJECT MATCHING
# ============================================================

from backend.ai.project_matching import (
    build_project_repository_mapping,
)


# ============================================================
# LINKEDIN OAUTH
# ============================================================

from backend.ai.linkedin_oauth import (
    build_linkedin_authorization_url,
    validate_oauth_state,
    exchange_code_for_token,
    fetch_authorized_linkedin_data,
    create_oauth_result,
    consume_oauth_result,
)


# ============================================================
# RAG KNOWLEDGE LAYER
#
# IMPORTANT:
# build_candidate_knowledge remains in rag.py.
# ============================================================

from backend.ai.rag import (
    build_candidate_knowledge,
)


# ============================================================
# RAG ENGINE
#
# IMPORTANT:
# These functions belong to the retrieval / verification layer.
# ============================================================

from backend.ai.rag_engine import (
    verify_claim_with_rag,
    retrieve_candidate_evidence,
    
)


# ============================================================
# JARVIS
# ============================================================

from backend.ai.jarvis_controller import (
    process_jarvis_command,
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="PersonaDNA API",
)


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


def extract_skills(
    resume_text: str,
) -> list[str]:

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
        "message": "Welcome to PersonaDNA API",
        "rag_enabled": True,
        "jarvis_enabled": True,
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
            detail="The PDF does not contain readable text.",
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

    github = (
        str(github or "")
        .strip()
        .strip("`\"'")
    )

    print("\n========== GITHUB INPUT DEBUG ==========")

    print(
        "Raw/Cleaned GitHub URL:",
        repr(github),
    )

    github_evidence = analyze_github(
        github
    )
    print("\n========== GITHUB EVIDENCE RAG DEBUG ==========")
    print(
        "profile_found:",
        github_evidence.get("profile_found")
    )
    print(
        "repository_count:",
        github_evidence.get("repository_count")
    )
    print(
        "repositories:",
        len(github_evidence.get("repositories", []))
    )
    print(
        "technology_evidence:",
        len(github_evidence.get("technology_evidence", []))
    )
    print(
        "skill_evidence:",
        len(github_evidence.get("skill_evidence", []))
    )
    print(
        "github_evidence keys:",
        list(github_evidence.keys())
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
    # 8. LINKEDIN IDENTITY
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


    if not linkedin_identity_name:

        linkedin_identity_name = str(
            linkedin_evidence.get(
                "display_name",
                "",
            )
        ).strip()


    print(
        "LinkedIn identity:",
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
    # 11. RAG CLAIM VERIFICATION
    #
    # IMPORTANT:
    # RAG verification happens AFTER all external evidence
    # has been collected.
    # ========================================================

    print("\n========== RAG VERIFICATION ==========")

    for claim in claims:

        claim_text = str(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        if not claim_text:

            claim["rag_status"] = "needs_review"
            claim["rag_confidence"] = 0
            claim["rag_evidence"] = []
            claim["rag_sources"] = []

            continue

        try:

            result = verify_claim_with_rag(
                claim=claim_text,
                resume_text=resume_text,
                github_evidence=github_evidence,
                linkedin_evidence=linkedin_evidence,
            )

            if not isinstance(
                result,
                dict,
            ):

                result = {}

            claim["rag_status"] = result.get(
                "status",
                "needs_review",
            )

            claim["rag_confidence"] = result.get(
                "confidence",
                0,
            )

            claim["rag_evidence"] = result.get(
                "evidence",
                [],
            )

            claim["rag_sources"] = result.get(
                "sources",
                [],
            )

            # ------------------------------------------------
            # Apply RAG verification to final claim status
            # ------------------------------------------------

            rag_status = str(
                claim.get(
                    "rag_status",
                    "needs_review",
                )
            ).lower().strip()

            rag_confidence = int(
                claim.get(
                    "rag_confidence",
                    0,
                ) or 0
            )

            if (
                rag_status == "supported"
                and rag_confidence >= 90
            ):
                claim["status"] = "supported"

            elif rag_status == "partially_supported":
                claim["status"] = "needs_review"

            # ------------------------------------------------
            # Direct authorized certification verification
            #
            # A matching authorized LinkedIn certification
            # is sufficient external evidence.
            #
            # Credential ID / URL is NOT required.
            # ------------------------------------------------

            if (
                claim.get("type") == "certification"
                and claim.get(
                    "evidence",
                    {},
                ).get(
                    "linkedin",
                    False,
                )
            ):

                claim["status"] = "supported"

                claim["rag_status"] = "supported"

                claim["rag_confidence"] = max(
                    claim.get(
                        "rag_confidence",
                        0,
                    ),
                    90,
                )

                claim.setdefault(
                    "rag_evidence",
                    [],
                )

                claim["rag_evidence"].append(
                    {
                        "source": "linkedin_authorized_api",
                        "text": (
                            "Certification title matched "
                            "against authorized LinkedIn "
                            "certification data."
                        ),
                        "confidence": 90,
                    }
                )

                claim["rag_sources"] = list(
                    dict.fromkeys(
                        claim.get(
                            "rag_sources",
                            [],
                        )
                        + [
                            "linkedin_authorized_api"
                        ]
                    )
                )

        except Exception as exc:

            print(
                "RAG verification error:",
                repr(exc),
            )

            claim["rag_status"] = "needs_review"
            claim["rag_confidence"] = 0
            claim["rag_evidence"] = []
            claim["rag_sources"] = []


    print(
        "RAG verification completed."
    )


    # ========================================================
    # 12. LINKEDIN SUMMARY
    # ========================================================

    linkedin_summary = build_linkedin_summary(
        linkedin_evidence
    )

    print("\n========== ALL CLAIMS ==========")

    for i, claim in enumerate(claims, 1):
        print(
            f"{i}. {claim.get('claim')} | "
            f"TYPE: {claim.get('type')} | "
            f"STATUS: {claim.get('status')} | "
            f"EVIDENCE: {claim.get('evidence')}"
        )

    print("========== END ALL CLAIMS ==========\n")


    # ========================================================
    # 13. CLAIM STATS
    # ========================================================

    claim_stats = calculate_claim_stats(
        claims
    )

    print("\n========== ALL CLAIMS ==========")

    for i, claim in enumerate(claims, 1):
        print(
            f"{i}. {claim.get('claim')} | "
            f"TYPE: {claim.get('type')} | "
            f"STATUS: {claim.get('status')} | "
            f"EVIDENCE: {claim.get('evidence')}"
        )

    print("========== END ALL CLAIMS ==========\n")

    # ============================================================
    # FINAL CLAIM STATUS DEBUG
    # ============================================================

    debug_file = BASE_DIR.parent / "claim_debug.txt"

    with open(debug_file, "w", encoding="utf-8") as f:

        f.write(
            "========== FINAL CLAIM STATUS DEBUG ==========\n\n"
        )

        for claim in claims:

            f.write(
                f"CLAIM: {claim.get('claim')}\n"
                f"TYPE: {claim.get('type')}\n"
                f"STATUS: {claim.get('status')}\n"
                f"RAG STATUS: {claim.get('rag_status')}\n"
                f"EVIDENCE: {claim.get('evidence')}\n"
                f"RAG CONFIDENCE: {claim.get('rag_confidence')}\n"
                f"RAG EVIDENCE: {claim.get('rag_evidence')}\n"
                f"RAG SOURCES: {claim.get('rag_sources')}\n"
                f"{'-' * 70}\n"
            )

        f.write(
            "\n========== END DEBUG ==========\n"
        )

    print(
        f"\n[DEBUG] Claim status report saved to: {debug_file}"
    )

    # ========================================================
    # 14. EVIDENCE REPORT
    # ========================================================

    evidence_report = build_evidence_report(
        claims,
        github_evidence,
    )


    # ========================================================
    # 15. RISK REPORT
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
    # 16. SKILL → REPOSITORY
    # ========================================================

    skill_repository_mapping = (
        build_skill_repository_mapping(
            claims,
            github_evidence,
        )
    )


    # ========================================================
    # 17. CANDIDATE INTELLIGENCE
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
    # 18. PROJECT → REPOSITORY
    # ========================================================

    project_repository_mapping = (
        build_project_repository_mapping(
            claims,
            github_evidence,
        )
    )


    # ========================================================
    # 19. CANDIDATE KNOWLEDGE
    #
    # IMPORTANT:
    # This is the actual knowledge base used by RAG.
    # ========================================================

    candidate_knowledge = (
        build_candidate_knowledge(
            resume_text=resume_text,
            claims=claims,
            github_evidence=github_evidence,
            linkedin_evidence=linkedin_evidence,
            candidate_intelligence=candidate_intelligence,
            skill_repository_mapping=skill_repository_mapping,
            project_repository_mapping=project_repository_mapping,
            identity=identity,
        )
    )

    print(
        "\n========== CANDIDATE RAG KNOWLEDGE =========="
    )

    print(
        "Knowledge characters:",
        len(candidate_knowledge)
        if isinstance(candidate_knowledge, str)
        else "structured",
    )


    # ========================================================
    # 19.5 RETRIEVAL SANITY CHECK
    #
    # This makes sure the candidate knowledge can actually be
    # searched before recruiter questions are answered.
    # ========================================================

    rag_retrieval_status = {
        "enabled": True,
        "candidate_knowledge_available": bool(
            candidate_knowledge
        ),
        "retrieval_tested": False,
    }

    try:

        if isinstance(
            candidate_knowledge,
            str,
        ) and candidate_knowledge.strip():

            retrieval_test = retrieve_candidate_evidence(
                query="candidate skills experience projects",
                candidate_knowledge=candidate_knowledge,
            )

            rag_retrieval_status["retrieval_tested"] = True

            if isinstance(
                retrieval_test,
                dict,
            ):

                rag_retrieval_status[
                    "retrieved_chunks"
                ] = len(
                    retrieval_test.get(
                        "evidence",
                        retrieval_test.get(
                            "chunks",
                            [],
                        ),
                    )
                    or []
                )

            elif isinstance(
                retrieval_test,
                list,
            ):

                rag_retrieval_status[
                    "retrieved_chunks"
                ] = len(
                    retrieval_test
                )

    except Exception as exc:

        print(
            "RAG retrieval sanity check failed:",
            repr(exc),
        )

        rag_retrieval_status[
            "retrieval_error"
        ] = str(exc)


    # ========================================================
    # 19.6 GEMINI CANDIDATE INSIGHT
    # ========================================================

    try:

        gemini_candidate_insight = (
            generate_candidate_insight(
                candidate_knowledge
            )
        )

    except Exception as exc:

        print(
            "\n========== GEMINI WARNING =========="
        )

        print(
            "Gemini candidate insight unavailable:"
        )

        print(
            repr(exc)
        )

        print(
            "Continuing analysis without Gemini insight."
        )

        print(
            "===================================="
        )

        gemini_candidate_insight = {
            "status": "unavailable",
            "reason": (
                "Gemini API quota exhausted "
                "or temporarily unavailable."
            ),
        }


    # ========================================================
    # 20. TRUST SCORE
    # ========================================================

    scoring = calculate_trust_score(
        identity=identity,
        github_evidence=github_evidence,
        claims=claims,
        evidence_report=evidence_report,
        linkedin_evidence=linkedin_evidence,
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


    # ========================================================
    # 21. VERIFIED CLAIMS
    # ========================================================

    verified_claims = claim_stats.get(
        "supported",
        0,
    )


    # ========================================================
    # 22. AI CONFIDENCE
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
    # 23. STRENGTHS
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
            "GitHub identity is consistent with the resume."
        )

    if identity.get(
        "linkedin_match",
        False,
    ):

        strengths.append(
            "LinkedIn identity is consistent with the resume."
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
    # 24. WARNINGS
    # ========================================================

    warnings = []

    if github and not identity.get(
        "github_match",
        False,
    ):
        warnings.append(
            "GitHub identity could not be matched "
            "with the name detected in the resume."
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
    # 25. LINKEDIN VERIFIED
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
    # 26. RAG RESULTS
    # ========================================================

    rag_verified_claims = []

    for claim in claims:

        rag_verified_claims.append(
            {
                "claim": claim.get(
                    "claim",
                    "",
                ),
                "status": claim.get(
                    "rag_status",
                    "needs_review",
                ),
                "confidence": claim.get(
                    "rag_confidence",
                    0,
                ),
                "evidence": claim.get(
                    "rag_evidence",
                    [],
                ),
                "sources": claim.get(
                    "rag_sources",
                    [],
                ),
            }
        )


    # ========================================================
    # 27. FINAL RESPONSE
    # ========================================================

    return {
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

        "claim_stats": claim_stats,

        "debug_claim_stats": {
            "supported": claim_stats.get("supported", 0),
            "needs_review": claim_stats.get("needs_review", 0),
            "detected": claim_stats.get("detected", 0),
        },

        "claims": claims,

        "skills": skills,

        "identity": identity,

        "github_evidence": github_evidence,

        "github": github,

        "linkedin": linkedin,

        "linkedin_evidence": linkedin_evidence,

        "linkedin_summary": linkedin_summary,

        "linkedin_verified": linkedin_verified,

        "evidence_report": evidence_report,

        "risk_report": risk_report,

        "risk_summary": risk_summary,

        "candidate_intelligence": (
            candidate_intelligence
        ),

        "skill_repository_mapping": (
            skill_repository_mapping
        ),

        "project_repository_mapping": (
            project_repository_mapping
        ),

        "candidate_knowledge": (
            candidate_knowledge
        ),

        "rag_enabled": True,

        "rag_retrieval": (
            rag_retrieval_status
        ),

        "rag_verified_claims": (
            rag_verified_claims
        ),

        "gemini_candidate_insight": (
            gemini_candidate_insight
        ),

        "strengths": strengths,

        "warnings": warnings,

        "resume_file_name": resume.filename,

        "resume_characters": len(
            resume_text
        ),

        "resume_preview": (
            resume_text[:2000]
        ),
    }


# ============================================================
# JARVIS COMMAND
# ============================================================

@app.post("/jarvis")
async def jarvis_command(
    command: str = Form(...),
    analysis_result: str = Form("{}"),
):

    try:

        candidate_data = json.loads(
            analysis_result
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        candidate_data = {}

    try:

        response = process_jarvis_command(
            command=command,
            analysis_result=candidate_data,
        )

    except TypeError:

        response = process_jarvis_command(
            command,
            candidate_data,
        )

    return {
        "command": command,
        "response": response,
        "rag_enabled": True,
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

    if error:

        raise HTTPException(
            status_code=400,
            detail=(
                "LinkedIn authorization failed: "
                f"{error_description or error}"
            ),
        )

    if not code:

        raise HTTPException(
            status_code=400,
            detail=(
                "LinkedIn authorization code is missing."
            ),
        )

    if not validate_oauth_state(state):

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state.",
        )

    try:

        token_data = exchange_code_for_token(
            code
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

        print(
            "LinkedIn authorized data received."
        )

        result_code = create_oauth_result(
            linkedin_data
        )

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
                "LinkedIn result code is missing."
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