import { motion } from "framer-motion";
import {
  ShieldCheck,
  SearchCheck,
  BrainCircuit,
  GitBranch,
  BarChart3,
  Fingerprint,
} from "lucide-react";

const features = [
  {
    icon: ShieldCheck,
    title: "Evidence-Based Verification",
    description:
      "Verify resume claims against real professional evidence instead of relying only on what candidates report.",
  },
  {
    icon: SearchCheck,
    title: "Evidence Gap Intelligence",
    description:
      "Identify claims that are missing sufficient evidence and highlight where manual verification is needed.",
  },
  {
    icon: BrainCircuit,
    title: "AI Candidate Intelligence",
    description:
      "Use AI reasoning to connect claims, evidence, skills, projects, and professional experience.",
  },
  {
    icon: GitBranch,
    title: "Claim-to-Code Proof",
    description:
      "Connect technical skills with relevant GitHub repositories and project evidence.",
  },
  {
    icon: BarChart3,
    title: "Trust Score",
    description:
      "Generate an evidence-backed trust score that helps recruiters understand candidate reliability.",
  },
  {
    icon: Fingerprint,
    title: "Digital DNA",
    description:
      "Transform verified candidate information into a structured professional trust profile.",
  },
];

export default function Features() {
  return (
    <section
      id="features"
      className="scroll-mt-24 bg-[#09090B] py-28"
    >
      <div className="mx-auto max-w-7xl px-6">

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mx-auto max-w-3xl text-center"
        >
          <p className="font-semibold uppercase tracking-[0.25em] text-blue-400">
            Features
          </p>

          <h2 className="mt-4 text-4xl font-bold text-white md:text-5xl">
            Verification built around
            <span className="text-blue-500"> real evidence.</span>
          </h2>

          <p className="mt-6 text-lg leading-8 text-gray-400">
            PersonaDNA connects candidate claims with professional evidence
            to create a deeper and more trustworthy candidate profile.
          </p>
        </motion.div>

        <div className="mt-16 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => {
            const Icon = feature.icon;

            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 25 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{
                  duration: 0.5,
                  delay: index * 0.08,
                }}
                className="group rounded-2xl border border-white/10 bg-white/[0.03] p-7 transition hover:border-blue-500/40 hover:bg-white/[0.05]"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600/15">
                  <Icon className="h-6 w-6 text-blue-400" />
                </div>

                <h3 className="mt-6 text-xl font-bold text-white">
                  {feature.title}
                </h3>

                <p className="mt-3 leading-7 text-gray-400">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}
        </div>

      </div>
    </section>
  );
}