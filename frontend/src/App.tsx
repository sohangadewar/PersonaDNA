import { useState } from "react";
import Features from "./components/landing/Features";
import Technology from "./components/landing/Technology";
import Roadmap from "./components/landing/Roadmap";
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

    <Features />

    <HowItWorks />

    <Technology />

    <Roadmap />

    <div id="generate-dna" className="scroll-mt-24">
      <UploadSection
        onGenerate={(data: CandidateReport) => {
          console.log("========== APP REPORT DEBUG ==========");
          console.log("Full report:", data);
          console.log("verified_claims:", data.verified_claims);
          console.log("claim_stats:", data.claim_stats);
          console.log("supported:", data.claim_stats?.supported);
          console.log("======================================");

          setReport(data);
          setScreen("processing");
        }}
      />
    </div>
  </div>
);
}

export default App;