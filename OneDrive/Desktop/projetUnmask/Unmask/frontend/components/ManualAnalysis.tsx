"use client";

import { useState } from "react";

const API = "http://localhost:8000";

type DiscourseResult = {
  manipulation_score: number;
  signals: { type: string; quote: string; explanation: string }[];
  summary: string;
  verdict: "safe" | "suspicious" | "manipulative";
  warning?: string;
  available: boolean;
};

type PartnershipResult = {
  has_disclosure: boolean;
  flags: { rule: string; severity: string; detail: string; source: string; source_url: string }[];
  compliance_score: number;
  warning?: string;
};

export default function ManualAnalysis() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [discourse, setDiscourse] = useState<DiscourseResult | null>(null);
  const [partnership, setPartnership] = useState<PartnershipResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function analyze(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) {
      setError("Collez un texte à analyser.");
      return;
    }
    setLoading(true);
    setError(null);
    setDiscourse(null);
    setPartnership(null);

    try {
      const [d, p] = await Promise.all([
        fetch(`${API}/audit/discourse`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        }),
        fetch(`${API}/audit/partnerships`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        }),
      ]);

      if (d.ok) setDiscourse(await d.json());
      if (p.ok) setPartnership(await p.json());
    } catch {
      setError("Impossible de contacter l'API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-2xl flex flex-col gap-6">
      <form onSubmit={analyze} className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4">
        <div>
          <label className="text-xs text-gray-500 uppercase tracking-wider mb-2 block">
            Texte à analyser (email, post Instagram, description YouTube, discours…)
          </label>
          <textarea
            rows={8}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Collez ici un texte suspect…"
            className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            autoFocus
          />
          <p className="text-xs text-gray-600 mt-1">{text.length} caractères</p>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition-colors rounded-xl py-3 font-semibold text-sm cursor-pointer"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full inline-block" />
              Analyse en cours…
            </span>
          ) : (
            "Analyser le texte"
          )}
        </button>
      </form>

      {discourse && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-gray-800 text-gray-400 text-xs font-bold flex items-center justify-center">3</span>
            Analyse du discours (IA)
          </h3>

          {!discourse.available ? (
            <p className="text-xs text-gray-500 italic">{discourse.warning}</p>
          ) : (
            <>
              <div className="flex items-center gap-4 mb-4">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Score de manipulation</p>
                  <div className="flex items-center gap-2">
                    <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          discourse.manipulation_score < 30 ? "bg-green-500" :
                          discourse.manipulation_score < 60 ? "bg-yellow-500" : "bg-red-500"
                        }`}
                        style={{ width: `${discourse.manipulation_score}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-white">{discourse.manipulation_score}/100</span>
                  </div>
                </div>
                <span className={`text-xs px-3 py-1 rounded-full border font-medium ${
                  discourse.verdict === "safe" ? "bg-green-900/40 text-green-300 border-green-700" :
                  discourse.verdict === "suspicious" ? "bg-yellow-900/40 text-yellow-300 border-yellow-700" :
                  "bg-red-900/40 text-red-300 border-red-700"
                }`}>
                  {discourse.verdict === "safe" ? "Sain" : discourse.verdict === "suspicious" ? "Suspect" : "Manipulatoire"}
                </span>
              </div>

              {discourse.summary && (
                <p className="text-xs text-gray-400 mb-4 p-3 bg-gray-800 rounded-lg">{discourse.summary}</p>
              )}

              {discourse.signals.map((s, i) => (
                <div key={i} className="mb-3 p-3 rounded-lg bg-red-900/20 border border-red-900/40 text-xs">
                  <p className="font-semibold text-red-300 mb-1">{s.type}</p>
                  {s.quote && <p className="italic text-gray-400 mb-1">« {s.quote} »</p>}
                  <p className="text-gray-500">{s.explanation}</p>
                </div>
              ))}

              {discourse.signals.length === 0 && (
                <p className="text-xs text-green-400">Aucun signal de manipulation détecté.</p>
              )}
            </>
          )}
        </div>
      )}

      {partnership && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-gray-800 text-gray-400 text-xs font-bold flex items-center justify-center">2</span>
            Conformité loi influenceurs 2023
          </h3>

          <div className="flex items-center gap-3 mb-4">
            <div className="w-24 h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  partnership.compliance_score >= 70 ? "bg-green-500" :
                  partnership.compliance_score >= 40 ? "bg-yellow-500" : "bg-red-500"
                }`}
                style={{ width: `${partnership.compliance_score}%` }}
              />
            </div>
            <span className="text-xs text-gray-400">{partnership.compliance_score}/100</span>
            <span className={`text-xs font-medium ${partnership.has_disclosure ? "text-green-400" : "text-red-400"}`}>
              {partnership.has_disclosure ? "✓ Mention partenariat présente" : "✗ Pas de mention partenariat"}
            </span>
          </div>

          {partnership.flags.map((f, i) => (
            <div key={i} className={`mb-2 p-2.5 rounded-lg text-xs ${
              f.severity === "violation"
                ? "bg-red-900/30 border border-red-800 text-red-300"
                : "bg-yellow-900/30 border border-yellow-800 text-yellow-300"
            }`}>
              <p className="font-semibold">{f.rule}</p>
              <p className="text-gray-400 mt-0.5">{f.detail}</p>
              {f.source_url && (
                <a href={f.source_url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline text-xs mt-1 inline-block">
                  ↗ {f.source}
                </a>
              )}
            </div>
          ))}

          {partnership.flags.length === 0 && (
            <p className="text-xs text-green-400">Aucune violation détectée.</p>
          )}
        </div>
      )}
    </div>
  );
}
