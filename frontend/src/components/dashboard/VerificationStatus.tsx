import {
  FileText,
  Globe,
  User,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

import type { CandidateReport } from "../../types/report";

interface VerificationStatusProps {
  report: CandidateReport;
}

type Status = "verified" | "warning" | "mismatch";

function StatusBadge({ status }: { status: Status }) {
  if (status === "verified") {
    return (
      <span className="flex items-center gap-2 rounded-full bg-green-500/10 px-3 py-1 text-sm font-medium text-green-400">
        <CheckCircle2 size={16} />
        Verified
      </span>
    );
  }

  if (status === "mismatch") {
    return (
      <span className="flex items-center gap-2 rounded-full bg-red-500/10 px-3 py-1 text-sm font-medium text-red-400">
        <AlertTriangle size={16} />
        Mismatch
      </span>
    );
  }

  return (
    <span className="flex items-center gap-2 rounded-full bg-yellow-500/10 px-3 py-1 text-sm font-medium text-yellow-400">
      <AlertTriangle size={16} />
      Needs Review
    </span>
  );
}

export default function VerificationStatus({
  report,
}: VerificationStatusProps) {
  // ========================================================
  // GITHUB VERIFICATION
  // ========================================================

  const githubProfileFound = report.github_evidence?.profile_found === true;

  const githubIdentityMismatch =
    githubProfileFound && report.identity?.github_match === false;

  // ========================================================
  // LINKEDIN VERIFICATION
  // ========================================================

  const linkedinMismatch = report.warnings.some((warning) =>
    warning.toLowerCase().includes("linkedin identity"),
  );

  const linkedinVerified =
    report.identity?.linkedin_match === true ||
    report.linkedin_evidence?.authorized_source === true;

  return (
    <div className="mt-8 rounded-3xl bg-[#111827] p-8">
      {/* Header */}

      <div>
        <h2 className="text-2xl font-bold text-white">Verification Status</h2>

        <p className="mt-2 text-sm text-gray-400">
          Source-level verification signals used in the current analysis.
        </p>
      </div>

      {/* Verification Cards */}

      <div className="mt-8 grid gap-5 md:grid-cols-3">
        {/* ==================================================
            RESUME
        ================================================== */}

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <div className="flex items-center gap-3">
            <FileText className="text-blue-400" size={24} />

            <div>
              <h3 className="font-semibold text-white">Resume</h3>

              <p className="text-sm text-gray-500">PDF extraction</p>
            </div>
          </div>

          <div className="mt-5">
            <StatusBadge status="verified" />
          </div>
        </div>

        {/* ==================================================
            GITHUB
        ================================================== */}

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <div className="flex items-center gap-3">
            <Globe className="text-gray-300" size={24} />

            <div>
              <h3 className="font-semibold text-white">GitHub</h3>

              <p className="text-sm text-gray-500">Profile + repositories</p>
            </div>
          </div>

          <div className="mt-5">
            <StatusBadge
              status={
                githubIdentityMismatch
                  ? "mismatch"
                  : githubProfileFound
                    ? "verified"
                    : "warning"
              }
            />
          </div>
        </div>

        {/* ==================================================
            LINKEDIN
        ================================================== */}

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <div className="flex items-center gap-3">
            <User className="text-sky-400" size={24} />

            <div>
              <h3 className="font-semibold text-white">LinkedIn</h3>

              <p className="text-sm text-gray-500">Identity consistency</p>
            </div>
          </div>

          <div className="mt-5">
            <StatusBadge
              status={
                linkedinMismatch
                  ? "mismatch"
                  : linkedinVerified
                    ? "verified"
                    : "warning"
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
}
