from io import BytesIO
import json
import re
import time
from typing import Any

from fastapi import UploadFile, HTTPException
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
# COMMON SKILLS
# ============================================================

COMMON_SKILLS = [

    # --------------------------------------------------------
    # Programming
    # --------------------------------------------------------

    "Python",
    "Java",
    "C++",
    "C",
    "JavaScript",
    "TypeScript",
    "Groovy",

    # --------------------------------------------------------
    # Frontend
    # --------------------------------------------------------

    "React",
    "ReactJS",
    "Redux",
    "HTML",
    "CSS",
    "Tailwind CSS",

    # --------------------------------------------------------
    # Backend
    # --------------------------------------------------------

    "Node.js",
    "NodeJS",
    "Express.js",
    "ExpressJS",
    "FastAPI",
    "Flask",
    "Django",
    "REST API",
    "REST",

    # --------------------------------------------------------
    # Databases
    # --------------------------------------------------------

    "SQL",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "Redis",

    # --------------------------------------------------------
    # AI / Data
    # --------------------------------------------------------

    "Artificial Intelligence",
    "AI",
    "Machine Learning",
    "Deep Learning",
    "Data Science",
    "Data Analysis",

    # --------------------------------------------------------
    # Computer Science
    # --------------------------------------------------------

    "Data Structures",
    "Algorithms",
    "Object Oriented Programming",
    "Operating Systems",
    "DBMS",
    "Computer Networks",
    "Competitive Programming",

    # --------------------------------------------------------
    # Tools / Cloud
    # --------------------------------------------------------

    "Git",
    "GitHub",
    "Docker",
    "AWS",
    "Google Cloud",

    # --------------------------------------------------------
    # PersonaDNA / AI stack
    # --------------------------------------------------------

    "RAG",
    "LangChain",
]


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: Any) -> str:
    """
    Normalize text for deterministic comparison.

    Examples:

        React.js       -> react
        ReactJS        -> react
        NodeJS         -> node.js
        Machine-Learning -> machine learning
        Scikit-Learn   -> scikit learn
    """

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

        "object-oriented programming":
            "object oriented programming",

        "artificial-intelligence":
            "artificial intelligence",

        "google cloud platform":
            "google cloud",

        "gcp":
            "google cloud",

        "postgres":
            "postgresql",
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
    Convert equivalent skill names into a single
    canonical representation.

    This prevents duplicate or inconsistent matching.

    Examples:

        ReactJS -> react
        React -> react

        REST -> rest api
        REST API -> rest api

        AI -> ai
        Artificial Intelligence -> ai

        GitHub -> git
        Git -> git

        GCP -> google cloud
        Google Cloud -> google cloud
    """

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

        "github": "git",
    }

    return aliases.get(
        normalized,
        normalized,
    )


# ============================================================
# SKILL DISPLAY NAME
# ============================================================

def get_display_skill(
    skill: str,
) -> str:
    """
    Return a clean human-readable skill name.
    """

    canonical = canonical_skill(skill)

    display_names = {
        "react": "React",
        "node.js": "Node.js",
        "express.js": "Express.js",
        "rest api": "REST API",
        "ai": "AI",
        "machine learning": "Machine Learning",
        "scikit-learn": "Scikit-Learn",
        "postgresql": "PostgreSQL",
        "google cloud": "Google Cloud",
        "git": "Git",
    }

    return display_names.get(
        canonical,
        str(skill).strip(),
    )


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(
    resume_text: str,
) -> list[str]:
    """
    Extract known skills explicitly mentioned
    in the resume.

    Duplicate aliases are normalized.

    Example:

        React
        ReactJS

    will be represented only once.
    """

    if not resume_text:
        return []

    normalized_resume = normalize_text(
        resume_text
    )

    found_skills = []
    seen_canonical = set()

    for skill in COMMON_SKILLS:

        normalized_skill = normalize_text(
            skill
        )

        canonical = canonical_skill(
            skill
        )

        if not normalized_skill:
            continue

        # Word-aware matching
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(normalized_skill)
            + r"(?![a-z0-9])"
        )

        if re.search(
            pattern,
            normalized_resume,
        ):

            if canonical not in seen_canonical:

                found_skills.append(
                    get_display_skill(skill)
                )

                seen_canonical.add(
                    canonical
                )

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

    return (
        str(value)
        .strip()
        .strip("`")
        .strip('"')
        .strip("'")
    )


# ============================================================
# LINKEDIN PROFILE PARSER
# ============================================================

def parse_linkedin_profile(
    linkedin_profile: str | None,
) -> dict | None:
    """
    Parse LinkedIn profile JSON when supplied directly.
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
    Get LinkedIn display name from authorized data.
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
# REPOSITORY SKILL EVIDENCE
# ============================================================

