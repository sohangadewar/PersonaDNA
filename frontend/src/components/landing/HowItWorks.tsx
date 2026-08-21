import { motion } from "framer-motion";
import {
  FileText,
  Search,
  ShieldCheck,
  BrainCircuit,
  BadgeCheck,
} from "lucide-react";

const steps = [
  {
    icon: FileText,
    title: "Upload Resume",
    description: "Upload your resume along with GitHub, LinkedIn, and certificates.",
  },
  {
    icon: Search,
    title: "Evidence Collection",
    description: "EvidenceAI gathers publicly available evidence from trusted sources.",
  },
  {
    icon: BrainCircuit,
    title: "AI Verification",
    description: "Claims are matched against repositories, projects, certificates, and experience.",
  },
  {
    icon: ShieldCheck,
    title: "TrustGraph™",
    description: "Relationships between skills, projects, and achievements are analyzed.",
  },
  {
    icon: BadgeCheck,
    title: "Digital DNA",
    description: "A complete trust profile with verification score and recruiter insights is generated.",
  },
];

export default function HowItWorks() {
  return (
    <section className="bg-[#09090B] py-28">
      <div className="mx-auto max-w-7xl px-6">

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: .6 }}
          className="text-center"
        >
          <p className="font-semibold uppercase tracking-widest text-blue-400">
            How It Works
          </p>

          <h2 className="mt-4 text-5xl font-bold text-white">
            From Resume to
            <span className="text-blue-500"> Digital Trust</span>
          </h2>

          <p className="mx-auto mt-6 max-w-3xl text-lg text-gray-400">
            PersonaDNA verifies professional identity through a five-step AI-powered verification pipeline.
          </p>
        </motion.div>

        <div className="relative mt-24">

          <div className="absolute left-0 right-0 top-16 hidden h-1 bg-gradient-to-r from-blue-500 via-cyan-400 to-green-400 lg:block" />

          <div className="grid gap-10 lg:grid-cols-5">

            {steps.map((step, index) => {

              const Icon = step.icon;

              return (

                <motion.div
                  key={step.title}
                  initial={{ opacity:0, y:40 }}
                  whileInView={{ opacity:1, y:0 }}
                  transition={{ delay:index*0.15 }}
                  viewport={{ once:true }}
                  className="relative"
                >

                  <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-blue-600 shadow-xl shadow-blue-600/30">

                    <Icon className="h-10 w-10 text-white"/>

                  </div>

                  <div className="mt-8 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">

                    <h3 className="text-xl font-bold text-white">
                      {step.title}
                    </h3>

                    <p className="mt-3 leading-7 text-gray-400">
                      {step.description}
                    </p>

                  </div>

                </motion.div>

              )

            })}

          </div>

        </div>

      </div>
    </section>
  );
}