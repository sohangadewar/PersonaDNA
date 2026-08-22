import {
  Upload,
  Globe,
  FileCheck,
  User,
  CheckCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../../services/api";
import type { CandidateReport } from "../../types/report";

interface LinkedInProfile {
  id?: string;
  first_name?: string;
  last_name?: string;
  name?: string;
  email?: string;
  profile_picture?: string;
}

interface UploadSectionProps {
  onGenerate: (data: CandidateReport) => void;
}

export default function UploadSection({
  onGenerate,
}: UploadSectionProps) {
  const [github, setGithub] = useState("");
  const [linkedinProfile, setLinkedinProfile] =
    useState<LinkedInProfile | null>(null);

  const [resumeFile, setResumeFile] =
    useState<File | null>(null);

  const [isGenerating, setIsGenerating] =
    useState(false);

  // ============================================================
  // READ LINKEDIN RESULT AFTER OAUTH REDIRECT
  // ============================================================

  useEffect(() => {
    const loadLinkedInResult = async () => {
      const params = new URLSearchParams(
        window.location.search
      );

      const resultCode =
        params.get("linkedin_result");

      if (!resultCode) {
        return;
      }

      try {
        const response = await api.get(
          "/linkedin/result",
          {
            params: {
              code: resultCode,
            },
          }
        );

        console.log(
          "LinkedIn profile received:",
          response.data
        );

        if (response.data?.linkedin) {
          setLinkedinProfile(
            response.data.linkedin
          );
        }

        // Remove linkedin_result from browser URL
        window.history.replaceState(
          {},
          document.title,
          window.location.pathname
        );
      } catch (error) {
        console.error(
          "Failed to retrieve LinkedIn profile:",
          error
        );

        alert(
          "LinkedIn connection could not be completed."
        );
      }
    };

    loadLinkedInResult();
  }, []);

  // ============================================================
  // RESUME
  // ============================================================

  const handleResumeChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file =
      e.target.files?.[0] ?? null;

    setResumeFile(file);
  };

  // ============================================================
  // LINKEDIN CONNECT
  // ============================================================

  const connectLinkedIn = () => {
    window.location.href =
      "https://personadna.onrender.com/linkedin/connect";
  };

  // ============================================================
  // GENERATE DIGITAL DNA
  // ============================================================

  const handleGenerate = async () => {
    if (!resumeFile) {
      alert(
        "Please upload a resume before generating."
      );
      return;
    }

    if (!github.trim()) {
      alert(
        "Please enter your GitHub profile URL."
      );
      return;
    }

    if (!linkedinProfile) {
      alert(
        "Please connect your LinkedIn profile first."
      );
      return;
    }

    try {
      setIsGenerating(true);

      const formData = new FormData();

      formData.append(
        "resume",
        resumeFile
      );

      formData.append(
        "github",
        github
      );

      // Send LinkedIn name to backend
      if (linkedinProfile.name) {
        formData.append(
          "linkedin",
          linkedinProfile.name
        );
      }

      const response =
        await api.post<CandidateReport>(
          "/analyze",
          formData
        );

      console.log(
        "PersonaDNA Backend Response:",
        response.data
      );

      onGenerate(response.data);
    } catch (error) {
      console.error(
        "PersonaDNA analysis failed:",
        error
      );

      alert(
        "Unable to analyze your profile. Please make sure the PersonaDNA backend is running."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  // ============================================================
  // UI
  // ============================================================

  return (
    <section
      id="verify"
      className="bg-[#09090B] py-24"
    >
      <div className="mx-auto max-w-5xl px-6">

        <div className="text-center">

          <p className="font-semibold uppercase tracking-widest text-blue-400">
            Verify Your Profile
          </p>

          <h2 className="mt-4 text-5xl font-bold text-white">
            Build Your Digital DNA
          </h2>

          <p className="mt-6 text-gray-400">
            Upload your resume and connect your
            professional profiles.
          </p>

        </div>

        <div className="mt-16 rounded-3xl border border-white/10 bg-white/5 p-10 backdrop-blur-xl">

          {/* ================================================== */}
          {/* RESUME */}
          {/* ================================================== */}

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

          {/* ================================================== */}
          {/* GITHUB */}
          {/* ================================================== */}

          <div className="mt-10">

            <label className="mb-2 flex items-center gap-2 text-white">

              <Globe size={18} />

              GitHub Profile

            </label>

            <input
              type="url"
              value={github}
              onChange={(e) =>
                setGithub(e.target.value)
              }
              placeholder="https://github.com/username"
              className="w-full rounded-xl border border-white/10 bg-[#111827] p-4 text-white outline-none focus:border-blue-500"
            />

          </div>

          {/* ================================================== */}
          {/* LINKEDIN */}
          {/* ================================================== */}

          <div className="mt-8">

            <label className="mb-2 flex items-center gap-2 text-white">

              <User size={18} />

              LinkedIn Profile

            </label>

            {!linkedinProfile ? (

              <button
                type="button"
                onClick={connectLinkedIn}
                className="flex w-full items-center justify-center gap-3 rounded-xl border border-blue-500/40 bg-blue-600/10 p-4 font-semibold text-blue-400 transition hover:border-blue-400 hover:bg-blue-600/20"
              >

                <User size={20} />

                Connect with LinkedIn

              </button>

            ) : (

              <div className="flex items-center gap-4 rounded-xl border border-green-500/30 bg-green-500/10 p-4">

                {linkedinProfile.profile_picture ? (

                  <img
                    src={
                      linkedinProfile.profile_picture
                    }
                    alt={
                      linkedinProfile.name ||
                      "LinkedIn"
                    }
                    className="h-12 w-12 rounded-full"
                  />

                ) : (

                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/20">

                    <User className="text-green-400" />

                  </div>

                )}

                <div className="flex-1">

                  <p className="font-semibold text-white">

                    {linkedinProfile.name ||
                      "LinkedIn User"}

                  </p>

                  <p className="text-sm text-gray-400">

                    {linkedinProfile.email ||
                      "LinkedIn account connected"}

                  </p>

                </div>

                <CheckCircle
                  className="text-green-400"
                  size={24}
                />

              </div>

            )}

          </div>

          {/* ================================================== */}
          {/* GENERATE */}
          {/* ================================================== */}

          <button
            type="button"
            onClick={handleGenerate}
            disabled={isGenerating}
            className="mt-10 flex w-full items-center justify-center gap-3 rounded-2xl bg-blue-600 py-4 text-lg font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >

            <FileCheck />

            {isGenerating
              ? "Analyzing Profile..."
              : "Generate Digital DNA"}

          </button>

        </div>

      </div>
    </section>
  );
}