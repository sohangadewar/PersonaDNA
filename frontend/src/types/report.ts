export interface ClaimEvidence {
  resume: boolean;
  github: boolean;
  linkedin: boolean;
}

export interface Claim {
  claim: string;
  type: string;
  status: "detected" | "supported" | "needs_review";
  evidence: ClaimEvidence;
}

export interface ClaimStats {
  detected: number;
  supported: number;
  needs_review: number;
}

export interface IdentityReport {
  resume_name: string;
  github_username: string;
  linkedin_username: string;
  github_match: boolean;
  linkedin_match: boolean;
}

export interface GitHubRepository {
  name: string;
  language: string | null;
  stars: number;
  forks: number;
  updated_at: string | null;
}

export interface GitHubEvidence {
  username: string;
  profile_found: boolean;
  display_name: string | null;
  public_repositories: number;
  repository_count: number;
  repositories: GitHubRepository[];
  evidence_status: string;
}

export interface CandidateReport {
  trust_score: number;
  ai_confidence: number;
  verified_claims: number;
  risk_level: string;
  recruiter_verdict: string;

  skills: string[];
  strengths: string[];
  warnings: string[];

  claims: Claim[];
  claim_stats: ClaimStats;
  identity: IdentityReport;

  github_evidence: GitHubEvidence;

  linkedin_evidence?: {
    profile_found: boolean;
    profile_data_available: boolean;
    evidence_status: string;
    profile_url: string;
    consent_granted: boolean;
    authorized_source: boolean;
    display_name: string;
    headline: string;
    about: string;
    verification_categories: string[];
    skills: string[];
    experience: Record<string, unknown>[];
    education: Record<string, unknown>[];
    certifications: string[];
    evidence: Record<string, unknown>[];
  };

  linkedin_summary?: {
    status: string;
    authorized: boolean;
    message: string;
    verification_categories: string[];
  };

  evidence_report?: Record<string, unknown>[];

  risk_report?: Record<string, unknown>[];

  risk_summary?: {
    overall_risk: string;
    total_claims: number;
    low_risk_claims: number;
    medium_risk_claims: number;
    high_risk_claims: number;
  };

  skill_repository_mapping?: Record<string, unknown>[];

  project_repository_mapping?: Record<string, unknown>[];

  candidate_intelligence?: Record<string, unknown>;

  github?: string;
  linkedin?: string;

  resume_file_name?: string;
  resume_characters?: number;
  resume_preview?: string;
}