from io import BytesIO
import json
import re
import time
from typing import Any

from fastapi import UploadFile, HTTPException
from pypdf import PdfReader

from backend.ai import identity
from backend.models.report import CandidateReport
from backend.ai.claims import extract_claims
from backend.ai.identity import extract_resume_name, compare_identity
from backend.ai.github import analyze_github
from backend.ai.linkedin import analyze_linkedin_evidence, enrich_claims_with_linkedin
from backend.ai.rag_engine import verify_claim_with_rag
from backend.ai.gemini_candidate import generate_candidate_insight
from backend.ai.candidate_intelligence import (
    build_candidate_intelligence,
    build_candidate_knowledge,
)

from backend.ai.project_matching import (
    build_project_repository_mapping,
)
from backend.ai.scoring import calculate_trust_score

COMMON_SKILLS = [
    "Python",
    "Java",
    "C++",
    "C",
    "JavaScript",
    "TypeScript",
    "Groovy",
    "React",
    "ReactJS",
    "Redux",
    "HTML",
    "CSS",
    "Tailwind CSS",
    "Node.js",
    "NodeJS",
    "Express.js",
    "ExpressJS",
    "FastAPI",
    "Flask",
    "Django",
    "REST API",
    "REST",
    "SQL",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "Redis",
    "Artificial Intelligence",
    "AI",
    "Machine Learning",
    "Deep Learning",
    "Data Science",
    "Data Analysis",
    "Data Structures",
    "Algorithms",
    "Object Oriented Programming",
    "Operating Systems",
    "DBMS",
    "Computer Networks",
    "Competitive Programming",
    "Git",
    "GitHub",
    "Docker",
    "AWS",
    "Google Cloud",
    "RAG",
    "LangChain",
]


