import { motion } from "framer-motion";
import {
  CheckCircle2,
  Circle,
  Rocket,
} from "lucide-react";

const roadmap = [
  {
    phase: "Phase 1",
    title: "Verification Intelligence",
    status: "Current",
    items: [
      "Evidence Gap Intelligence",
      "Claim verification",
      "Evidence-backed Trust Score",
      "Candidate Intelligence",
    ],
  },
  {
    phase: "Phase 2",
    title: "Deep Technical Verification",
    status: "Next",
    items: [
      "Claim-to-Code Proof",
      "Skill Evolution Graph",
      "Evidence Timeline",
      "Evidence Freshness",
    ],
  },
  {
    phase: "Phase 3",
    title: "AI Recruiter Intelligence",
    status: "Planned",
    items: [
      "Verification Interview Generator",
      "Evidence-backed Recruiter Copilot",
      "Gemini intelligence",
      "Jarvis verification assistant",
    ],
  },
  {
    phase: "Phase 4",
    title: "Trust Infrastructure",
    status: "Future",
    items: [
      "Verification Action Center",
      "Candidate Trust Passport",
      "Continuous evidence verification",
      "Enterprise workflows",
    ],
  },
];

export default function Roadmap() {
  return (
    <section
      id="roadmap"
      className="scroll-mt-24 bg-[#09090B] py-28"
    >
      <div className="mx-auto max-w-7xl px-6">

        <div className="text-center">
          <p className="font-semibold uppercase tracking-[0.25em] text-blue-400">
            Roadmap
          </p>

          <h2 className="mt-4 text-4xl font-bold text-white md:text-5xl">
            From verification to
            <span className="text-blue-500"> trust infrastructure.</span>
          </h2>

          <p className="mx-auto mt-6 max-w-3xl text-lg leading-8 text-gray-400">
            PersonaDNA is evolving from candidate verification into a
            complete evidence-driven trust platform.
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-5xl space-y-6">
          {roadmap.map((phase, index) => (
            <motion.div
              key={phase.phase}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{
                duration: 0.5,
                delay: index * 0.1,
              }}
              className="relative rounded-2xl border border-white/10 bg-white/[0.03] p-7"
            >
              <div className="flex flex-col gap-6 md:flex-row">

                <div className="md:w-40">
                  <p className="text-sm font-semibold text-blue-400">
                    {phase.phase}
                  </p>

                  <div className="mt-2 flex items-center gap-2 text-sm text-gray-400">
                    {phase.status === "Current" ? (
                      <CheckCircle2 className="h-4 w-4 text-green-400" />
                    ) : phase.status === "Next" ? (
                      <Rocket className="h-4 w-4 text-blue-400" />
                    ) : (
                      <Circle className="h-4 w-4 text-gray-500" />
                    )}

                    {phase.status}
                  </div>
                </div>

                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-white">
                    {phase.title}
                  </h3>

                  <div className="mt-5 grid gap-3 sm:grid-cols-2">
                    {phase.items.map((item) => (
                      <div
                        key={item}
                        className="flex items-center gap-3 text-sm text-gray-400"
                      >
                        <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
                        {item}
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            </motion.div>
          ))}
        </div>

      </div>
    </section>
  );
}