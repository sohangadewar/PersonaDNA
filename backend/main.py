from io import BytesIO
import json
import re
import time
from typing import Any

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pypdf import PdfReader

from backend.models.report import CandidateReport

from backend.ai.claims import extract_claims

from backend.ai.identity import (
    extract_resume_name,
    compare_identity,
)

from backend.ai.github import analyze_github

from backend.ai.linkedin import (
    analyze_linkedin_evidence,
    enrich_claims_with_linkedin,
)

from backend.ai.rag_engine import (
    verify_claim_with_rag,
)

from backend.ai.gemini_candidate import (
    generate_candidate_insight,
)

from backend.ai.candidate_intelligence import (
    build_candidate_intelligence,
    build_candidate_knowledge,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="PersonaDNA API",
    version="1.0.0",
    description="AI-powered candidate verification and trust analysis API.",
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "PersonaDNA API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }


# ============================================================
# ANALYZE ENDPOINT
# ============================================================

@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    github_url: str = Form(""),
    linkedin_url: str = Form(""),
    linkedin_result: str = Form(""),
):
    return await verify_candidate(
        resume=resume,
        github_url=github_url,
        linkedin_url=linkedin_url,
        linkedin_result=linkedin_result,
    )

# ============================================================
# COMMON SKILLS
# ============================================================

COMMON_SKILLS = [
    "Python",
    "Java",
    "JavaScript",
    "React",
    "HTML",
    "CSS",
    "FastAPI",
    "Flask",
    "REST",
    "SQL",
    "PostgreSQL",
    "Artificial Intelligence",
    "Machine Learning",
    "Data Science",
    "Git",
    "GitHub",
    "Google Cloud",
    "RAG",
    "LangChain",
]


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {
    "reactjs": "React",
    "react.js": "React",

    "nodejs": "Node.js",
    "node.js": "Node.js",

    "expressjs": "Express",
    "express.js": "Express",

    "rest api": "REST",
    "restful api": "REST",

    "artificial intelligence": "Artificial Intelligence",
    "ai": "Artificial Intelligence",

    "machine-learning": "Machine Learning",
    "machine learning": "Machine Learning",

    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",

    "google cloud platform": "Google Cloud",
    "gcp": "Google Cloud",

    "github": "GitHub",
}

# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value: Any) -> str:
    """
    Normalize text for deterministic matching.
    """

    if value is None:
        return ""

    text = str(value).lower().strip()

    replacements = {
        "machine-learning": "machine learning",
        "scikit-learn": "scikit learn",
        "react.js": "react",
        "reactjs": "react",
        "node.js": "node",
        "nodejs": "node",
        "express.js": "express",
        "expressjs": "express",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r"[^a-z0-9+#.\- ]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# CANONICAL SKILL
# ============================================================

def canonical_skill(skill: Any) -> str:
    """
    Convert skill names into a deterministic canonical form.
    """

    value = normalize_text(skill)

    if not value:
        return ""

    return SKILL_ALIASES.get(
        value,
        value,
    )


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(resume_text: str) -> list[str]:
    """
    Extract skills from the resume.

    Returns canonical skill names only.
    Removes duplicate aliases such as:
        React / ReactJS
        AI / Artificial Intelligence
        REST / REST API
    """

    if not resume_text:
        return []

    normalized_resume = normalize_text(resume_text)

    found_skills = []
    seen = set()

    for skill in COMMON_SKILLS:

        normalized_skill = canonical_skill(skill)

        if not normalized_skill:
            continue

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(normalized_skill)
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, normalized_resume):

            canonical = canonical_skill(skill)

            if canonical not in seen:
                found_skills.append(canonical)
                seen.add(canonical)

    return found_skills

# ============================================================
# URL CLEANING
# ============================================================

def clean_url(
    value: str | None,
) -> str:
    """
    Clean URLs received from multipart form data.
    """

    if not value:
        return ""

    value = str(value).strip()

    value = value.strip("`")
    value = value.strip('"')
    value = value.strip("'")

    return value.strip()


# ============================================================
# LINKEDIN PROFILE PARSER
# ============================================================

def parse_linkedin_profile(
    linkedin_profile: str | None,
) -> dict | None:
    """
    Parse LinkedIn OAuth result JSON.
    """

    if not linkedin_profile:
        return None

    try:
        parsed = json.loads(
            linkedin_profile
        )

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return None

    if not isinstance(
        parsed,
        dict,
    ):
        return None

    linkedin_data = parsed.get(
        "linkedin"
    )

    if isinstance(
        linkedin_data,
        dict,
    ):
        return linkedin_data

    return parsed


