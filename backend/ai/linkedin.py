from __future__ import annotations

from typing import Any


# ============================================================
# Helpers
# ============================================================

def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def clean_string(value: Any) -> str:
    return str(value or "").strip()


def clean_string_list(
    values: Any,
) -> list[str]:

    if not isinstance(values, list):
        return []

    result = []

    for value in values:
        text = clean_string(value)

        if text and text not in result:
            result.append(text)

    return result


def clean_object_list(
    values: Any,
) -> list[dict]:

    if not isinstance(values, list):
        return []

    return [
        value
        for value in values
        if isinstance(value, dict)
    ]


# ============================================================
# Empty / unavailable state
# ============================================================

def linkedin_unavailable(
    linkedin_url: str,
    reason: str,
) -> dict:

    return {
        "profile_found": False,
        "profile_data_available": False,
        "evidence_status": reason,
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


# ============================================================
# LinkedIn URL only
# ============================================================

def analyze_linkedin_url(
    linkedin_url: str,
) -> dict:
    """
    A LinkedIn URL by itself is NOT treated as evidence.

    It is only stored as a supplied profile reference.
    """

    if not linkedin_url:
        return linkedin_unavailable(
            "",
            "missing",
        )

    return linkedin_unavailable(
        linkedin_url,
        "url_only",
    )


# ============================================================
# Authorized LinkedIn data
# ============================================================

def analyze_linkedin_evidence(
    linkedin_url: str,
    profile_data: dict | None = None,
    consent_granted: bool = False,
) -> dict:
    """
    Analyze LinkedIn information obtained through an
    authorized integration.

    This function intentionally does NOT scrape LinkedIn.

    profile_data must come from an authorized LinkedIn API
    integration after member consent.
    """

    if not linkedin_url:
        return linkedin_unavailable(
            "",
            "missing",
        )

    if not consent_granted:
        return linkedin_unavailable(
            linkedin_url,
            "consent_required",
        )

    if not isinstance(profile_data, dict):
        return linkedin_unavailable(
            linkedin_url,
            "authorized_data_unavailable",
        )

    # --------------------------------------------------------
    # Basic profile
    # --------------------------------------------------------

    first_name = clean_string(
        profile_data.get(
            "first_name",
            "",
        )
    )

    last_name = clean_string(
        profile_data.get(
            "last_name",
            "",
        )
    )

    display_name = clean_string(
        profile_data.get(
            "name",
            "",
        )
    )

    if not display_name:
        display_name = " ".join(
            value
            for value in (
                first_name,
                last_name,
            )
            if value
        ).strip()

    headline = clean_string(
        profile_data.get(
            "headline",
            "",
        )
    )

    about = clean_string(
        profile_data.get(
            "about",
            "",
        )
    )

    # --------------------------------------------------------
    # Verification categories
    #
    # Example:
    # ["IDENTITY", "WORKPLACE"]
    # --------------------------------------------------------

    verification_categories = [
        str(value).strip().upper()
        for value in profile_data.get(
            "verification_categories",
            [],
        )
        if str(value).strip()
    ]

    # --------------------------------------------------------
    # Optional authorized fields
    #
    # These should only be populated when the connected
    # LinkedIn product actually returns them.
    # --------------------------------------------------------

    skills = clean_string_list(
        profile_data.get(
            "skills",
            [],
        )
    )

    experience = clean_object_list(
        profile_data.get(
            "experience",
            [],
        )
    )

    education = clean_object_list(
        profile_data.get(
            "education",
            [],
        )
    )

    certifications = clean_string_list(
        profile_data.get(
            "certifications",
            [],
        )
    )

    # --------------------------------------------------------
    # Evidence records
    # --------------------------------------------------------

    evidence = []

    if display_name:
        evidence.append(
            {
                "type": "identity",
                "field": "display_name",
                "value": display_name,
                "source": "linkedin_authorized_api",
            }
        )

    if "IDENTITY" in verification_categories:
        evidence.append(
            {
                "type": "verification",
                "field": "identity",
                "value": "IDENTITY",
                "source": "linkedin_verified_on_linkedin",
            }
        )

    if "WORKPLACE" in verification_categories:
        evidence.append(
            {
                "type": "verification",
                "field": "workplace",
                "value": "WORKPLACE",
                "source": "linkedin_verified_on_linkedin",
            }
        )

    if headline:
        evidence.append(
            {
                "type": "professional",
                "field": "headline",
                "value": headline,
                "source": "linkedin_authorized_api",
            }
        )

    if skills:
        evidence.append(
            {
                "type": "skills",
                "field": "skills",
                "value": skills,
                "source": "linkedin_authorized_api",
            }
        )

    if experience:
        evidence.append(
            {
                "type": "experience",
                "field": "experience",
                "value": experience,
                "source": "linkedin_authorized_api",
            }
        )

    if education:
        evidence.append(
            {
                "type": "education",
                "field": "education",
                "value": education,
                "source": "linkedin_authorized_api",
            }
        )

    if certifications:
        evidence.append(
            {
                "type": "certification",
                "field": "certifications",
                "value": certifications,
                "source": "linkedin_authorized_api",
            }
        )

    return {
        "profile_found": True,
        "profile_data_available": True,
        "evidence_status": (
            "verified_data_available"
            if evidence
            else "authorized_but_no_evidence"
        ),
        "profile_url": linkedin_url,
        "consent_granted": True,
        "authorized_source": True,

        "display_name": display_name,
        "headline": headline,
        "about": about,

        "verification_categories": (
            verification_categories
        ),

        "skills": skills,
        "experience": experience,
        "education": education,
        "certifications": certifications,

        "evidence": evidence,
    }


# ============================================================
# Skill evidence
# ============================================================

def linkedin_supports_skill(
    skill: str,
    linkedin_evidence: dict,
) -> bool:
    """
    LinkedIn skill evidence requires actual authorized data.

    A URL alone never returns True.
    """

    if not linkedin_evidence.get(
        "authorized_source",
        False,
    ):
        return False

    target = normalize_text(
        skill
    )

    for linkedin_skill in linkedin_evidence.get(
        "skills",
        [],
    ):

        if (
            normalize_text(
                linkedin_skill
            )
            == target
        ):
            return True

    return False


# ============================================================
# Experience evidence
# ============================================================

def linkedin_supports_experience(
    company: str,
    linkedin_evidence: dict,
) -> bool:

    if not linkedin_evidence.get(
        "authorized_source",
        False,
    ):
        return False

    target = normalize_text(
        company
    )

    for item in linkedin_evidence.get(
        "experience",
        [],
    ):

        if not isinstance(item, dict):
            continue

        company_name = normalize_text(
            item.get(
                "company",
                "",
            )
        )

        if (
            target
            and company_name
            and target == company_name
        ):
            return True

    return False


# ============================================================
# Education evidence
# ============================================================

def linkedin_supports_education(
    institution: str,
    linkedin_evidence: dict,
) -> bool:

    if not linkedin_evidence.get(
        "authorized_source",
        False,
    ):
        return False

    target = normalize_text(
        institution
    )

    for item in linkedin_evidence.get(
        "education",
        [],
    ):

        if not isinstance(item, dict):
            continue

        school = normalize_text(
            item.get(
                "school",
                "",
            )
        )

        if (
            target
            and school
            and target in school
        ):
            return True

    return False


# ============================================================
# Add LinkedIn evidence to claims
# ============================================================

def enrich_claims_with_linkedin(
    claims: list[dict],
    linkedin_evidence: dict,
) -> list[dict]:
    """
    Add LinkedIn evidence without changing the meaning
    of unsupported claims.

    No consent / no authorized API data:
        linkedin = False
    """

    for claim in claims:

        claim.setdefault(
            "evidence",
            {
                "resume": True,
                "github": False,
                "linkedin": False,
            },
        )

        claim_type = claim.get(
            "type",
            "",
        )

        # ----------------------------------------------------
        # Skills
        # ----------------------------------------------------

        if claim_type == "skill":

            claim[
                "evidence"
            ][
                "linkedin"
            ] = linkedin_supports_skill(
                str(
                    claim.get(
                        "claim",
                        "",
                    )
                ),
                linkedin_evidence,
            )

        # ----------------------------------------------------
        # Everything else remains unverified until
        # we have structured matching logic for that claim.
        # ----------------------------------------------------

        else:

            claim[
                "evidence"
            ].setdefault(
                "linkedin",
                False,
            )

    return claims


# ============================================================
# LinkedIn summary
# ============================================================

def build_linkedin_summary(
    linkedin_evidence: dict,
) -> dict:
    """
    Recruiter-friendly summary.

    This describes available evidence only.
    It does NOT approve or reject a candidate.
    """

    status = linkedin_evidence.get(
        "evidence_status",
        "unknown",
    )

    if status == "verified_data_available":

        message = (
            "Authorized LinkedIn evidence is available "
            "for review."
        )

    elif status == "url_only":

        message = (
            "A LinkedIn URL was supplied, but no LinkedIn "
            "evidence was retrieved. A URL alone is not treated "
            "as verification."
        )

    elif status == "consent_required":

        message = (
            "LinkedIn evidence requires the member to "
            "authorize the PersonaDNA integration."
        )

    elif status == "authorized_data_unavailable":

        message = (
            "LinkedIn authorization is expected, but no "
            "authorized profile data is currently available."
        )

    else:

        message = (
            "No LinkedIn evidence is currently available."
        )

    return {
        "status": status,
        
        
        
        
        "authorized": bool(
            linkedin_evidence.get(
                "authorized_source",
                False,
            )
        ),
        "message": message,
        "verification_categories": (
            linkedin_evidence.get(
                "verification_categories",
                [],
            )
        ),
    }