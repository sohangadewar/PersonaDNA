import { motion } from "framer-motion";
import { ShieldCheck, GitBranch, FileCheck, Brain } from "lucide-react";

const stats = [
  {
    title: "Trust Score",
    value: "94%",
    icon: ShieldCheck,
    color: "text-green-400",
  },
  {
    title: "Evidence Sources",
    value: "5",
    icon: GitBranch,
    color: "text-blue-400",
  },
  {
    title: "Claims Verified",
    value: "16",
    icon: FileCheck,
    color: "text-purple-400",
  },
  {
    title: "AI Confidence",
    value: "98%",
    icon: Brain,
    color: "text-cyan-400",
  },
];

const HeroStats = () => {
  return (
    <div className="relative z-10 mx-auto mt-20 grid max-w-6xl grid-cols-1 gap-6 px-6 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat, index) => {
        const Icon = stat.icon;

        return (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.5,
              delay: index * 0.15,
            }}
            viewport={{ once: true }}
            className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
          >
            <div className="mb-4 flex items-center justify-between">
              <Icon className={`h-8 w-8 ${stat.color}`} />
            </div>

            <h3 className="text-3xl font-bold text-white">
              {stat.value}
            </h3>

            <p className="mt-2 text-sm text-gray-400">
              {stat.title}
            </p>
          </motion.div>
        );
      })}
    </div>
  );
};

export default HeroStats;