# ============================================================
# LINKEDIN NAME
# ============================================================

def get_linkedin_name(
    profile_data: dict | None,
    linkedin_evidence: dict,
) -> str:
    """
    Extract LinkedIn display name.
    """

    if isinstance(
        profile_data,
        dict,
    ):

        name = str(
            profile_data.get(
                "name",
                "",
            )
        ).strip()

        if name:
            return name

        first_name = str(
            profile_data.get(
                "first_name",
                "",
            )
        ).strip()

        last_name = str(
            profile_data.get(
                "last_name",
                "",
            )
        ).strip()

        combined = " ".join(
            part
            for part in (
                first_name,
                last_name,
            )
            if part
        ).strip()

        if combined:
            return combined

    return str(
        linkedin_evidence.get(
            "display_name",
            "",
        )
    ).strip()


# ============================================================
# GITHUB REPOSITORY SKILL MATCHING
# ============================================================

def repository_has_skill(
    skill: str,
    repository: dict,
) -> tuple[bool, list[str]]:
    """
    Check whether a GitHub repository contains
    evidence for a particular skill.
    """

    if not isinstance(
        repository,
        dict,
    ):
        return False, []

    target = canonical_skill(
        skill
    )

    if not target:
        return False, []

    evidence_sources = []

    # --------------------------------------------------------
    # TECHNOLOGIES
    # --------------------------------------------------------

    technologies = repository.get(
        "technologies",
        [],
    )

    if isinstance(
        technologies,
        list,
    ):

        for technology in technologies:

            if canonical_skill(
                technology
            ) == target:

                evidence_sources.append(
                    "technology"
                )

                break

    # --------------------------------------------------------
    # PRIMARY LANGUAGE
    # --------------------------------------------------------

    language = repository.get(
        "language",
        "",
    )

    if language:

        if canonical_skill(
            language
        ) == target:

            evidence_sources.append(
                "language"
            )

    # --------------------------------------------------------
    # LANGUAGE STATISTICS
    # --------------------------------------------------------

    languages = repository.get(
        "languages",
        {},
    )

    if isinstance(
        languages,
        dict,
    ):

        for language_name in languages.keys():

            if canonical_skill(
                language_name
            ) == target:

                evidence_sources.append(
                    "languages"
                )

                break

    return (
        bool(evidence_sources),
        sorted(
            set(evidence_sources)
        ),
    )


# ============================================================
# SKILL → REPOSITORY MAPPING
# ============================================================

def map_skill_to_repositories(
    skill: str,
    repositories: list[dict],
) -> list[dict]:
    """
    Return repositories containing evidence
    for a particular skill.
    """

    matches = []

    if not isinstance(
        repositories,
        list,
    ):
        return matches

    for repository in repositories:

        if not isinstance(
            repository,
            dict,
        ):
            continue

        matched, evidence_sources = (
            repository_has_skill(
                skill,
                repository,
            )
        )

        if not matched:
            continue

        matches.append(
            {
                "repository": repository.get(
                    "name",
                    "",
                ),
                "matched_evidence": (
                    evidence_sources
                ),
                "language": repository.get(
                    "language",
                    "",
                ),
                "technologies": repository.get(
                    "technologies",
                    [],
                ),
                "languages": repository.get(
                    "languages",
                    {},
                ),
                "has_readme": bool(
                    repository.get(
                        "has_readme",
                        False,
                    )
                ),
                "dependency_files": repository.get(
                    "dependency_files",
                    {},
                ),
            }
        )

    return matches


# ============================================================
# COMPLETE SKILL REPOSITORY MAPPING
# ============================================================

