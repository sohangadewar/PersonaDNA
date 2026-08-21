import {
  ShieldCheck,
  BrainCircuit,
  AlertTriangle,
  BadgeCheck,
  FileSearch,
  Star,
} from "lucide-react";

import TrustGraph from "./TrustGraph";
import AIInsights from "./AIInsights";
import VerificationStatus from "./VerificationStatus";
import ClaimEvidence from "./ClaimEvidence";

import type { CandidateReport } from "../../types/report";

interface DashboardProps {
  report: CandidateReport;
}

export default function Dashboard({ report }: DashboardProps) {
  return (
    <div className="min-h-screen bg-[#09090B] px-8 py-10 text-white">

      {/* Header */}
      <div className="mb-12">
        <h1 className="text-5xl font-bold">
          🧬 Digital DNA Report
        </h1>

        <p className="mt-3 text-gray-400">
          AI Verified Candidate Profile
        </p>
      </div>

      {/* Top Cards */}
      <div className="grid gap-6 md:grid-cols-4">

        {/* Trust Score */}
        <div className="rounded-3xl bg-[#111827] p-6">
          <ShieldCheck
            className="text-green-400"
            size={35}
          />

          <h2 className="mt-4 text-4xl font-bold">
            {report.trust_score}%
          </h2>

          <p className="text-gray-400">
            Trust Score
          </p>
        </div>

        {/* Analysis Confidence */}
        <div className="rounded-3xl bg-[#111827] p-6">
          <BrainCircuit
            className="text-blue-400"
            size={35}
          />

          <h2 className="mt-4 text-4xl font-bold">
            {report.ai_confidence}%
          </h2>

          <p className="text-gray-400">
            Analysis Confidence
          </p>
        </div>

        {/* Verified Claims */}
        <div className="rounded-3xl bg-[#111827] p-6">
          <BadgeCheck
            className="text-cyan-400"
            size={35}
          />

          <h2 className="mt-4 text-4xl font-bold">
            {report.verified_claims}
          </h2>

          <p className="text-gray-400">
            Supported Claims
          </p>
        </div>

        {/* Risk */}
        <div className="rounded-3xl bg-[#111827] p-6">
          <AlertTriangle
            className="text-yellow-400"
            size={35}
          />

          <h2 className="mt-4 text-4xl font-bold">
            {report.risk_level}
          </h2>

          <p className="text-gray-400">
            Risk Level
          </p>
        </div>

      </div>

      {/* Evidence Summary + Skills */}
      <div className="mt-10 grid gap-8 lg:grid-cols-2">

        {/* Evidence Summary */}
        <div className="rounded-3xl bg-[#111827] p-8">

          <div className="flex items-center gap-3">
            <FileSearch />

            <h2 className="text-2xl font-bold">
              Evidence Summary
            </h2>
          </div>

          <ul className="mt-6 space-y-4 text-gray-300">

            {report.strengths.map((strength) => (
              <li key={strength}>
                <span className="mr-2 text-green-400">
                  ✓
                </span>

                {strength}
              </li>
            ))}

            {report.warnings.map((warning) => (
              <li key={warning}>
                <span className="mr-2 text-yellow-400">
                  ⚠
                </span>

                {warning}
              </li>
            ))}

          </ul>

        </div>

        {/* Skills */}
        <div className="rounded-3xl bg-[#111827] p-8">

          <div className="flex items-center gap-3">
            <Star />

            <h2 className="text-2xl font-bold">
              Top Skills
            </h2>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">

            {report.skills.map((skill) => (
              <div
                key={skill}
                className="rounded-full bg-blue-600 px-5 py-2"
              >
                {skill}
              </div>
            ))}

          </div>

        </div>

      </div>

      {/* Verification Status */}
      <VerificationStatus report={report} />

      {/* Claim Evidence */}
      <ClaimEvidence report={report} />

      {/* Trust Graph */}
      <TrustGraph report={report} />

      {/* AI Insights */}
      <div className="mt-8">
        <AIInsights report={report} />
      </div>

      {/* Recruiter Verdict */}
      <div className="mt-10 rounded-3xl border border-green-500/20 bg-green-500/10 p-8">

        <h2 className="text-3xl font-bold">
          ✅ Recruiter Verdict
        </h2>

        <p className="mt-4 text-lg text-gray-300">
          {report.recruiter_verdict}
        </p>

      </div>

    </div>
  );
}