def repository_has_skill(
    skill: str,
    repository: dict,
) -> tuple[bool, list[str]]:
    """
    Determine whether a repository contains genuine
    evidence for a specific skill.

    Evidence sources:

        1. technologies
        2. primary language
        3. language statistics
    """

    if not isinstance(
        repository,
        dict,
    ):
        return False, []

    target = canonical_skill(
        skill
    )

    evidence_sources = []

    # --------------------------------------------------------
    # Technology evidence
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

            if (
                canonical_skill(
                    technology
                )
                == target
            ):

                evidence_sources.append(
                    "technology"
                )

                break

    # --------------------------------------------------------
    # Primary language
    # --------------------------------------------------------

    language = repository.get(
        "language",
        "",
    )

    if language:

        if (
            canonical_skill(
                language
            )
            == target
        ):

            evidence_sources.append(
                "language"
            )

    # --------------------------------------------------------
    # Language statistics
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

            if (
                canonical_skill(
                    language_name
                )
                == target
            ):

                evidence_sources.append(
                    "languages"
                )

                break

    evidence_sources = sorted(
        set(
            evidence_sources
        )
    )

    return (
        bool(evidence_sources),
        evidence_sources,
    )


# ============================================================
# SKILL → REPOSITORY MAPPING
# ============================================================

