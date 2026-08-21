import { motion } from "framer-motion";
import { ArrowRight, PlayCircle } from "lucide-react";

const HeroContent = () => {
  return (
    <div className="relative z-10 mx-auto flex max-w-4xl flex-col items-center px-6 pt-40 text-center">
      <motion.div
        initial={{ opacity: 0, y: 25 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
      >
        <span className="rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-400">
          Powered by EvidenceAI™
        </span>

        <h1 className="mt-8 text-5xl font-extrabold leading-tight text-white md:text-7xl">
          Trust the
          <span className="block bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
            Evidence.
          </span>
          <span className="block">Not the Claims.</span>
        </h1>

        <p className="mx-auto mt-8 max-w-2xl text-lg leading-8 text-gray-400">
          PersonaDNA verifies professional identity using real evidence from
          GitHub, LinkedIn, projects, certificates, and resumes to build a
          trusted Digital DNA profile.
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <button className="flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-4 font-semibold text-white transition hover:bg-blue-500">
            Generate Digital DNA
            <ArrowRight size={18} />
          </button>

          <button className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-8 py-4 font-semibold text-gray-200 backdrop-blur-md transition hover:bg-white/10">
            <PlayCircle size={20} />
            Watch Demo
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default HeroContent;