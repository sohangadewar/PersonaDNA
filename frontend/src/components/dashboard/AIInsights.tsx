import {
  BrainCircuit,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

import type { CandidateReport } from "../../types/report";

interface AIInsightsProps {
  report: CandidateReport;
}

export default function AIInsights({
  report,
}: AIInsightsProps) {
  return (
    <div className="rounded-3xl bg-[#111827] p-8">

      {/* Header */}

      <div className="mb-8 flex items-center gap-3">
        <BrainCircuit className="text-blue-400" />

        <div>
          <h2 className="text-2xl font-bold text-white">
            AI Insights
          </h2>

          <p className="mt-1 text-sm text-gray-400">
            Evidence-based analysis of your professional profile.
          </p>
        </div>
      </div>

      {/* Positive Insights */}

      <div className="space-y-4">

        {report.strengths.map((item) => (
          <div
            key={item}
            className="flex items-start gap-3 rounded-xl bg-green-500/10 p-4"
          >
            <CheckCircle2
              className="mt-1 shrink-0 text-green-400"
              size={20}
            />

            <p className="text-gray-200">
              {item}
            </p>
          </div>
        ))}

        {/* Warnings */}

        {report.warnings.map((item) => (
          <div
            key={item}
            className="flex items-start gap-3 rounded-xl bg-yellow-500/10 p-4"
          >
            <AlertTriangle
              className="mt-1 shrink-0 text-yellow-400"
              size={20}
            />

            <p className="text-gray-200">
              {item}
            </p>
          </div>
        ))}

      </div>

      {/* AI Confidence */}

      <div className="mt-8 rounded-2xl border border-blue-500/20 bg-blue-500/10 p-5">

        <div className="flex items-center justify-between">

          <span className="text-gray-300">
            AI Confidence
          </span>

          <span className="font-bold text-blue-400">
            {report.ai_confidence}%
          </span>

        </div>

        <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">

          <div
            className="h-full rounded-full bg-blue-500 transition-all duration-700"
            style={{
              width: `${report.ai_confidence}%`,
            }}
          />

        </div>

      </div>

    </div>
  );
}