def map_skill_to_repositories(
    skill: str,
    repositories: list[dict],
) -> list[dict]:
    """
    Return only repositories that genuinely support
    the requested skill.
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

                "dependency_files": (
                    repository.get(
                        "dependency_files",
                        {},
                    )
                ),
            }
        )

    return matches


# ============================================================
# BUILD SKILL → REPOSITORY MAPPING
# ============================================================

def build_repository_skill_mapping(
    claims: list[dict],
    github_evidence: dict,
) -> dict:
    """
    Build a mapping:

        Skill
          ↓
        GitHub repositories
          ↓
        Evidence sources
    """

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
# AUTHORITATIVE EVIDENCE SCORE
# ============================================================

def calculate_evidence_strength(
    claim: dict,
    repository_matches: list[dict],
    github_evidence: dict,
) -> dict:
    """
    Authoritative evidence scoring model.

    Score:

        Resume evidence          = 20
        GitHub repository match  = 30
        Exact technology         = 20
        GitHub language          = 15
        Multiple repositories    = 10
        README evidence          = 5

        Maximum = 100
    """

    score = 0
    reasons = []

    evidence = claim.get(
        "evidence",
        {},
    )

    if not isinstance(
        evidence,
        dict,
    ):
        evidence = {}

    # --------------------------------------------------------
    # Resume
    # --------------------------------------------------------

    if evidence.get(
        "resume",
        True,
    ):

        score += 20

        reasons.append(
            "Claim appears in the resume."
        )

    # --------------------------------------------------------
    # No GitHub repository match
    # --------------------------------------------------------

    if not repository_matches:

        return {
            "score": score,
            "level": (
                "Weak"
                if score > 0
                else "None"
            ),
            "reasons": reasons,
        }

    # --------------------------------------------------------
    # GitHub repository evidence
    # --------------------------------------------------------

    score += 30

    reasons.append(
        "Matching GitHub repository evidence was found."
    )

    # --------------------------------------------------------
    # Exact technology
    # --------------------------------------------------------

    technology_matches = sum(
        1
        for repository
        in repository_matches
        if "technology"
        in repository.get(
            "matched_evidence",
            [],
        )
    )

    if technology_matches > 0:

        score += 20

        reasons.append(
            "The exact technology was found in repository metadata."
        )

    # --------------------------------------------------------
    # Language
    # --------------------------------------------------------

    language_matches = sum(
        1
        for repository
        in repository_matches
        if (
            "language"
            in repository.get(
                "matched_evidence",
                [],
            )
            or
            "languages"
            in repository.get(
                "matched_evidence",
                [],
            )
        )
    )

    if language_matches > 0:

        score += 15

        reasons.append(
            "Repository language supports the claim."
        )

    # --------------------------------------------------------
    # Multiple repositories
    # --------------------------------------------------------

    if len(
        repository_matches
    ) >= 2:

        score += 10

        reasons.append(
            "The claim is supported across multiple repositories."
        )

    # --------------------------------------------------------
    # README
    # --------------------------------------------------------

    if any(
        repository.get(
            "has_readme",
            False,
        )
        for repository
        in repository_matches
    ):

        score += 5

        reasons.append(
            "Supporting repository contains a README."
        )

    # --------------------------------------------------------
    # Clamp
    # --------------------------------------------------------

    score = min(
        score,
        100,
    )

    # --------------------------------------------------------
    # Level
    # --------------------------------------------------------

    if score >= 80:
        level = "Strong"

    elif score >= 60:
        level = "Moderate"

    elif score >= 20:
        level = "Weak"

    else:
        level = "None"

    return {
        "score": score,
        "level": level,
        "reasons": reasons,
    }


# ============================================================
# AUTHORITATIVE EVIDENCE REPORT
# ============================================================

def build_evidence_report(
    claims: list[dict],
    github_evidence: dict,
) -> list[dict]:
    """
    Build the authoritative evidence report.

    Every skill claim goes through the same matching
    and scoring pipeline.
    """

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if not isinstance(
        repositories,
        list,
    ):
        repositories = []

    report = []

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

        claim_name = str(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        if not claim_name:
            continue

        repository_matches = (
            map_skill_to_repositories(
                claim_name,
                repositories,
            )
        )

        strength = (
            calculate_evidence_strength(
                claim,
                repository_matches,
                github_evidence,
            )
        )

        report.append(
            {
                "claim": claim_name,

                "type": "skill",

                "score": strength[
                    "score"
                ],

                "level": strength[
                    "level"
                ],

                "reasons": strength[
                    "reasons"
                ],

                "github_repository_count": (
                    len(repository_matches)
                ),

                "github_repositories": [
                    item.get(
                        "repository",
                        "",
                    )
                    for item
                    in repository_matches
                ],
            }
        )

    return report


# ============================================================
# GITHUB CLAIM ENRICHMENT
# ============================================================

def enrich_claims_with_github(
    claims: list,
    github_evidence: dict,
) -> list:
    """
    Add authoritative GitHub evidence to claims.

    GitHub matching is performed against repository metadata,
    technology lists, and language information.

    It does NOT rely on simple substring matching between
    technology names and claim text.
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

        # ----------------------------------------------------
        # Ensure evidence object
        # ----------------------------------------------------

        evidence = claim.get(
            "evidence",
            {},
        )

        if not isinstance(
            evidence,
            dict,
        ):
            evidence = {}

        evidence.setdefault(
            "resume",
            True,
        )

        evidence.setdefault(
            "linkedin",
            False,
        )

        evidence.setdefault(
            "github",
            False,
        )

        # ----------------------------------------------------
        # Only skill claims use repository skill matching
        # ----------------------------------------------------

        if claim.get(
            "type"
        ) != "skill":

            claim[
                "evidence"
            ] = evidence

            continue

        skill = str(
            claim.get(
                "claim",
                "",
            )
        ).strip()

        if not skill:

            claim[
                "evidence"
            ] = evidence

            continue

        repository_matches = (
            map_skill_to_repositories(
                skill,
                repositories,
            )
        )

        github_match = bool(
            github_found
            and repository_matches
        )

        evidence[
            "github"
        ] = github_match

        # ----------------------------------------------------
        # Store repository evidence
        # ----------------------------------------------------

        claim[
            "github_repositories"
        ] = [
            item.get(
                "repository",
                "",
            )
            for item
            in repository_matches
        ]

        claim[
            "github_evidence_sources"
        ] = [
            item.get(
                "matched_evidence",
                [],
            )
            for item
            in repository_matches
        ]

        # ----------------------------------------------------
        # Calculate evidence strength
        # ----------------------------------------------------

        evidence_strength = (
            calculate_evidence_strength(
                claim,
                repository_matches,
                github_evidence,
            )
        )

        claim[
            "evidence_score"
        ] = evidence_strength[
            "score"
        ]

        claim[
            "evidence_level"
        ] = evidence_strength[
            "level"
        ]

        claim[
            "evidence_reasons"
        ] = evidence_strength[
            "reasons"
        ]

        claim[
            "repository_matches"
        ] = repository_matches

        claim[
            "evidence"
        ] = evidence

    return claims


