import { motion } from "framer-motion";
import { CheckCircle2, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

const steps = [
  "Uploading Resume...",
  "Extracting Claims...",
  "Analyzing GitHub...",
  "Verifying LinkedIn...",
  "Checking Certificates...",
  "Building TrustGraph™...",
  "Generating Digital DNA...",
];

interface ProcessingScreenProps {
  onComplete: () => void;
}

export default function ProcessingScreen({
  onComplete,
}: ProcessingScreenProps) {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (current >= steps.length - 1) {
      const timer = setTimeout(() => {
        onComplete();
      }, 500);

      return () => clearTimeout(timer);
    }

    const timer = setTimeout(() => {
      setCurrent((prev) => prev + 1);
    }, 350);

    return () => clearTimeout(timer);
  }, [current, onComplete]);

  return (
    <section className="flex min-h-screen items-center justify-center bg-[#09090B] px-6">
      <div className="w-full max-w-3xl rounded-3xl border border-white/10 bg-white/5 p-10 backdrop-blur-xl">

        <h1 className="text-center text-4xl font-bold text-white">
          EvidenceAI™ Verification
        </h1>

        <p className="mt-4 text-center text-gray-400">
          Please wait while we verify professional claims...
        </p>

        <div className="mt-12 space-y-4">

          {steps.map((step, index) => (
            <motion.div
              key={step}
              initial={{ opacity: 0, y: 10 }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              transition={{ duration: 0.3 }}
              className="flex items-center justify-between rounded-xl border border-white/10 bg-[#111827] px-6 py-4"
            >
              <span className="text-white">
                {step}
              </span>

              {index < current ? (
                <CheckCircle2
                  className="text-green-400"
                  size={24}
                />
              ) : index === current ? (
                <Loader2
                  className="animate-spin text-blue-400"
                  size={24}
                />
              ) : (
                <div className="h-6 w-6 rounded-full border border-gray-600" />
              )}
            </motion.div>
          ))}

        </div>

        <p className="mt-8 text-center text-sm text-gray-500">
          Building your Digital DNA profile...
        </p>

      </div>
    </section>
  );
}