"use client";

import { useState } from "react";
import AuditForm from "@/components/AuditForm";
import AuditDashboard from "@/components/AuditDashboard";
import ManualAnalysis from "@/components/ManualAnalysis";

export type AuditResponse = {
  entity: {
    name?: string;
    siren?: string;
    url?: string;
    sector?: string;
  };
  global_score: number;
  verdict: "fiable" | "suspect" | "alerte";
  pillars: Record<string, unknown>;
  disclaimer: string;
};

export default function Home() {
  const [results, setResults] = useState<AuditResponse | null>(null);
  const [mode, setMode] = useState<"audit" | "manual">("audit");

  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col items-center px-4 py-10">
      {/* Header */}
      <header className="mb-10 text-center">
        <div className="flex items-center justify-center gap-3 mb-3">
          <span className="text-3xl font-black tracking-tight text-white">
            Un<span className="text-indigo-400">mask</span>
          </span>
          <span className="text-xs bg-indigo-900 text-indigo-300 px-2 py-0.5 rounded-full font-medium">v2.0</span>
        </div>
        <p className="text-gray-400 text-sm max-w-md">
          Audit de crédibilité IA — identité légale, conformité AMF, analyse du discours, engagement, réputation.
        </p>

        {/* Mode switcher */}
        <div className="flex mt-6 gap-2 justify-center">
          <button
            onClick={() => setMode("audit")}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              mode === "audit"
                ? "bg-indigo-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-white"
            }`}
          >
            Audit d'entité
          </button>
          <button
            onClick={() => setMode("manual")}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              mode === "manual"
                ? "bg-indigo-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-white"
            }`}
          >
            Analyse de texte
          </button>
        </div>
      </header>

      {mode === "audit" ? (
        <>
          <AuditForm onResults={setResults} onReset={() => setResults(null)} />
          {results && <AuditDashboard results={results} />}
        </>
      ) : (
        <ManualAnalysis />
      )}

      <footer className="mt-16 text-center text-gray-600 text-xs max-w-lg">
        Aucun verdict définitif. Données issues de sources publiques officielles.
        Pas de stockage de données personnelles (RGPD).
      </footer>
    </main>
  );
}
