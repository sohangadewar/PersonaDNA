import { motion } from "framer-motion";

const technologies = [
  {
    name: "React",
    category: "Frontend",
    description: "Interactive product interface",
  },
  {
    name: "TypeScript",
    category: "Frontend",
    description: "Type-safe application development",
  },
  {
    name: "Tailwind CSS",
    category: "Frontend",
    description: "Modern responsive UI styling",
  },
  {
    name: "FastAPI",
    category: "Backend",
    description: "High-performance API layer",
  },
  {
    name: "Python",
    category: "AI & Backend",
    description: "Verification and intelligence pipeline",
  },
  {
    name: "RAG",
    category: "AI",
    description: "Evidence-grounded verification",
  },
  {
    name: "Gemini",
    category: "AI",
    description: "Candidate intelligence and reasoning",
  },
  {
    name: "GitHub API",
    category: "Evidence",
    description: "Repository and project evidence",
  },
  {
    name: "LinkedIn",
    category: "Evidence",
    description: "Professional identity evidence",
  },
  {
    name: "PostgreSQL",
    category: "Data",
    description: "Structured application data",
  },
  {
    name: "OpenAI",
    category: "AI",
    description: "AI-powered application capabilities",
  },
  {
    name: "n8n",
    category: "Automation",
    description: "Workflow automation",
  },
];

export default function Technology() {
  return (
    <section
      id="technology"
      className="scroll-mt-24 bg-[#0B0B0F] py-28"
    >
      <div className="mx-auto max-w-7xl px-6">

        <div className="text-center">
          <p className="font-semibold uppercase tracking-[0.25em] text-blue-400">
            Technology
          </p>

          <h2 className="mt-4 text-4xl font-bold text-white md:text-5xl">
            Built with a modern
            <span className="text-blue-500"> AI stack.</span>
          </h2>

          <p className="mx-auto mt-6 max-w-3xl text-lg leading-8 text-gray-400">
            PersonaDNA combines modern web technologies, AI reasoning,
            retrieval, APIs, and automation to build an evidence-driven
            verification system.
          </p>
        </div>

        <div className="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {technologies.map((technology, index) => (
            <motion.div
              key={technology.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{
                duration: 0.4,
                delay: index * 0.05,
              }}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-6"
            >
              <p className="text-xs font-semibold uppercase tracking-wider text-blue-400">
                {technology.category}
              </p>

              <h3 className="mt-3 text-xl font-bold text-white">
                {technology.name}
              </h3>

              <p className="mt-2 text-sm leading-6 text-gray-400">
                {technology.description}
              </p>
            </motion.div>
          ))}
        </div>

      </div>
    </section>
  );
}