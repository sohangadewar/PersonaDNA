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
}