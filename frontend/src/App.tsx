import { useState } from "react";

import Navbar from "./components/landing/Navbar";
import Hero from "./components/landing/Hero";
import Problem from "./components/landing/Problem";
import HowItWorks from "./components/landing/HowItWorks";
import UploadSection from "./components/upload/UploadSection";
import ProcessingScreen from "./components/dashboard/ProcessingScreen";
import Dashboard from "./components/dashboard/Dashboard";

import type { CandidateReport } from "./types/report";

function App() {
  const [screen, setScreen] = useState<
    "landing" | "processing" | "dashboard"
  >("landing");

  const [report, setReport] =
    useState<CandidateReport | null>(null);

  if (screen === "processing") {
    return (
      <ProcessingScreen
        onComplete={() => {
          setScreen("dashboard");
        }}
      />
    );
  }

  if (screen === "dashboard" && report) {
    return <Dashboard report={report} />;
  }

  return (
    <div className="min-h-screen bg-[#09090B]">
      <Navbar />

      <Hero />

      <Problem />

      <HowItWorks />

      <UploadSection
        onGenerate={(data: CandidateReport) => {
          console.log(
            "PersonaDNA Report:",
            data
          );

          setReport(data);
          setScreen("processing");
        }}
      />
    </div>
  );
}

export default App;