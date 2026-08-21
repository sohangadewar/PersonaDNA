import {
  CheckCircle2,
  AlertTriangle,
  FileText,
  Globe,
  User,
} from "lucide-react";

import type { LucideIcon } from "lucide-react";
import type { CandidateReport, Claim } from "../../types/report";

interface ClaimEvidenceProps {
  report: CandidateReport;
}

/* -----------------------------------------
   Evidence Mark
----------------------------------------- */

function EvidenceMark({
  active,
  label,
  Icon,
}: {
  active: boolean;
  label: string;
  Icon: LucideIcon;
}) {
  return (
    <span
      className={`flex items-center gap-1.5 text-xs ${
        active ? "text-green-400" : "text-gray-500"
      }`}
    >
      {active ? (
        <CheckCircle2 size={14} />
      ) : (
        <AlertTriangle size={14} />
      )}

      <Icon size={13} />

      <span>{label}</span>
    </span>
  );
}

/* -----------------------------------------
   Status Badge
----------------------------------------- */

function StatusBadge({ claim }: { claim: Claim }) {
  if (claim.status === "supported") {
    return (
      <span className="rounded-full bg-green-500/10 px-3 py-1 text-xs font-semibold text-green-400">
        Supported
      </span>
    );
  }

  if (claim.status === "needs_review") {
    return (
      <span className="rounded-full bg-yellow-500/10 px-3 py-1 text-xs font-semibold text-yellow-400">
        Needs Review
      </span>
    );
  }

  return (
    <span className="rounded-full bg-blue-500/10 px-3 py-1 text-xs font-semibold text-blue-400">
      Detected
    </span>
  );
}

/* -----------------------------------------
   Claim Row
----------------------------------------- */

function ClaimRow({ claim }: { claim: Claim }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        
        {/* Claim information */}
        <div>
          <div className="flex items-center gap-3">
            <h3 className="font-semibold text-white">
              {claim.claim}
            </h3>

            <span className="rounded-full bg-white/5 px-2.5 py-1 text-[11px] uppercase tracking-wide text-gray-500">
              {claim.type}
            </span>
          </div>

          {/* Evidence sources */}
          <div className="mt-3 flex flex-wrap gap-4">

            <EvidenceMark
              active={claim.evidence.resume}
              label="Resume"
              Icon={FileText}
            />

            <EvidenceMark
              active={claim.evidence.github}
              label="GitHub"
              Icon={Globe}
            />

            <EvidenceMark
              active={claim.evidence.linkedin}
              label="LinkedIn"
              Icon={User}
            />

          </div>
        </div>

        {/* Status */}
        <StatusBadge claim={claim} />

      </div>
    </div>
  );
}

/* -----------------------------------------
   Main Component
----------------------------------------- */

export default function ClaimEvidence({
  report,
}: ClaimEvidenceProps) {

  const claims = report.claims.filter(
    (claim) => claim.type === "skill"
  );

  return (
    <div className="mt-8 rounded-3xl bg-[#111827] p-8">

      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">

        <div>
          <h2 className="text-2xl font-bold text-white">
            Claim Evidence
          </h2>

          <p className="mt-2 text-sm text-gray-400">
            Resume claims compared with available external evidence.
          </p>
        </div>

        {/* Claim statistics */}
        <div className="flex gap-3 text-xs text-gray-500">

          <span>
            Supported: {report.claim_stats.supported}
          </span>

          <span>
            Review: {report.claim_stats.needs_review}
          </span>

        </div>
      </div>

      {/* Claims */}
      <div className="mt-8 space-y-3">

        {claims.length > 0 ? (
          claims.map((claim) => (
            <ClaimRow
              key={`${claim.type}-${claim.claim}`}
              claim={claim}
            />
          ))
        ) : (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-center text-gray-400">
            No skill claims were detected.
          </div>
        )}

      </div>
    </div>
  );
}