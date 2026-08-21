import {
  FileText,
  Globe,
  User,
  Award,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

import type { CandidateReport } from "../../types/report";

interface TrustGraphProps {
  report: CandidateReport;
}

type NodeStatus = "verified" | "warning" | "mismatch";

interface NodeData {
  title: string;
  subtitle: string;
  icon: typeof FileText;
  color: string;
  status: NodeStatus;
}

function getStatusStyles(status: NodeStatus) {
  switch (status) {
    case "verified":
      return {
        badge: "bg-green-500/10 text-green-400",
        icon: CheckCircle2,
        label: "Verified",
      };

    case "mismatch":
      return {
        badge: "bg-red-500/10 text-red-400",
        icon: AlertTriangle,
        label: "Mismatch",
      };

    default:
      return {
        badge: "bg-yellow-500/10 text-yellow-400",
        icon: AlertTriangle,
        label: "Needs Review",
      };
  }
}

export default function TrustGraph({
  report,
}: TrustGraphProps) {
  const githubMismatch = report.warnings.some((warning) =>
    warning.toLowerCase().includes("github identity")
  );

  const linkedinMismatch = report.warnings.some((warning) =>
    warning.toLowerCase().includes("linkedin identity")
  );

  const githubFound = report.strengths.some((strength) =>
    strength.toLowerCase().includes("github profile found")
  );

  const nodes: NodeData[] = [
    {
      title: "Resume",
      subtitle: "PDF extraction",
      icon: FileText,
      color: "bg-blue-600",
      status: "verified",
    },
    {
      title: "GitHub",
      subtitle: "Profile + repositories",
      icon: Globe,
      color: "bg-gray-700",
      status: githubMismatch
        ? "mismatch"
        : githubFound
          ? "verified"
          : "warning",
    },
    {
      title: "LinkedIn",
      subtitle: "Identity consistency",
      icon: User,
      color: "bg-sky-600",
      status: linkedinMismatch
        ? "mismatch"
        : "warning",
    },
    {
      title: "Certificates",
      subtitle: "Credential evidence",
      icon: Award,
      color: "bg-yellow-500",
      status: "warning",
    },
  ];

  return (
    <div className="mt-8 rounded-3xl bg-[#111827] p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">
            🕸 TrustGraph™
          </h2>

          <p className="mt-2 text-sm text-gray-400">
            Source-level evidence contributing to the trust assessment.
          </p>
        </div>

        <div className="rounded-full bg-green-500/10 px-4 py-2 text-sm font-semibold text-green-400">
          {report.trust_score}% Trust
        </div>
      </div>

      <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {nodes.map((node) => {
          const Icon = node.icon;
          const status = getStatusStyles(node.status);
          const StatusIcon = status.icon;

          return (
            <div
              key={node.title}
              className="rounded-2xl border border-white/10 bg-white/5 p-5"
            >
              <div className="flex flex-col items-center text-center">
                <div
                  className={`${node.color} flex h-16 w-16 items-center justify-center rounded-full shadow-lg`}
                >
                  <Icon
                    className="text-white"
                    size={30}
                  />
                </div>

                <h3 className="mt-4 font-semibold text-white">
                  {node.title}
                </h3>

                <p className="mt-1 text-xs text-gray-500">
                  {node.subtitle}
                </p>

                <span
                  className={`mt-4 flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${status.badge}`}
                >
                  <StatusIcon size={14} />
                  {status.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="relative mt-12 flex justify-center">
        <div className="absolute top-0 h-12 w-px bg-white/10" />

        <div className="relative flex h-32 w-32 items-center justify-center rounded-full border border-green-400/30 bg-green-500/10">
          <div className="absolute inset-2 rounded-full border border-green-400/20" />

          <div className="relative flex h-24 w-24 items-center justify-center rounded-full bg-green-600 shadow-xl">
            <ShieldCheck
              size={42}
              className="text-white"
            />
          </div>
        </div>
      </div>

      <div className="mt-8 text-center">
        <p className="text-sm uppercase tracking-widest text-gray-500">
          Overall Trust Score
        </p>

        <p className="mt-2 text-5xl font-bold text-white">
          {report.trust_score}%
        </p>

        <p className="mx-auto mt-3 max-w-2xl text-gray-400">
          The score summarizes the evidence signals currently available
          across the connected professional sources.
        </p>
      </div>
    </div>
  );
}