import { Upload, Globe, FileCheck, User } from "lucide-react";
import { useState } from "react";

import { api } from "../../services/api";
import type { CandidateReport } from "../../types/report";

interface UploadSectionProps {
  onGenerate: (data: CandidateReport) => void;
}

export default function UploadSection({
  onGenerate,
}: UploadSectionProps) {
  const [github, setGithub] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleResumeChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0] ?? null;
    setResumeFile(file);
  };

  const handleGenerate = async () => {
    if (!resumeFile) {
      alert("Please upload a resume before generating.");
      return;
    }

    if (!github.trim()) {
      alert("Please enter your GitHub profile URL.");
      return;
    }

    if (!linkedin.trim()) {
      alert("Please enter your LinkedIn profile URL.");
      return;
    }

    try {
      setIsGenerating(true);

      const formData = new FormData();

      formData.append("resume", resumeFile);
      formData.append("github", github);
      formData.append("linkedin", linkedin);

      const response = await api.post<CandidateReport>(
        "/analyze",
        formData
      );

      console.log("PersonaDNA Backend Response:", response.data);

      onGenerate(response.data);
    } catch (error) {
      console.error("PersonaDNA analysis failed:", error);

      alert(
        "Unable to analyze your profile. Please make sure the PersonaDNA backend is running."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <section className="bg-[#09090B] py-24">
      <div className="mx-auto max-w-5xl px-6">

        <div className="text-center">
          <p className="font-semibold uppercase tracking-widest text-blue-400">
            Verify Your Profile
          </p>

          <h2 className="mt-4 text-5xl font-bold text-white">
            Build Your Digital DNA
          </h2>

          <p className="mt-6 text-gray-400">
            Upload your resume and connect your professional profiles.
          </p>
        </div>

        <div className="mt-16 rounded-3xl border border-white/10 bg-white/5 p-10 backdrop-blur-xl">

          {/* Resume Upload */}
          <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-blue-500/40 p-12 transition hover:border-blue-400 hover:bg-blue-500/10">

            <Upload className="h-14 w-14 text-blue-400" />

            <h3 className="mt-4 text-2xl font-bold text-white">
              Upload Resume
            </h3>

            <p className="mt-2 text-gray-400">
              {resumeFile
                ? resumeFile.name
                : "Drag & Drop or Click to Upload PDF"}
            </p>

            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleResumeChange}
            />
          </label>

          {/* GitHub */}
          <div className="mt-10">
            <label className="mb-2 flex items-center gap-2 text-white">
              <Globe size={18} />
              GitHub Profile
            </label>

            <input
              type="url"
              value={github}
              onChange={(e) => setGithub(e.target.value)}
              placeholder="https://github.com/username"
              className="w-full rounded-xl border border-white/10 bg-[#111827] p-4 text-white outline-none focus:border-blue-500"
            />
          </div>

          {/* LinkedIn */}
          <div className="mt-8">
            <label className="mb-2 flex items-center gap-2 text-white">
              <User size={18} />
              LinkedIn Profile
            </label>

            <input
              type="url"
              value={linkedin}
              onChange={(e) => setLinkedin(e.target.value)}
              placeholder="https://linkedin.com/in/username"
              className="w-full rounded-xl border border-white/10 bg-[#111827] p-4 text-white outline-none focus:border-blue-500"
            />
          </div>

          {/* Generate */}
          <button
            type="button"
            onClick={handleGenerate}
            disabled={isGenerating}
            className="mt-10 flex w-full items-center justify-center gap-3 rounded-2xl bg-blue-600 py-4 text-lg font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <FileCheck />

            {isGenerating
              ? "Connecting to EvidenceAI..."
              : "Generate Digital DNA"}
          </button>

        </div>
      </div>
    </section>
  );
}