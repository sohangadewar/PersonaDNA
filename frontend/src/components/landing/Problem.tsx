import { motion } from "framer-motion";
import {
  FileWarning,
  BadgeCheck,
  ShieldAlert,
} from "lucide-react";

const problems = [
  {
    icon: FileWarning,
    title: "Fake Resumes",
    description:
      "Anyone can generate professional resumes using AI in minutes, making it difficult for recruiters to verify real skills.",
  },
  {
    icon: BadgeCheck,
    title: "Unverified Profiles",
    description:
      "GitHub, LinkedIn and portfolios often contain exaggerated claims without proof or measurable evidence.",
  },
  {
    icon: ShieldAlert,
    title: "Hiring Risk",
    description:
      "Recruiters spend countless hours verifying candidates manually, increasing hiring costs and mistakes.",
  },
];

const Problem = () => {
  return (
    <section className="bg-[#09090B] py-28 px-6">
      <div className="mx-auto max-w-7xl">

        <motion.div
          initial={{ opacity: 0, y: 25 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <p className="text-blue-400 font-semibold uppercase tracking-widest">
            The Problem
          </p>

          <h2 className="mt-4 text-5xl font-bold text-white">
            The Internet Has a
            <span className="text-blue-500"> Trust Problem</span>
          </h2>

          <p className="mx-auto mt-6 max-w-3xl text-lg text-gray-400">
            Traditional hiring relies on documents and self-declared claims.
            PersonaDNA verifies credibility using real digital evidence instead
            of assumptions.
          </p>
        </motion.div>

        <div className="mt-20 grid gap-8 md:grid-cols-3">
          {problems.map((problem, index) => {
            const Icon = problem.icon;

            return (
              <motion.div
                key={problem.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.5,
                  delay: index * 0.2,
                }}
                viewport={{ once: true }}
                className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl transition hover:border-blue-500/40 hover:bg-white/10"
              >
                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600/20">
                  <Icon className="h-7 w-7 text-blue-400" />
                </div>

                <h3 className="text-2xl font-semibold text-white">
                  {problem.title}
                </h3>

                <p className="mt-4 leading-7 text-gray-400">
                  {problem.description}
                </p>
              </motion.div>
            );
          })}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          viewport={{ once: true }}
          className="mt-20 rounded-3xl border border-red-500/20 bg-red-500/10 p-8 text-center"
        >
          <h3 className="text-3xl font-bold text-white">
            Every incorrect hiring decision costs companies time, money, and trust.
          </h3>

          <p className="mt-4 text-lg text-gray-300">
            PersonaDNA replaces blind trust with AI-powered evidence verification.
          </p>
        </motion.div>

      </div>
    </section>
  );
};

export default Problem;