# ============================================================
# CLAIM ENRICHMENT
# ============================================================

def enrich_claims(
    claims: list,
    github_evidence: dict,
    linkedin_evidence: dict,
) -> list:
    """
    Run all evidence enrichment layers.
    """

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


# ============================================================
# SAFE RAG VERIFICATION
# ============================================================

def verify_claims(
    claims: list,
    resume_text: str,
    github_evidence: dict,
    linkedin_evidence: dict,
) -> list:
    """
    Verify every extracted claim against available evidence.

    RAG interprets evidence.

    It does not manufacture external evidence.
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
        # Empty claim
        # ----------------------------------------------------

        if not claim_text:

            claim[
                "rag_status"
            ] = "needs_review"

            claim[
                "rag_confidence"
            ] = 0

            claim[
                "rag_evidence"
            ] = []

            claim[
                "rag_sources"
            ] = []

            claim[
                "status"
            ] = "needs_review"

            continue

        # ----------------------------------------------------
        # RAG VERIFICATION
        # ----------------------------------------------------

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

            rag_status = str(
                result.get(
                    "status",
                    "needs_review",
                )
            ).lower().strip()

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
            # Store RAG data
            # ------------------------------------------------

            claim[
                "rag_status"
            ] = rag_status

            claim[
                "rag_confidence"
            ] = rag_confidence

            rag_evidence = result.get(
                "evidence",
                [],
            )

            if not isinstance(
                rag_evidence,
                list,
            ):
                rag_evidence = []

            claim[
                "rag_evidence"
            ] = rag_evidence

            rag_sources = result.get(
                "sources",
                [],
            )

            if not isinstance(
                rag_sources,
                list,
            ):
                rag_sources = []

            claim[
                "rag_sources"
            ] = rag_sources

            # ------------------------------------------------
            # Normalize RAG status
            # ------------------------------------------------

            if rag_status == "supported":

                claim[
                    "status"
                ] = "supported"

            elif rag_status in (
                "partially_supported",
                "unsupported",
                "needs_review",
            ):

                claim[
                    "status"
                ] = "needs_review"

            else:

                claim[
                    "status"
                ] = "needs_review"

            # ------------------------------------------------
            # LinkedIn certification override
            # ------------------------------------------------

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

            if (
                claim_type == "certification"
                and evidence.get(
                    "linkedin",
                    False,
                )
            ):

                claim[
                    "status"
                ] = "supported"

                claim[
                    "rag_status"
                ] = "supported"

                claim[
                    "rag_confidence"
                ] = max(
                    claim.get(
                        "rag_confidence",
                        0,
                    ),
                    90,
                )

                if not isinstance(
                    claim.get(
                        "rag_evidence"
                    ),
                    list,
                ):

                    claim[
                        "rag_evidence"
                    ] = []

                certification_evidence = {
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
                    item.get(
                        "source"
                    )
                    for item
                    in claim[
                        "rag_evidence"
                    ]
                    if isinstance(
                        item,
                        dict,
                    )
                ]

                if (
                    "linkedin_authorized_api"
                    not in existing_sources
                ):

                    claim[
                        "rag_evidence"
                    ].append(
                        certification_evidence
                    )

                if not isinstance(
                    claim.get(
                        "rag_sources"
                    ),
                    list,
                ):

                    claim[
                        "rag_sources"
                    ] = []

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

            claim[
                "rag_status"
            ] = "needs_review"

            claim[
                "rag_confidence"
            ] = 0

            claim[
                "rag_evidence"
            ] = []

            claim[
                "rag_sources"
            ] = []

            claim[
                "status"
            ] = "needs_review"

        # ----------------------------------------------------
        # Per-claim timing
        # ----------------------------------------------------

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

def calculate_claim_stats(
    claims: list[dict],
) -> dict:
    """
    Calculate final claim statistics.

    The final 'status' field is the authoritative source.
    """

    if not isinstance(
        claims,
        list,
    ):
        claims = []

    supported = 0
    needs_review = 0

    for claim in claims:

        if not isinstance(
            claim,
            dict,
        ):
            continue

        status = str(
            claim.get(
                "status",
                "",
            )
        ).lower().strip()

        if status == "supported":

            supported += 1

        elif status in (
            "needs_review",
            "review",
        ):

            needs_review += 1

    return {
        "detected": len(claims),
        "supported": supported,
        "needs_review": needs_review,
    }


# ============================================================
# BUILD FINAL EVIDENCE REPORT
# ============================================================

def get_final_evidence_score(
    claims: list[dict],
) -> float:
    """
    Calculate the average evidence strength
    across claims.

    Only claims containing an evidence_score
    participate in this calculation.
    """

    scores = []

    for claim in claims:

        if not isinstance(
            claim,
            dict,
        ):
            continue

        score = claim.get(
            "evidence_score"
        )

        if score is None:
            continue

        try:

            score = float(
                score
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        scores.append(
            max(
                0,
                min(
                    score,
                    100,
                ),
            )
        )

    if not scores:
        return 0.0

    return (
        sum(scores)
        / len(scores)
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

    print(
        "DEBUG: verify_candidate STARTED"
    )

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

    if resume.content_type != "application/pdf":

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

        resume_text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                resume_text += page_text

            resume_text += "\n"

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

    resume_analysis_start = time.perf_counter()

    resume_name = extract_resume_name(
        resume_text
    )

    claims = extract_claims(
        resume_text
    )

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
        github_evidence.get(
            "profile_found",
            False,
        ),
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
        github_evidence.get(
            "repository_count",
            0,
        ),
    )

    print(
        "Technology evidence:",
        len(
            github_evidence.get(
                "technology_evidence",
                [],
            )
            if isinstance(
                github_evidence.get(
                    "technology_evidence",
                    [],
                ),
                list,
            )
            else []
        ),
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
                    profile_data=(
                        linkedin_profile_data
                    ),
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
        linkedin_evidence.get(
            "authorized_source",
            False,
        ),
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

    # --------------------------------------------------------
    # Important:
    # LinkedIn identity should only count when authorized
    # LinkedIn evidence is actually available.
    # --------------------------------------------------------

    linkedin_authorized = bool(
        linkedin_evidence.get(
            "authorized_source",
            False,
        )
        and linkedin_profile_data
    )

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

    print(
        "LinkedIn authorized:",
        linkedin_authorized,
    )

    # ========================================================
    # 9. ENRICH CLAIMS
    # ========================================================

    enrichment_start = time.perf_counter()

    try:

        claims = enrich_claims(
            claims=claims,
            github_evidence=github_evidence,
            linkedin_evidence=linkedin_evidence,
        )

    except Exception as exc:

        print(
            "Claim enrichment error:",
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
    # 10.5. BUILD EVIDENCE REPORT
    # ========================================================

    evidence_report = (
        build_evidence_report(
            claims=claims,
            github_evidence=github_evidence,
        )
    )

    # ========================================================
    # DEBUG: FINAL CLAIM VERIFICATION
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
            "Evidence score:",
            claim.get(
                "evidence_score"
            ),
        )

        print(
            "Evidence level:",
            claim.get(
                "evidence_level"
            ),
        )

        print(
            "GitHub repositories:",
            claim.get(
                "github_repositories"
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
    # 10.6. CANDIDATE INTELLIGENCE
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
    # 11. CLAIM STATISTICS
    # ========================================================

    claim_stats = calculate_claim_stats(
        claims
    )

    total_claims = (
        claim_stats[
            "detected"
        ]
    )

    verified_claims = (
        claim_stats[
            "supported"
        ]
    )

    needs_review_claims = (
        claim_stats[
            "needs_review"
        ]
    )

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
        needs_review_claims,
    )

    # ========================================================
    # 12. GITHUB REPOSITORIES
    # ========================================================

    repositories = github_evidence.get(
        "repositories",
        [],
    )

    if not isinstance(
        repositories,
        list,
    ):
        repositories = []

    repository_count = github_evidence.get(
        "repository_count",
        len(repositories),
    )

    try:

        repository_count = int(
            repository_count or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        repository_count = len(
            repositories
        )

    # ========================================================
    # 13. EVIDENCE QUALITY
    # ========================================================

    average_evidence_score = (
        get_final_evidence_score(
            claims
        )
    )

    print()
    print(
        "========== EVIDENCE QUALITY =========="
    )

    print(
        "Average evidence score:",
        round(
            average_evidence_score,
            2,
        ),
    )

    # ========================================================
    # 14. TRUST SCORE
    # ========================================================

    """
    Trust Score model:

        Claim verification  = 60%
        GitHub identity      = 15%
        LinkedIn identity    = 15%
        GitHub activity      = 10%

    This prevents identity alone from creating
    an artificially high trust score.
    """

    score = 0

    # --------------------------------------------------------
    # Claim verification = 60
    # --------------------------------------------------------

    if total_claims > 0:

        claim_ratio = (
            verified_claims
            / total_claims
        )

        score += int(
            claim_ratio * 60
        )

    # --------------------------------------------------------
    # GitHub identity = 15
    # --------------------------------------------------------

    if github_match:

        score += 15

    # --------------------------------------------------------
    # LinkedIn identity = 15
    # --------------------------------------------------------

    if linkedin_match:

        score += 15

    # --------------------------------------------------------
    # GitHub activity = 10
    # --------------------------------------------------------

    if (
        github_evidence.get(
            "profile_found",
            False,
        )
        and repository_count > 0
    ):

        score += 10

    # --------------------------------------------------------
    # Evidence quality adjustment
    # --------------------------------------------------------

    if average_evidence_score > 0:

        # Evidence quality acts as a safety cap.
        #
        # It does not blindly add points.
        #
        # This prevents weak evidence from producing
        # an excessively high trust score.

        if (
            average_evidence_score < 30
            and score > 40
        ):

            score = min(
                score,
                40,
            )

        elif (
            average_evidence_score < 50
            and score > 60
        ):

            score = min(
                score,
                60,
            )

    score = max(
        0,
        min(
            score,
            100,
        ),
    )

    # ========================================================
    # 15. AI CONFIDENCE
    # ========================================================

    confidence_components = []

    # Claim verification confidence
    if total_claims > 0:

        claim_verification_confidence = (
            verified_claims
            / total_claims
        ) * 100

        confidence_components.append(
            claim_verification_confidence
        )

    # Evidence quality
    if average_evidence_score > 0:

        confidence_components.append(
            average_evidence_score
        )

    # GitHub profile
    if github_evidence.get(
        "profile_found",
        False,
    ):

        confidence_components.append(
            90
        )

    # GitHub identity
    if github_match:

        confidence_components.append(
            95
        )

    # LinkedIn identity
    if linkedin_match:

        confidence_components.append(
            95
        )

    if confidence_components:

        ai_confidence = int(
            sum(
                confidence_components
            )
            / len(
                confidence_components
            )
        )

    else:

        ai_confidence = 50

    ai_confidence = max(
        0,
        min(
            ai_confidence,
            100,
        ),
    )

    # ========================================================
    # 16. RISK LEVEL
    # ========================================================

    if score >= 80:

        risk_level = "Low"

    elif score >= 60:

        risk_level = "Medium"

    else:

        risk_level = "High"

    # ========================================================
    # 17. WARNINGS
    # ========================================================

    warnings = []

    # --------------------------------------------------------
    # GitHub
    # --------------------------------------------------------

    if not github_url:

        warnings.append(
            "GitHub profile was not provided."
        )

    elif not github_evidence.get(
        "profile_found",
        False,
    ):

        warnings.append(
            "GitHub profile could not be verified."
        )

    # --------------------------------------------------------
    # Claims
    # --------------------------------------------------------

    if total_claims == 0:

        warnings.append(
            "No verifiable claims were extracted "
            "from the resume."
        )

    elif needs_review_claims > 0:

        warnings.append(
            f"{needs_review_claims} "
            "resume claim(s) need further verification."
        )

    # --------------------------------------------------------
    # LinkedIn
    # --------------------------------------------------------

    if linkedin_url and not linkedin_match:

        if linkedin_authorized:

            warnings.append(
                "LinkedIn identity could not be confirmed."
            )

        else:

            warnings.append(
                "LinkedIn identity could not be verified "
                "because authorized profile evidence was unavailable."
            )

    # --------------------------------------------------------
    # Suspicious claims
    # --------------------------------------------------------

    suspicious_count = (
        candidate_intelligence.get(
            "suspicious_claim_count",
            0,
        )
    )

    try:

        suspicious_count = int(
            suspicious_count or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        suspicious_count = 0

    if suspicious_count > 0:

        warnings.append(
            f"{suspicious_count} suspicious claim(s) "
            "require additional review."
        )

    # --------------------------------------------------------
    # Evidence quality
    # --------------------------------------------------------

    if (
        average_evidence_score > 0
        and average_evidence_score < 40
    ):

        warnings.append(
            "Overall external evidence strength is limited."
        )

    if not warnings:

        warnings.append(
            "No major verification risks detected."
        )

    # ========================================================
    # 18. STRENGTHS
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

    if average_evidence_score >= 70:

        strengths.append(
            "Overall external evidence strength is strong."
        )

    if not strengths:

        strengths.append(
            "Candidate profile was successfully processed."
        )

    # ========================================================
    # 19. RECRUITER VERDICT
    # ========================================================

    if score >= 80:

        recruiter_verdict = (
            "Recommended for Technical Interview"
        )

    elif score >= 60:

        recruiter_verdict = (
            "Consider for Technical Interview "
            "after further verification"
        )

    else:

        recruiter_verdict = (
            "Further Verification Recommended"
        )

    # ========================================================
    # 20. BUILD SKILL REPOSITORY MAPPING
    # ========================================================

    try:

        skill_repository_mapping = (
            build_repository_skill_mapping(
                claims=claims,
                github_evidence=github_evidence,
            )
        )

    except Exception as exc:

        print(
            "Skill repository mapping error:",
            repr(exc),
        )

        skill_repository_mapping = {}

    # ========================================================
    # 21. BUILD CANDIDATE KNOWLEDGE
    # ========================================================

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

    # ========================================================
    # 22. GEMINI INSIGHT
    # ========================================================

    try:

        candidate_insight = (
            generate_candidate_insight(
                candidate_knowledge
            )
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

    pipeline_time = (
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
        "Total claims:",
        total_claims,
    )

    print(
        "Needs review:",
        needs_review_claims,
    )

    print(
        "Average evidence score:",
        round(
            average_evidence_score,
            2,
        ),
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
        "GitHub identity:",
        github_match,
    )

    print(
        "LinkedIn identity:",
        linkedin_match,
    )

    print(
        "Repositories:",
        repository_count,
    )

    print(
        "Gemini insight:",
        bool(
            report.candidate_insight
        ),
    )

    print(
        f"TOTAL PIPELINE TIME: "
        f"{pipeline_time:.2f}s"
    )

    print(
        "======================================="
    )

    return report