def build_skill_repository_mapping(
    claims: list[dict],
    github_evidence: dict,
) -> dict:

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if not isinstance(
        repositories,
        list,
    ):
        repositories = []

    mapping = {}

    for claim in claims:

        if not isinstance(
            claim,
            dict,
        ):
            continue

        if claim.get(
            "type"
        ) != "skill":
            continue

        skill = str(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        if not skill:
            continue

        mapping[skill] = (
            map_skill_to_repositories(
                skill,
                repositories,
            )
        )

    return mapping


# ============================================================
# GITHUB CLAIM ENRICHMENT
# ============================================================

def enrich_claims_with_github(
    claims: list,
    github_evidence: dict,
) -> list:
    """
    Add GitHub evidence to skill claims.

    GitHub evidence is not automatically treated as final
    verification. RAG performs the final verification.
    """

    if not isinstance(
        claims,
        list,
    ):
        return []

    if not isinstance(
        github_evidence,
        dict,
    ):
        github_evidence = {}

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if not isinstance(
        repositories,
        list,
    ):
        repositories = []

    github_found = bool(
        github_evidence.get(
            "profile_found",
            False,
        )
    )

    for claim in claims:

        if not isinstance(
            claim,
            dict,
        ):
            continue

        claim_text = str(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        if not claim_text:
            continue

        claim_type = str(
            claim.get(
                "type",
                "",
            )
        ).lower().strip()

        evidence = claim.get(
            "evidence",
            {},
        )

        if not isinstance(
            evidence,
            dict,
        ):
            evidence = {}

        # ----------------------------------------------------
        # ONLY SKILL CLAIMS
        # ----------------------------------------------------

        if claim_type != "skill":

            claim["evidence"] = evidence

            continue

        matches = map_skill_to_repositories(
            claim_text,
            repositories,
        )

        if github_found and matches:

            evidence["github"] = True

            evidence[
                "github_repository_count"
            ] = len(matches)

            evidence[
                "github_repositories"
            ] = [
                item.get(
                    "repository",
                    "",
                )
                for item in matches
            ]

            evidence[
                "github_match_sources"
            ] = sorted(
                {
                    source
                    for item in matches
                    for source in item.get(
                        "matched_evidence",
                        [],
                    )
                }
            )

        else:

            evidence.setdefault(
                "github",
                False,
            )

            evidence[
                "github_repository_count"
            ] = 0

            evidence[
                "github_repositories"
            ] = []

        claim["evidence"] = evidence

    return claims


# ============================================================
# RAG VERIFICATION
# ============================================================

def verify_claims(
    claims: list,
    resume_text: str,
    github_evidence: dict,
    linkedin_evidence: dict,
) -> list:
    """
    Verify every extracted claim using RAG.
    """

    if not isinstance(
        claims,
        list,
    ):
        return []

    rag_total_start = time.perf_counter()

    for index, claim in enumerate(
        claims,
        start=1,
    ):

        if not isinstance(
            claim,
            dict,
        ):
            continue

        claim_text = str(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        # ----------------------------------------------------
        # EMPTY CLAIM
        # ----------------------------------------------------

        if not claim_text:

            claim["rag_status"] = (
                "needs_review"
            )

            claim["rag_confidence"] = 0
            claim["rag_evidence"] = []
            claim["rag_sources"] = []
            claim["status"] = "needs_review"

            continue

        claim_start = time.perf_counter()

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

            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            rag_status = str(
                result.get(
                    "status",
                    "needs_review",
                )
            ).lower().strip()

            if rag_status not in {
                "supported",
                "needs_review",
            }:
                rag_status = "needs_review"

            # ------------------------------------------------
            # CONFIDENCE
            # ------------------------------------------------

            rag_confidence = result.get(
                "confidence",
                0,
            )

            try:
                rag_confidence = int(
                    rag_confidence or 0
                )

            except (
                TypeError,
                ValueError,
            ):
                rag_confidence = 0

            rag_confidence = max(
                0,
                min(
                    rag_confidence,
                    100,
                ),
            )

            # ------------------------------------------------
            # EVIDENCE
            # ------------------------------------------------

            evidence = result.get(
                "evidence",
                [],
            )

            if not isinstance(
                evidence,
                list,
            ):
                evidence = []

            sources = result.get(
                "sources",
                [],
            )

            if not isinstance(
                sources,
                list,
            ):
                sources = []

            # ------------------------------------------------
            # STORE RAG RESULT
            # ------------------------------------------------

            claim["rag_status"] = rag_status

            claim["rag_confidence"] = (
                rag_confidence
            )

            claim["rag_evidence"] = evidence

            claim["rag_sources"] = sources

            claim["status"] = (
                "supported"
                if rag_status == "supported"
                else "needs_review"
            )

            # ------------------------------------------------
            # LINKEDIN CERTIFICATION OVERRIDE
            # ------------------------------------------------

            claim_type = str(
                claim.get(
                    "type",
                    "",
                )
            ).lower().strip()

            claim_evidence = claim.get(
                "evidence",
                {},
            )

            if not isinstance(
                claim_evidence,
                dict,
            ):
                claim_evidence = {}

            linkedin_certified = bool(
                claim_evidence.get(
                    "linkedin",
                    False,
                )
            )

            linkedin_authorized = bool(
                linkedin_evidence.get(
                    "authorized_source",
                    False,
                )
            )

            if (
                claim_type == "certification"
                and linkedin_certified
                and linkedin_authorized
            ):

                claim["status"] = "supported"

                claim["rag_status"] = "supported"

                claim["rag_confidence"] = max(
                    claim["rag_confidence"],
                    90,
                )

                linkedin_certification_evidence = {
                    "source": (
                        "linkedin_authorized_api"
                    ),
                    "text": (
                        "Certification title matched "
                        "against authorized LinkedIn "
                        "certification data."
                    ),
                    "confidence": 90,
                }

                existing_sources = [
                    item.get("source")
                    for item in claim.get(
                        "rag_evidence",
                        [],
                    )
                    if isinstance(
                        item,
                        dict,
                    )
                ]

                if (
                    "linkedin_authorized_api"
                    not in existing_sources
                ):

                    claim.setdefault(
                        "rag_evidence",
                        [],
                    ).append(
                        linkedin_certification_evidence
                    )

                claim.setdefault(
                    "rag_sources",
                    [],
                )

                if (
                    "linkedin_authorized_api"
                    not in claim[
                        "rag_sources"
                    ]
                ):

                    claim[
                        "rag_sources"
                    ].append(
                        "linkedin_authorized_api"
                    )

        except Exception as exc:

            print(
                "RAG verification error:",
                repr(claim_text),
            )

            print(
                "Error:",
                repr(exc),
            )

            claim["rag_status"] = (
                "needs_review"
            )

            claim["rag_confidence"] = 0
            claim["rag_evidence"] = []
            claim["rag_sources"] = []
            claim["status"] = "needs_review"

        claim_time = (
            time.perf_counter()
            - claim_start
        )

        print(
            f"RAG claim #{index}: "
            f"{claim_time:.2f}s | "
            f"{claim_text[:80]}"
        )

    rag_total_time = (
        time.perf_counter()
        - rag_total_start
    )

    print(
        f"TOTAL RAG VERIFICATION: "
        f"{rag_total_time:.2f}s"
    )

    return claims


# ============================================================
# CLAIM STATISTICS
# ============================================================

def calculate_claim_statistics(
    claims: list[dict],
) -> dict:

    valid_claims = [
        claim
        for claim in claims
        if isinstance(
            claim,
            dict,
        )
    ]

    total = len(
        valid_claims
    )

    supported = sum(
        1
        for claim in valid_claims
        if claim.get(
            "status"
        ) == "supported"
    )

    needs_review = sum(
        1
        for claim in valid_claims
        if claim.get(
            "status"
        ) == "needs_review"
    )

    return {
        "detected": total,
        "supported": supported,
        "needs_review": needs_review,
    }


# ============================================================
# TRUST SCORE
# ============================================================

def calculate_trust_score(
    verified_claims: int,
    total_claims: int,
    github_found: bool,
    repository_count: int,
    github_match: bool,
    linkedin_match: bool,
) -> int:
    """
    PersonaDNA trust score.

    Maximum = 100.

    Base processing          = 10
    GitHub profile           = 10
    GitHub repositories      = 10
    GitHub identity          = 15
    LinkedIn identity        = 15
    Claim verification       = 40
    """

    score = 10

    # GitHub profile
    if github_found:
        score += 10

    # GitHub repositories
    if repository_count > 0:
        score += 10

    # GitHub identity
    if github_match:
        score += 15

    # LinkedIn identity
    if linkedin_match:
        score += 15

    # Claim verification
    if total_claims > 0:

        claim_ratio = (
            verified_claims
            / total_claims
        )

        score += round(
            claim_ratio * 40
        )

    return max(
        0,
        min(
            score,
            100,
        ),
    )


# ============================================================
# AI CONFIDENCE
# ============================================================

def calculate_ai_confidence(
    verified_claims: int,
    total_claims: int,
    github_found: bool,
    github_match: bool,
    linkedin_match: bool,
) -> int:
    """
    Calculate confidence in the evidence pipeline.
    """

    components = []

    if total_claims > 0:

        claim_ratio = (
            verified_claims
            / total_claims
        )

        components.append(
            claim_ratio * 100
        )

    if github_found:
        components.append(90)

    if github_match:
        components.append(95)

    if linkedin_match:
        components.append(95)

    if not components:
        return 50

    confidence = int(
        sum(components)
        / len(components)
    )

    return max(
        0,
        min(
            confidence,
            100,
        ),
    )


# ============================================================
# RISK LEVEL
# ============================================================

def calculate_risk_level(
    trust_score: int,
) -> str:

    if trust_score >= 80:
        return "Low"

    if trust_score >= 60:
        return "Medium"

    return "High"


# ============================================================
# RECRUITER VERDICT
# ============================================================

def calculate_recruiter_verdict(
    trust_score: int,
) -> str:

    if trust_score >= 80:

        return (
            "Recommended for Technical Interview"
        )

    if trust_score >= 60:

        return (
            "Consider for Technical Interview "
            "after further verification"
        )

    return (
        "Further Verification Recommended"
    )


# ============================================================
# MAIN VERIFICATION PIPELINE
# ============================================================

async def verify_candidate(
    resume: UploadFile,
    github_url: str = "",
    linkedin_url: str = "",
    linkedin_result: str = "",
) -> CandidateReport:

    pipeline_start = time.perf_counter()

    print()
    print(
        "=============================================="
    )
    print(
        "       PERSONADNA VERIFICATION STARTED"
    )
    print(
        "=============================================="
    )

    # ========================================================
    # 1. VALIDATE RESUME
    # ========================================================

    if resume is None:

        raise HTTPException(
            status_code=400,
            detail="Resume file is required.",
        )

    # Some clients may send PDF with slightly different
    # content-type headers. Therefore also check extension.

    filename = (
        resume.filename or ""
    ).lower()

    content_type = (
        resume.content_type or ""
    ).lower()

    if (
        content_type != "application/pdf"
        and not filename.endswith(".pdf")
    ):

        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF resume.",
        )

    # ========================================================
    # 2. READ PDF
    # ========================================================

    pdf_start = time.perf_counter()

    try:

        file_bytes = await resume.read()

        if not file_bytes:

            raise HTTPException(
                status_code=400,
                detail="Uploaded resume is empty.",
            )

        reader = PdfReader(
            BytesIO(file_bytes)
        )

        resume_pages = []

        for page in reader.pages:

            try:

                page_text = (
                    page.extract_text()
                    or ""
                )

            except Exception as exc:

                print(
                    "Page extraction error:",
                    repr(exc),
                )

                page_text = ""

            resume_pages.append(
                page_text
            )

        resume_text = "\n".join(
            resume_pages
        )

    except HTTPException:

        raise

    except Exception as exc:

        print(
            "PDF reading error:",
            repr(exc),
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not read the uploaded PDF."
            ),
        ) from exc

    print(
        f"PDF reading: "
        f"{time.perf_counter() - pdf_start:.2f}s"
    )

    # ========================================================
    # 3. VALIDATE RESUME TEXT
    # ========================================================

    if not resume_text.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "The PDF does not contain readable text."
            ),
        )

    # ========================================================
    # 4. CLEAN INPUTS
    # ========================================================

    github_url = clean_url(
        github_url
    )

    linkedin_url = clean_url(
        linkedin_url
    )

    linkedin_result = clean_url(
        linkedin_result
    )

    print()
    print(
        "========== INPUT DEBUG =========="
    )

    print(
        "GitHub:",
        repr(github_url),
    )

    print(
        "LinkedIn:",
        repr(linkedin_url),
    )

    print(
        "LinkedIn OAuth result supplied:",
        bool(linkedin_result),
    )

    # ========================================================
    # 5. RESUME ANALYSIS
    # ========================================================

    resume_analysis_start = (
        time.perf_counter()
    )

    try:

        resume_name = extract_resume_name(
            resume_text
        )

    except Exception as exc:

        print(
            "Resume name extraction error:",
            repr(exc),
        )

        resume_name = ""

    try:

        claims = extract_claims(
            resume_text
        )

    except Exception as exc:

        print(
            "Claim extraction error:",
            repr(exc),
        )

        claims = []

    if not isinstance(
        claims,
        list,
    ):
        claims = []

    skills = extract_skills(
        resume_text
    )

    print(
        f"Resume analysis: "
        f"{time.perf_counter() - resume_analysis_start:.2f}s"
    )

    print()
    print(
        "========== RESUME DEBUG =========="
    )

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
    # 6. GITHUB ANALYSIS
    # ========================================================

    github_start = time.perf_counter()

    try:

        github_evidence = analyze_github(
            github_url
        )

        if not isinstance(
            github_evidence,
            dict,
        ):
            github_evidence = {}

    except Exception as exc:

        print(
            "GitHub analysis error:",
            repr(exc),
        )

        github_evidence = {
            "username": github_url,
            "profile_found": False,
            "display_name": "",
            "public_repositories": [],
            "repository_count": 0,
            "repositories": [],
            "technology_evidence": [],
            "skill_evidence": [],
            "evidence_status": "error",
        }

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if not isinstance(
        repositories,
        list,
    ):
        repositories = []

    try:

        repository_count = int(
            github_evidence.get(
                "repository_count",
                len(repositories),
            )
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        repository_count = len(
            repositories
        )

    github_found = bool(
        github_evidence.get(
            "profile_found",
            False,
        )
    )

    print(
        f"GitHub analysis: "
        f"{time.perf_counter() - github_start:.2f}s"
    )

    print()
    print(
        "========== GITHUB DEBUG =========="
    )

    print(
        "Profile found:",
        github_found,
    )

    print(
        "Display name:",
        github_evidence.get(
            "display_name",
            "",
        ),
    )

    print(
        "Repository count:",
        repository_count,
    )

    technology_evidence = (
        github_evidence.get(
            "technology_evidence",
            [],
        )
    )

    if not isinstance(
        technology_evidence,
        list,
    ):
        technology_evidence = []

    print(
        "Technology evidence:",
        len(technology_evidence),
    )

    # ========================================================
    # 7. LINKEDIN ANALYSIS
    # ========================================================

    linkedin_start = time.perf_counter()

    linkedin_profile_data = (
        parse_linkedin_profile(
            linkedin_result
        )
    )

    try:

        if linkedin_profile_data:

            linkedin_evidence = (
                analyze_linkedin_evidence(
                    linkedin_url=linkedin_url,
                    profile_data=linkedin_profile_data,
                    consent_granted=True,
                )
            )

        else:

            linkedin_evidence = (
                analyze_linkedin_evidence(
                    linkedin_url=linkedin_url,
                    profile_data=None,
                    consent_granted=False,
                )
            )

        if not isinstance(
            linkedin_evidence,
            dict,
        ):
            linkedin_evidence = {}

    except Exception as exc:

        print(
            "LinkedIn analysis error:",
            repr(exc),
        )

        linkedin_evidence = {
            "profile_found": False,
            "profile_data_available": False,
            "evidence_status": "error",
            "profile_url": linkedin_url,
            "consent_granted": False,
            "authorized_source": False,
            "display_name": "",
            "headline": "",
            "about": "",
            "verification_categories": [],
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "evidence": [],
        }

    linkedin_identity_name = (
        get_linkedin_name(
            linkedin_profile_data,
            linkedin_evidence,
        )
    )

    linkedin_authorized = bool(
        linkedin_evidence.get(
            "authorized_source",
            False,
        )
    )

    print(
        f"LinkedIn analysis: "
        f"{time.perf_counter() - linkedin_start:.2f}s"
    )

    print()
    print(
        "========== LINKEDIN DEBUG =========="
    )

    print(
        "LinkedIn name:",
        repr(linkedin_identity_name),
    )

    print(
        "Authorized:",
        linkedin_authorized,
    )

    print(
        "Evidence status:",
        linkedin_evidence.get(
            "evidence_status",
            "unknown",
        ),
    )

    # ========================================================
    # 8. IDENTITY VERIFICATION
    # ========================================================

    identity_start = time.perf_counter()

    try:

        identity = compare_identity(
            resume_name=resume_name,
            github=github_url,
            linkedin=linkedin_identity_name,
            github_display_name=(
                github_evidence.get(
                    "display_name",
                    "",
                )
            ),
        )

        if not isinstance(
            identity,
            dict,
        ):
            identity = {}

    except Exception as exc:

        print(
            "Identity comparison error:",
            repr(exc),
        )

        identity = {}

    github_match = bool(
        identity.get(
            "github_match",
            False,
        )
    )

    linkedin_match = bool(
        identity.get(
            "linkedin_match",
            False,
        )
    )

    # LinkedIn identity counts only if the authorized
    # LinkedIn source exists.

    if not linkedin_authorized:

        linkedin_match = False

    print(
        f"Identity verification: "
        f"{time.perf_counter() - identity_start:.2f}s"
    )

    print()
    print(
        "========== IDENTITY DEBUG =========="
    )

    print(
        "GitHub match:",
        github_match,
    )

    print(
        "LinkedIn match:",
        linkedin_match,
    )

    # ========================================================
    # 9. CLAIM ENRICHMENT
    # ========================================================

    enrichment_start = (
        time.perf_counter()
    )

    try:

        claims = enrich_claims_with_github(
            claims,
            github_evidence,
        )

    except Exception as exc:

        print(
            "GitHub claim enrichment error:",
            repr(exc),
        )

    try:

        claims = enrich_claims_with_linkedin(
            claims,
            linkedin_evidence,
        )

    except Exception as exc:

        print(
            "LinkedIn claim enrichment error:",
            repr(exc),
        )

    print(
        f"Claim enrichment: "
        f"{time.perf_counter() - enrichment_start:.2f}s"
    )

    # ========================================================
    # 10. RAG VERIFICATION
    # ========================================================

    print()
    print(
        "========== RAG VERIFICATION =========="
    )

    claims = verify_claims(
        claims=claims,
        resume_text=resume_text,
        github_evidence=github_evidence,
        linkedin_evidence=linkedin_evidence,
    )

    # ========================================================
    # 11. FINAL CLAIM DEBUG
    # ========================================================

    print()
    print(
        "========== FINAL CLAIMS =========="
    )

    for index, claim in enumerate(
        claims,
        start=1,
    ):

        if not isinstance(
            claim,
            dict,
        ):
            continue

        print()
        print(
            f"CLAIM #{index}"
        )

        print(
            "Claim:",
            claim.get(
                "claim"
            ),
        )

        print(
            "Type:",
            claim.get(
                "type"
            ),
        )

        print(
            "Evidence:",
            claim.get(
                "evidence"
            ),
        )

        print(
            "Status:",
            claim.get(
                "status"
            ),
        )

        print(
            "RAG Status:",
            claim.get(
                "rag_status"
            ),
        )

        print(
            "RAG Confidence:",
            claim.get(
                "rag_confidence"
            ),
        )

        print(
            "RAG Sources:",
            claim.get(
                "rag_sources"
            ),
        )

    # ========================================================
    # 12. CANDIDATE INTELLIGENCE
    # ========================================================

    candidate_intelligence_start = (
        time.perf_counter()
    )

    try:

        candidate_intelligence = (
            build_candidate_intelligence(
                claims=claims,
                github_evidence=github_evidence,
                identity=identity,
                resume_text=resume_text,
            )
        )

        if not isinstance(
            candidate_intelligence,
            dict,
        ):
            candidate_intelligence = {}

    except Exception as exc:

        print(
            "Candidate intelligence error:",
            repr(exc),
        )

        candidate_intelligence = {
            "overall_evidence_score": 0,
            "evidence_level": "none",
            "claim_evidence": [],
            "project_evidence": [],
            "suspicious_claims": [],
            "suspicious_claim_count": 0,
        }

    print(
        f"Candidate intelligence: "
        f"{time.perf_counter() - candidate_intelligence_start:.2f}s"
    )

    # ========================================================
    # 13. CLAIM STATISTICS
    # ========================================================

    claim_stats = (
        calculate_claim_statistics(
            claims
        )
    )

    total_claims = claim_stats[
        "detected"
    ]

    verified_claims = claim_stats[
        "supported"
    ]

    needs_review = claim_stats[
        "needs_review"
    ]

    print()
    print(
        "========== CLAIM STATISTICS =========="
    )

    print(
        "Total claims:",
        total_claims,
    )

    print(
        "Verified claims:",
        verified_claims,
    )

    print(
        "Needs review:",
        needs_review,
    )

    # ========================================================
    # 14. SKILL → REPOSITORY MAPPING
    # ========================================================

    skill_repository_mapping = (
        build_skill_repository_mapping(
            claims=claims,
            github_evidence=github_evidence,
        )
    )

    # ========================================================
    # 15. TRUST SCORE
    # ========================================================

    score = calculate_trust_score(
        verified_claims=verified_claims,
        total_claims=total_claims,
        github_found=github_found,
        repository_count=repository_count,
        github_match=github_match,
        linkedin_match=linkedin_match,
    )

    # ========================================================
    # 16. AI CONFIDENCE
    # ========================================================

    ai_confidence = (
        calculate_ai_confidence(
            verified_claims=verified_claims,
            total_claims=total_claims,
            github_found=github_found,
            github_match=github_match,
            linkedin_match=linkedin_match,
        )
    )

    # ========================================================
    # 17. RISK
    # ========================================================

    risk_level = calculate_risk_level(
        score
    )

    # ========================================================
    # 18. RECRUITER VERDICT
    # ========================================================

    recruiter_verdict = (
        calculate_recruiter_verdict(
            score
        )
    )

    # ========================================================
    # 19. WARNINGS
    # ========================================================

    warnings = []

    if not github_url:

        warnings.append(
            "GitHub profile was not provided."
        )

    elif not github_found:

        warnings.append(
            "GitHub profile could not be verified."
        )

    if total_claims == 0:

        warnings.append(
            "No verifiable claims were extracted "
            "from the resume."
        )

    elif needs_review > 0:

        warnings.append(
            f"{needs_review} resume claim(s) "
            "need further verification."
        )

    if linkedin_url and not linkedin_match:

        warnings.append(
            "LinkedIn identity could not be confirmed."
        )

    # ========================================================
    # SUSPICIOUS CLAIM COUNT
    # ========================================================

    suspicious_count = 0

    if isinstance(candidate_intelligence, dict):

        suspicious_count = candidate_intelligence.get(
            "suspicious_claim_count",
            0,
        )

    try:
        suspicious_count = int(
            suspicious_count or 0
        )

    except (TypeError, ValueError):

        suspicious_count = 0

    suspicious_count = max(
        0,
        suspicious_count,
    )

    if suspicious_count > 0:

        warnings.append(
            f"{suspicious_count} suspicious claim(s) "
            "require additional review."
        )

    # ========================================================
    # 20. STRENGTHS
    # ========================================================

    strengths = []

    if github_match:

        strengths.append(
            "Resume identity matches GitHub."
        )

    if linkedin_match:

        strengths.append(
            "Resume identity matches LinkedIn."
        )

    if repository_count > 0:

        strengths.append(
            "GitHub repositories provide project evidence."
        )

    if verified_claims > 0:

        strengths.append(
            f"{verified_claims} resume claim(s) "
            "were supported by available evidence."
        )

    if not strengths:

        strengths.append(
            "Candidate profile was successfully processed."
        )

    # ========================================================
    # 21. CANDIDATE KNOWLEDGE
    # ========================================================

    try:

        candidate_knowledge = (
            build_candidate_knowledge(
                resume_text=resume_text,
                claims=claims,
                github_evidence=github_evidence,
                linkedin_evidence=linkedin_evidence,
                candidate_intelligence=(
                    candidate_intelligence
                ),
                skill_repository_mapping=(
                    skill_repository_mapping
                ),
                project_repository_mapping={},
                identity=identity,
                trust_score=score,
                ai_confidence=ai_confidence,
                risk_level=risk_level,
                recruiter_verdict=recruiter_verdict,
            )
        )

    except Exception as exc:

        print(
            "Candidate knowledge error:",
            repr(exc),
        )

        candidate_knowledge = {
            "resume_text": resume_text,
            "claims": claims,
            "github_evidence": github_evidence,
            "linkedin_evidence": linkedin_evidence,
            "candidate_intelligence": candidate_intelligence,
            "trust_score": score,
            "ai_confidence": ai_confidence,
            "risk_level": risk_level,
            "recruiter_verdict": recruiter_verdict,
        }

    # ========================================================
    # 22. GEMINI CANDIDATE INSIGHT
    # ========================================================

    candidate_insight = ""

    try:

        print()
        print(
            "========== GEMINI CANDIDATE INSIGHT =========="
        )

        gemini_start = time.perf_counter()

        candidate_insight = (
            generate_candidate_insight(
                candidate_knowledge
            )
        )

        if candidate_insight is None:

            candidate_insight = ""

        candidate_insight = str(
            candidate_insight
        ).strip()

        print(
            f"Gemini generation: "
            f"{time.perf_counter() - gemini_start:.2f}s"
        )

        print(
            "Gemini output length:",
            len(candidate_insight),
        )

        if not candidate_insight:

            candidate_insight = (
                "AI candidate insight could not be generated."
            )

    except Exception as exc:

        print(
            "Gemini candidate insight error:",
            repr(exc),
        )

        candidate_insight = (
            "AI candidate insight could not be generated."
        )

    # ========================================================
    # 23. FINAL REPORT
    # ========================================================

    report = CandidateReport(
        trust_score=score,
        ai_confidence=ai_confidence,
        verified_claims=verified_claims,
        risk_level=risk_level,
        recruiter_verdict=recruiter_verdict,
        skills=skills,
        strengths=strengths,
        warnings=warnings,
        candidate_insight=candidate_insight,
    )

    # ========================================================
    # 24. FINAL DEBUG
    # ========================================================

    total_pipeline_time = (
        time.perf_counter()
        - pipeline_start
    )

    print()
    print(
        "========== PERSONADNA RESULT =========="
    )

    print(
        "Trust score:",
        report.trust_score,
    )

    print(
        "AI confidence:",
        report.ai_confidence,
    )

    print(
        "Verified claims:",
        report.verified_claims,
    )

    print(
        "Risk:",
        report.risk_level,
    )

    print(
        "Verdict:",
        report.recruiter_verdict,
    )

    print(
        "Skills:",
        len(report.skills),
    )

    print(
        "Gemini insight:",
        bool(report.candidate_insight),
    )

    print(
        "Gemini insight preview:",
        report.candidate_insight[:200],
    )

    print(
        f"TOTAL PIPELINE TIME: "
        f"{total_pipeline_time:.2f}s"
    )

    print(
        "======================================="
    )

    return report