def normalize_text(text: Any) -> str:
    if text is None:
        return ""

    text = str(text).lower().strip()

    replacements = {
        "machine-learning": "machine learning",
        "machine_learning": "machine learning",
        "scikit-learn": "scikit learn",
        "scikit_learn": "scikit learn",
        "react.js": "react",
        "reactjs": "react",
        "nodejs": "node.js",
        "expressjs": "express.js",
        "object-oriented programming": "object oriented programming",
        "artificial-intelligence": "artificial intelligence",
        "google cloud platform": "google cloud",
        "gcp": "google cloud",
        "postgres": "postgresql",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9+#.\- ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def canonical_skill(skill: Any) -> str:
    normalized = normalize_text(skill)

    aliases = {
        "reactjs": "react",
        "react.js": "react",
        "nodejs": "node.js",
        "expressjs": "express.js",
        "rest": "rest api",
        "artificial intelligence": "ai",
        "machine-learning": "machine learning",
        "scikit learn": "scikit-learn",
        "postgres": "postgresql",
        "google cloud platform": "google cloud",
        "gcp": "google cloud",
    }

    return aliases.get(
        normalized,
        normalized,
    )


def get_display_skill(skill: str) -> str:
    canonical = canonical_skill(skill)

    display_names = {
        "react": "React",
        "node.js": "Node.js",
        "express.js": "Express.js",
        "rest api": "REST API",
        "ai": "Artificial Intelligence",
        "machine learning": "Machine Learning",
        "scikit-learn": "Scikit-Learn",
        "postgresql": "PostgreSQL",
        "google cloud": "Google Cloud",
        "git": "Git",
        "github": "GitHub",
    }

    return display_names.get(
        canonical,
        str(skill).strip(),
    )


def extract_skills(resume_text: str) -> list[str]:
    if not resume_text:
        return []

    normalized_resume = normalize_text(resume_text)
    found_skills = []
    seen_canonical = set()

    for skill in COMMON_SKILLS:
        normalized_skill = normalize_text(skill)
        canonical = canonical_skill(skill)

        if not normalized_skill:
            continue

        pattern = r"(?<![a-z0-9])" + re.escape(normalized_skill) + r"(?![a-z0-9])"

        if re.search(pattern, normalized_resume):
            if canonical not in seen_canonical:
                found_skills.append(get_display_skill(skill))
                seen_canonical.add(canonical)

    return found_skills


def clean_url(value: str | None) -> str:
    if not value:
        return ""

    return str(value).strip().strip("`").strip('"').strip("'")


def parse_linkedin_profile(linkedin_profile: str | None) -> dict | None:
    if not linkedin_profile:
        return None

    try:
        parsed = json.loads(linkedin_profile)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None

    if not isinstance(parsed, dict):
        return None

    linkedin_data = parsed.get("linkedin")

    if isinstance(linkedin_data, dict):
        return linkedin_data

    return parsed


def get_linkedin_name(
    profile_data: dict | None,
    linkedin_evidence: dict,
) -> str:
    if isinstance(profile_data, dict):
        name = str(profile_data.get("name", "")).strip()
        if name:
            return name

        first_name = str(profile_data.get("first_name", "")).strip()
        last_name = str(profile_data.get("last_name", "")).strip()

        combined = " ".join(part for part in (first_name, last_name) if part).strip()

        if combined:
            return combined

    return str(linkedin_evidence.get("display_name", "")).strip()


def repository_has_skill(
    skill: str,
    repository: dict,
) -> tuple[bool, list[str]]:
    if not isinstance(repository, dict):
        return False, []

    target = canonical_skill(skill)
    evidence_sources = []

    technologies = repository.get("technologies", [])
    if isinstance(technologies, list):
        for technology in technologies:
            if canonical_skill(technology) == target:
                evidence_sources.append("technology")
                break

    language = repository.get("language", "")
    if language and canonical_skill(language) == target:
        evidence_sources.append("language")

    languages = repository.get("languages", {})
    if isinstance(languages, dict):
        for language_name in languages.keys():
            if canonical_skill(language_name) == target:
                evidence_sources.append("languages")
                break

    return bool(evidence_sources), sorted(set(evidence_sources))


def map_skill_to_repositories(
    skill: str,
    repositories: list[dict],
) -> list[dict]:
    matches = []

    if not isinstance(repositories, list):
        return matches

    for repository in repositories:
        if not isinstance(repository, dict):
            continue

        matched, evidence_sources = repository_has_skill(skill, repository)
        if not matched:
            continue

        matches.append(
            {
                "repository": repository.get("name", ""),
                "matched_evidence": evidence_sources,
                "language": repository.get("language", ""),
                "technologies": repository.get("technologies", []),
                "languages": repository.get("languages", {}),
                "has_readme": bool(repository.get("has_readme", False)),
                "dependency_files": repository.get("dependency_files", {}),
            }
        )

    return matches


def build_repository_skill_mapping(
    claims: list[dict],
    github_evidence: dict,
) -> dict:
    repositories = github_evidence.get("repositories", [])

    if not isinstance(repositories, list):
        repositories = []

    mapping = {}

    for claim in claims:
        if not isinstance(claim, dict):
            continue

        if claim.get("type") != "skill":
            continue

        skill = str(claim.get("claim", "")).strip()
        if not skill:
            continue

        mapping[skill] = map_skill_to_repositories(skill, repositories)

    return mapping


def calculate_evidence_strength(
    claim: dict,
    repository_matches: list[dict],
    github_evidence: dict,
) -> dict:
    score = 0
    reasons = []

    evidence = claim.get("evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}

    if evidence.get("resume", True):
        score += 20
        reasons.append("Claim appears in the resume.")

    if not repository_matches:
        return {
            "score": score,
            "level": "Weak" if score > 0 else "None",
            "reasons": reasons,
        }

    score += 30
    reasons.append("Matching GitHub repository evidence was found.")

    technology_matches = sum(
        1
        for repository in repository_matches
        if "technology" in repository.get("matched_evidence", [])
    )

    if technology_matches > 0:
        score += 20
        reasons.append("The exact technology was found in repository metadata.")

    language_matches = sum(
        1
        for repository in repository_matches
        if (
            "language" in repository.get("matched_evidence", [])
            or "languages" in repository.get("matched_evidence", [])
        )
    )

    if language_matches > 0:
        score += 15
        reasons.append("Repository language supports the claim.")

    if len(repository_matches) >= 2:
        score += 10
        reasons.append("The claim is supported across multiple repositories.")

    if any(repository.get("has_readme", False) for repository in repository_matches):
        score += 5
        reasons.append("Supporting repository contains a README.")

    score = min(score, 100)

    if score >= 80:
        level = "Strong"
    elif score >= 60:
        level = "Moderate"
    elif score >= 20:
        level = "Weak"
    else:
        level = "None"

    return {"score": score, "level": level, "reasons": reasons}


def build_evidence_report(
    claims: list[dict],
    github_evidence: dict,
) -> list[dict]:
    repositories = github_evidence.get("repositories", [])
    if not isinstance(repositories, list):
        repositories = []

    report = []

    for claim in claims:
        if not isinstance(claim, dict):
            continue

        if claim.get("type") != "skill":
            continue

        claim_name = str(claim.get("claim", "")).strip()
        if not claim_name:
            continue

        repository_matches = map_skill_to_repositories(
            claim_name,
            repositories,
        )

        strength = calculate_evidence_strength(
            claim,
            repository_matches,
            github_evidence,
        )

        report.append(
            {
                "claim": claim_name,
                "type": "skill",
                "score": strength["score"],
                "level": strength["level"],
                "reasons": strength["reasons"],
                "github_repository_count": len(repository_matches),
                "github_repositories": [
                    item.get("repository", "") for item in repository_matches
                ],
            }
        )

    return report

def enrich_claims_with_github(
    claims: list,
    github_evidence: dict,
) -> list:
    """
    Enrich resume skill claims with GitHub evidence.

    This function ONLY collects and attaches GitHub evidence.
    Final claim verification is performed by the RAG verification layer.
    """

    if not isinstance(claims, list):
        return []

    if not isinstance(github_evidence, dict):
        github_evidence = {}

    repositories = github_evidence.get("repositories", [])
    if not isinstance(repositories, list):
        repositories = []

    technology_evidence = github_evidence.get(
        "technology_evidence",
        [],
    )
    if not isinstance(technology_evidence, list):
        technology_evidence = []

    github_found = bool(
        github_evidence.get("profile_found", False)
    )

    github_technologies = {
        canonical_skill(item)
        for item in technology_evidence
        if item
    }

    technology_aliases = {
        "python": {"python"},
        "javascript": {"javascript", "js"},
        "typescript": {"typescript", "ts"},
        "node.js": {"node.js", "node", "nodejs"},
        "react": {"react", "react.js", "reactjs"},
        "fastapi": {"fastapi"},
        "flask": {"flask"},
        "sql": {"sql", "sqlite", "mysql", "postgresql"},
        "postgresql": {"postgresql", "postgres", "pgvector"},
        "machine learning": {
            "machine learning",
            "scikit-learn",
            "pytorch",
            "tensorflow",
        },
        "artificial intelligence": {
            "artificial intelligence",
            "ai",
            "machine learning",
            "deep learning",
        },
        "data science": {
            "data science",
            "pandas",
            "numpy",
            "scikit-learn",
        },
        "git": {"git"},
        "github": {"github"},
        "google cloud": {
            "google cloud",
            "google-cloud",
            "gcp",
        },
        "rag": {
            "rag",
            "langchain",
            "llamaindex",
            "chromadb",
            "faiss",
            "qdrant",
            "pinecone",
            "pgvector",
        },
        "langchain": {
            "langchain",
            "langchain-community",
            "langchain-core",
            "langchain-openai",
            "langchain-google",
        },
        "jarvis": {
            "jarvis",
            "speechrecognition",
            "pyttsx3",
            "pyaudio",
            "vosk",
            "pygame",
        },
        "requests": {"requests"},
        "pygame": {"pygame"},
        "numpy": {"numpy"},
        "pandas": {"pandas"},
        "scikit-learn": {"scikit-learn"},
        "sqlalchemy": {"sqlalchemy"},
    }

    for claim in claims:

        if not isinstance(claim, dict):
            continue

        claim_text = str(
            claim.get("claim", "")
        ).strip()

        if not claim_text:
            continue

        evidence = claim.get("evidence", {})

        if not isinstance(evidence, dict):
            evidence = {}

        evidence.setdefault("resume", True)
        evidence.setdefault("linkedin", False)
        evidence.setdefault("github", False)

        claim_type = str(
            claim.get("type", "")
        ).strip().lower()

        if claim_type != "skill":
            claim["evidence"] = evidence
            continue

        claim_lower = canonical_skill(claim_text)

        aliases = technology_aliases.get(
            claim_lower,
            {claim_lower},
        )

        matched_technologies = []
        matched_repositories = []

        # Direct GitHub technology evidence
        for technology in github_technologies:
            if technology in {
                canonical_skill(alias)
                for alias in aliases
            }:
                matched_technologies.append(technology)

        # Repository evidence
        for repository in repositories:

            if not isinstance(repository, dict):
                continue

            repository_name = str(
                repository.get("name", "")
            ).strip()

            repository_description = str(
                repository.get("description", "") or ""
            ).strip()

            repository_technologies = repository.get(
                "technologies",
                [],
            )

            if not isinstance(repository_technologies, list):
                repository_technologies = []

            normalized_repository_technologies = {
                canonical_skill(item)
                for item in repository_technologies
                if item
            }

            alias_canonicals = {
                canonical_skill(alias)
                for alias in aliases
            }

            repository_match = bool(
                alias_canonicals.intersection(
                    normalized_repository_technologies
                )
            )

            searchable_text = normalize_text(
                " ".join(
                    [
                        repository_name,
                        repository_description,
                        " ".join(
                            normalized_repository_technologies
                        ),
                    ]
                )
            )

            claim_normalized = normalize_text(claim_text)

            if claim_normalized:
                pattern = (
                    rf"(?<![a-z0-9])"
                    rf"{re.escape(claim_normalized)}"
                    rf"(?![a-z0-9])"
                )

                if re.search(pattern, searchable_text):
                    repository_match = True

            if repository_match:
                matched_repositories.append(
                    {
                        "repository": repository_name,
                        "matched_evidence": [
                            claim_text
                        ],
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

        github_supported = bool(
            github_found
            and (
                matched_technologies
                or matched_repositories
            )
        )

        evidence["github"] = github_supported

        claim["github_repositories"] = [
            item.get("repository", "")
            for item in matched_repositories
        ]

        claim["github_evidence_sources"] = [
            {
                "type": "technology",
                "technology": technology,
            }
            for technology in matched_technologies
        ]

        claim["repository_matches"] = matched_repositories

        if github_supported:

            if (
                matched_technologies
                and matched_repositories
            ):
                evidence_score = 100
                evidence_level = "Strong"

                reasons = [
                    "GitHub contains matching technology evidence.",
                    "Matching repository evidence was found.",
                ]

            elif matched_repositories:
                evidence_score = 85
                evidence_level = "Strong"

                reasons = [
                    "Matching repository evidence was found on GitHub.",
                ]

            else:
                evidence_score = 75
                evidence_level = "Moderate"

                reasons = [
                    "GitHub contains matching technology evidence.",
                ]

            claim["github_evidence"] = {
                "source": "github",
                "verified": True,
                "technology": claim_text,
                "technologies": matched_technologies,
                "repositories": [
                    item.get("repository", "")
                    for item in matched_repositories
                ],
            }

        else:

            evidence_score = 20
            evidence_level = "Weak"

            reasons = [
                "No matching GitHub technology or repository evidence was found."
            ]

            claim.pop(
                "github_evidence",
                None,
            )

        claim["evidence_score"] = evidence_score
        claim["evidence_level"] = evidence_level
        claim["evidence_reasons"] = reasons
        claim["evidence"] = evidence

    return claims
def enrich_claims(
    claims: list,
    github_evidence: dict,
    linkedin_evidence: dict,
) -> list:

    claims = enrich_claims_with_github(
        claims,
        github_evidence,
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

    return claims


def verify_claims(
    claims: list,
    resume_text: str,
    github_evidence: dict,
    linkedin_evidence: dict,
) -> list:

    if not isinstance(claims, list):
        return []

    claims = enrich_claims(
        claims,
        github_evidence,
        linkedin_evidence,
    )

    for claim in claims:

        if not isinstance(claim, dict):
            continue

        claim_text = str(
            claim.get("claim", "")
        ).strip()

        if not claim_text:
            continue

        try:

            rag_result = verify_claim_with_rag(
                claim_text,
                resume_text,
                github_evidence,
                linkedin_evidence,
            )

            if isinstance(rag_result, dict):

                claim["rag_verification"] = rag_result

                # Normalize RAG fields for scoring
                rag_status = str(
                    rag_result.get(
                        "status",
                        rag_result.get(
                            "rag_status",
                            "",
                        ),
                    )
                ).strip().lower()

            claim["rag_status"] = rag_status

            claim["rag_confidence"] = rag_result.get(
                "confidence",
                rag_result.get(
                    "rag_confidence",
                    0,
                ),
            )

            if rag_status == "supported":
                claim["status"] = "supported"
            elif rag_status in {
                "partially_supported",
                "needs_review",
            }:
                claim["status"] = "needs_review"

            else:
                claim["rag_verification"] = rag_result

        except Exception as exc:

            print(
                "RAG verification error:",
                repr(exc),
            )

    return claims


async def verify_candidate(
    resume: UploadFile,
    github_url: str = "",
    linkedin_url: str = "",
    linkedin_result: str = "",
) -> CandidateReport:
    """
    Main PersonaDNA candidate verification pipeline.

    Flow:
    Resume
        ↓
    Claims + Skills
        ↓
    GitHub Evidence
        ↓
    LinkedIn Evidence
        ↓
    Identity Verification
        ↓
    RAG Claim Verification
        ↓
    Candidate Intelligence
        ↓
    Gemini Insight
        ↓
    Trust Score
        ↓
    CandidateReport
    """

    # ========================================================
    # 1. Validate resume
    # ========================================================

    if resume is None:
        raise HTTPException(
            status_code=400,
            detail="Resume file is required.",
        )

    try:
        resume_bytes = await resume.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to read resume file.",
        ) from exc

    if not resume_bytes:
        raise HTTPException(
            status_code=400,
            detail="Resume file is empty.",
        )

    # ========================================================
    # 2. Extract resume text
    # ========================================================

    try:
        reader = PdfReader(BytesIO(resume_bytes))

        resume_text_parts = []

        for page in reader.pages:
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            if text.strip():
                resume_text_parts.append(text)

        resume_text = "\n".join(resume_text_parts).strip()

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to extract text from resume PDF.",
        ) from exc

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in resume.",
        )

    # ========================================================
    # 3. Extract candidate name
    # ========================================================

    try:
        resume_name = extract_resume_name(resume_text)
    except Exception:
        resume_name = ""

    # ========================================================
    # 4. Extract claims
    # ========================================================

    try:
        claims = extract_claims(resume_text)
    except Exception as exc:
        print("Claim extraction error:", repr(exc))
        claims = []

    if not isinstance(claims, list):
        claims = []

    # ========================================================
    # 5. Extract skills
    # ========================================================

    skills = extract_skills(resume_text)

    # Add skills discovered from claims
    for claim in claims:
        if not isinstance(claim, dict):
            continue

        if str(claim.get("type", "")).strip().lower() != "skill":
            continue

        skill = str(
            claim.get("claim", "")
        ).strip()

        if skill and skill not in skills:
            skills.append(skill)

    # Remove duplicates
    skills = list(
        dict.fromkeys(
            str(skill).strip()
            for skill in skills
            if str(skill).strip()
        )
    )

    # ========================================================
    # 6. GitHub analysis
    # ========================================================

    github_url = clean_url(github_url)

    try:
        github_evidence = analyze_github(github_url)
    except Exception as exc:
        print("GitHub analysis error:", repr(exc))

        github_evidence = {
            "username": "",
            "profile_found": False,
            "repository_count": 0,
            "repositories": [],
            "technology_evidence": [],
            "evidence_status": "error",
        }

    if not isinstance(github_evidence, dict):
        github_evidence = {
            "username": "",
            "profile_found": False,
            "repository_count": 0,
            "repositories": [],
            "technology_evidence": [],
            "evidence_status": "error",
        }

    # ========================================================
    # 7. LinkedIn analysis
    # ========================================================

    linkedin_url = clean_url(linkedin_url)
    linkedin_profile = {}

    try:
        linkedin_profile = parse_linkedin_profile(
            linkedin_result
        )

        linkedin_evidence = analyze_linkedin_evidence(
            linkedin_url=linkedin_url,
            profile_data=linkedin_profile,
            consent_granted=bool(linkedin_profile),
        )
    except Exception as exc:
        print(
            "LinkedIn analysis error:",
            repr(exc),
        )
        linkedin_evidence = {}

    if not isinstance(linkedin_evidence, dict):
        linkedin_evidence = {}

    # ========================================================
    # 8. Identity verification
    # ========================================================

    linkedin_name = get_linkedin_name(
        linkedin_profile,
        linkedin_evidence,
    )

    try:
        identity_result = compare_identity(
            resume_name=resume_name,
            github=github_evidence.get("username", ""),
            linkedin=linkedin_name,
            github_display_name=github_evidence.get("display_name", ""),
        )
    except Exception as exc:
        print(
            "Identity comparison error:",
            repr(exc),
        )
        identity_result = {}

    if not isinstance(identity_result, dict):
        identity_result = {}

    # ========================================================
    # 9. Enrich + verify claims
    # ========================================================

    try:
        verified_claims = verify_claims(
            claims,
            resume_text,
            github_evidence,
            linkedin_evidence,
        )
    except Exception as exc:
        print(
            "Claim verification pipeline error:",
            repr(exc),
        )
        verified_claims = claims

    if not isinstance(verified_claims, list):
        verified_claims = []

    # ========================================================
    # 10. Build evidence report
    # ========================================================

    try:
        evidence_report = build_evidence_report(
            claims=verified_claims,
            github_evidence=github_evidence,
        )
    except Exception as exc:
        print(
            "Evidence report error:",
            repr(exc),
        )
        evidence_report = []

    if not isinstance(evidence_report, list):
        evidence_report = []
    # ========================================================
    # 10. Count verified claims
    # ========================================================

    verified_count = 0

    for claim in verified_claims:
        if not isinstance(claim, dict):
            continue

        rag_result = claim.get(
            "rag_verification",
            {},
        )

        if not isinstance(rag_result, dict):
            continue

        if rag_result.get("status") == "supported":
            verified_count += 1

    # ========================================================
    # 11. Build candidate intelligence
    # ========================================================

    try:
        candidate_intelligence = build_candidate_intelligence(
            claims=verified_claims,
            github_evidence=github_evidence,
            identity=identity_result,
            resume_text=resume_text,
        )
    except TypeError:
        try:
            candidate_intelligence = build_candidate_intelligence(
                verified_claims,
            )
        except Exception as exc:
            print(
                "Candidate intelligence error:",
                repr(exc),
            )
            candidate_intelligence = {}
    except Exception as exc:
        print(
            "Candidate intelligence error:",
            repr(exc),
        )
        candidate_intelligence = {}

    if not isinstance(candidate_intelligence, dict):
        candidate_intelligence = {}


        # ========================================================
    # 12. Build repository mappings
    # ========================================================

    skill_repository_mapping = (
        build_repository_skill_mapping(
            verified_claims,
            github_evidence,
        )
    )

    project_repository_mapping = (
        build_project_repository_mapping(
            verified_claims,
            github_evidence,
        )
    )

    # ========================================================
    # 12. Build candidate knowledge
    # ========================================================

    # ========================================================
    # 12. Build candidate knowledge
    # ========================================================

    try:
        candidate_knowledge = build_candidate_knowledge(
            resume_text=resume_text,
            claims=verified_claims,
            github_evidence=github_evidence,
            linkedin_evidence=linkedin_evidence,
            candidate_intelligence=candidate_intelligence,
            skill_repository_mapping=skill_repository_mapping,
            project_repository_mapping=project_repository_mapping,
            identity=identity_result,
        )
    except Exception as exc:
        print(
            "Candidate knowledge error:",
            repr(exc),
        )
        candidate_knowledge = ""

    if not isinstance(candidate_knowledge, str):
        candidate_knowledge = ""


    # ========================================================
    # 13. Gemini candidate insight
    # ========================================================

    try:
        candidate_insight = generate_candidate_insight(
            candidate_knowledge
        )
    except Exception as exc:
        print(
            "Gemini candidate insight error:",
            repr(exc),
        )
        candidate_insight = ""

    if not isinstance(candidate_insight, str):
        candidate_insight = str(
            candidate_insight or ""
        )
    # ========================================================
    # 14. Calculate trust score
    # ========================================================

    try:
        score_result = calculate_trust_score(
            identity=identity_result,
            github_evidence=github_evidence,
            claims=verified_claims,
            evidence_report=evidence_report,
            linkedin_evidence=linkedin_evidence,
        )
    except TypeError:
        try:
            score_result = calculate_trust_score(
                verified_claims,
                identity_result,
                github_evidence,
            )
        except Exception as exc:
            print(
                "Trust score calculation error:",
                repr(exc),
            )
            score_result = {}
    except Exception as exc:
        print(
            "Trust score calculation error:",
            repr(exc),
        )
        score_result = {}

    if not isinstance(score_result, dict):
        score_result = {}


    # ========================================================
    # 15. Extract score fields
    # ========================================================

    trust_score = int(
        score_result.get(
            "trust_score",
            0,
        ) or 0
    )

    ai_confidence = int(
        score_result.get(
            "ai_confidence",
            0,
        ) or 0
    )

    risk_level = str(
        score_result.get(
            "risk_level",
            "High",
        )
    )

    recruiter_verdict = str(
        score_result.get(
            "recruiter_verdict",
            "Manual verification is recommended.",
        )
    )


    # ========================================================
    # 16. Build candidate knowledge
    # ========================================================

    try:
        candidate_knowledge = build_candidate_knowledge(
            resume_text=resume_text,
            claims=verified_claims,
            github_evidence=github_evidence,
            linkedin_evidence=linkedin_evidence,
            candidate_intelligence=candidate_intelligence,
            skill_repository_mapping=skill_repository_mapping,
            project_repository_mapping=project_repository_mapping,
            identity=identity_result,
            trust_score=trust_score,
            ai_confidence=ai_confidence,
            risk_level=risk_level,
            recruiter_verdict=recruiter_verdict,
        )
    except Exception as exc:
        print(
            "Candidate knowledge error:",
            repr(exc),
        )
        candidate_knowledge = ""

    if not isinstance(candidate_knowledge, str):
        candidate_knowledge = ""


    # ========================================================
    # 17. Gemini candidate insight
    # ========================================================

    try:
        candidate_insight = generate_candidate_insight(
            candidate_knowledge
        )
    except Exception as exc:
        print(
            "Gemini candidate insight error:",
            repr(exc),
        )
        candidate_insight = ""

    if not isinstance(candidate_insight, str):
        candidate_insight = str(
            candidate_insight or ""
        ) # ========================================================
           # 16. Strengths
        # ========================================================

    strengths = []

    for claim in verified_claims:
        if not isinstance(claim, dict):
            continue

        evidence_level = str(
            claim.get(
                "evidence_level",
                "",
            )
        ).lower()

        claim_text = str(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        if (
            claim_text
            and evidence_level == "strong"
        ):
            strengths.append(
                claim_text
            )

    # ========================================================
    # 17. Warnings
    # ========================================================

    warnings = []

    for claim in verified_claims:
        if not isinstance(claim, dict):
            continue

        evidence_level = str(
            claim.get(
                "evidence_level",
                "",
            )
        ).lower()

        claim_text = str(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        if (
            claim_text
            and evidence_level in {
                "weak",
                "none",
            }
        ):
            warnings.append(
                f"Limited supporting evidence for {claim_text}."
            )

    if not github_evidence.get(
        "profile_found",
        False,
    ):
        warnings.append(
            "GitHub profile could not be verified."
        )

    # Remove duplicates
    strengths = list(
        dict.fromkeys(strengths)
    )

    warnings = list(
        dict.fromkeys(warnings)
    )
    claim_stats = {
        "detected": len(verified_claims),
        "supported": 0,
        "needs_review": 0,
        "unsupported": 0,
    }

    for claim in verified_claims:
        if not isinstance(claim, dict):
            continue

        status = str(
            claim.get("rag_status", "")
        ).strip().lower()

        if status == "supported":
            claim_stats["supported"] += 1
        elif status == "needs_review":
            claim_stats["needs_review"] += 1
        elif status == "unsupported":
            claim_stats["unsupported"] += 1


        # ========================================================
        # 18. Final CandidateReport
        # ========================================================

    return CandidateReport(
        trust_score=max(
            0,
            min(
                100,
                trust_score,
            ),
        ),
        ai_confidence=max(
            0,
            min(
                100,
                ai_confidence,
            ),
        ),
        verified_claims=verified_count,
        risk_level=risk_level,
        recruiter_verdict=recruiter_verdict,
        skills=skills,
        strengths=strengths,
        warnings=warnings,

        identity=identity_result,
        github_evidence=github_evidence,
        linkedin_evidence=linkedin_evidence,

        claims=verified_claims,
        claim_stats=claim_stats,
        candidate_insight=candidate_insight,
    )
