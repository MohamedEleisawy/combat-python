"use client";

import type { AuditResponse } from "@/app/page";

type Props = { results: AuditResponse };

export default function AuditDashboard({ results }: Props) {
  const { global_score, verdict, pillars, entity, disclaimer } = results;

  const verdictStyle = {
    fiable: { bg: "bg-green-900/50", border: "border-green-700", text: "text-green-300", label: "Fiable" },
    suspect: { bg: "bg-yellow-900/50", border: "border-yellow-700", text: "text-yellow-300", label: "Suspect" },
    alerte: { bg: "bg-red-900/50", border: "border-red-700", text: "text-red-300", label: "Alerte" },
  }[verdict];

  return (
    <div className="w-full max-w-2xl mt-8 flex flex-col gap-6">
      {/* Score global */}
      <div className={`rounded-2xl border p-6 ${verdictStyle.bg} ${verdictStyle.border}`}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Score global de crédibilité</p>
            <p className="text-xs text-gray-500">
              {entity.name && <span className="text-gray-300">{entity.name}</span>}
              {entity.siren && <span className="ml-2 text-gray-500">SIREN {entity.siren}</span>}
            </p>
          </div>
          <div className="text-right">
            <p className={`text-4xl font-black ${verdictStyle.text}`}>{global_score}<span className="text-2xl">/100</span></p>
            <p className={`text-sm font-semibold ${verdictStyle.text}`}>{verdictStyle.label}</p>
          </div>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              global_score >= 70 ? "bg-green-500" : global_score >= 40 ? "bg-yellow-500" : "bg-red-500"
            }`}
            style={{ width: `${global_score}%` }}
          />
        </div>
      </div>

      {/* Piliers */}
      <div className="grid grid-cols-1 gap-4">
        <PillarCard
          number="1"
          title="Identité légale"
          subtitle="data.gouv.fr — Annuaire des Entreprises"
          data={pillars.legal_identity as Record<string, unknown>}
          render={(d) => <LegalPillar data={d} />}
        />
        <PillarCard
          number="2"
          title="Transparence partenariats"
          subtitle="Loi n°2023-451 du 9 juin 2023"
          data={pillars.partnerships as Record<string, unknown>}
          render={(d) => <PartnershipPillar data={d} />}
        />
        <PillarCard
          number="3"
          title="Analyse du discours"
          subtitle="Détection de manipulation rhétorique (IA)"
          data={pillars.discourse as Record<string, unknown>}
          render={(d) => <DiscoursePillar data={d} />}
        />
        <PillarCard
          number="4"
          title="Cohérence d'engagement"
          subtitle="YouTube Data API v3"
          data={pillars.youtube as Record<string, unknown>}
          render={(d) => <YoutubePillar data={d} />}
        />
        <PillarCard
          number="5"
          title="Réputation externe"
          subtitle="OSINT — Presse & signalements"
          data={pillars.osint as Record<string, unknown>}
          render={(d) => <OsintPillar data={d} />}
        />
        <PillarCard
          number="6"
          title="Conformité AMF/ACPR"
          subtitle="ABE Infoservice — Liste noire officielle"
          data={pillars.compliance as Record<string, unknown>}
          render={(d) => <CompliancePillar data={d} />}
        />
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-gray-600 text-center px-4">{disclaimer}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// PillarCard wrapper
// ---------------------------------------------------------------------------

function PillarCard({
  number, title, subtitle, data,
  render,
}: {
  number: string;
  title: string;
  subtitle: string;
  data: Record<string, unknown> | undefined;
  render: (d: Record<string, unknown>) => React.ReactNode;
}) {
  const unavailable = !data || data.available === false;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="w-7 h-7 rounded-full bg-gray-800 text-gray-400 text-xs font-bold flex items-center justify-center flex-shrink-0">
            {number}
          </span>
          <div>
            <h3 className="text-sm font-semibold text-white">{title}</h3>
            <p className="text-xs text-gray-500">{subtitle}</p>
          </div>
        </div>
        {unavailable && (
          <span className="text-xs bg-gray-800 text-gray-500 px-2 py-0.5 rounded-full border border-gray-700">
            Indisponible
          </span>
        )}
      </div>

      {unavailable ? (
        <p className="text-xs text-gray-500 italic ml-10">
          {(data?.warning as string) || "Clé API non configurée."}
        </p>
      ) : (
        <div className="ml-10">{render(data!)}</div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Renderers par pilier
// ---------------------------------------------------------------------------

function LegalPillar({ data }: { data: Record<string, unknown> }) {
  const found = data.found as boolean;
  const identity = data.identity as Record<string, unknown> | null;
  return (
    <div>
      <StatusBadge ok={found} okLabel="Entité trouvée" failLabel="Introuvable" />
      {identity && (
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <InfoRow label="Nom" value={identity.nom as string} />
          <InfoRow label="SIREN" value={identity.siren as string} />
          <InfoRow label="Statut" value={(identity.est_actif as boolean) ? "Active" : "Radiée"} alert={!identity.est_actif as boolean} />
          <InfoRow label="Forme" value={identity.forme_juridique as string} />
          <InfoRow label="Création" value={identity.date_creation as string} />
        </div>
      )}
      {identity?.source_url && (
        <SourceLink href={identity.source_url as string} label="Vérifier sur data.gouv.fr" />
      )}
      {data.warning && <Warning text={data.warning as string} />}
    </div>
  );
}

function PartnershipPillar({ data }: { data: Record<string, unknown> }) {
  const score = data.compliance_score as number;
  const flags = (data.flags as Record<string, unknown>[]) || [];
  const hasDisclosure = data.has_disclosure as boolean;

  if (data.warning && flags.length === 0) {
    return <Warning text={data.warning as string} />;
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <ScoreBar score={score} />
        <StatusBadge ok={hasDisclosure} okLabel="Mention partenariat ✓" failLabel="Pas de mention" />
      </div>
      {flags.map((f, i) => (
        <div key={i} className={`mb-2 p-2 rounded-lg text-xs ${
          f.severity === "violation" ? "bg-red-900/30 border border-red-800 text-red-300" : "bg-yellow-900/30 border border-yellow-800 text-yellow-300"
        }`}>
          <p className="font-semibold">{f.rule as string}</p>
          <p className="text-gray-400 mt-0.5">{f.detail as string}</p>
          {f.source_url && <SourceLink href={f.source_url as string} label={f.source as string} />}
        </div>
      ))}
      {flags.length === 0 && <p className="text-xs text-green-400">Aucune violation détectée.</p>}
    </div>
  );
}

function DiscoursePillar({ data }: { data: Record<string, unknown> }) {
  const score = data.manipulation_score as number;
  const signals = (data.signals as Record<string, unknown>[]) || [];
  const verdict = data.verdict as string;

  const verdictColor = verdict === "safe" ? "text-green-400" : verdict === "suspicious" ? "text-yellow-400" : "text-red-400";

  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <ScoreBar score={100 - score} />
        <span className={`text-xs font-semibold ${verdictColor}`}>
          {verdict === "safe" ? "Sain" : verdict === "suspicious" ? "Suspect" : "Manipulatoire"}
        </span>
      </div>
      {data.summary && <p className="text-xs text-gray-400 mb-2">{data.summary as string}</p>}
      {signals.map((s, i) => (
        <div key={i} className="mb-2 p-2 rounded-lg bg-red-900/20 border border-red-900/50 text-xs">
          <p className="font-semibold text-red-300">{s.type as string}</p>
          {s.quote && <p className="italic text-gray-400 mt-0.5">« {s.quote as string} »</p>}
          <p className="text-gray-500 mt-0.5">{s.explanation as string}</p>
        </div>
      ))}
    </div>
  );
}

function YoutubePillar({ data }: { data: Record<string, unknown> }) {
  const flags = (data.flags as Record<string, unknown>[]) || [];
  return (
    <div>
      <div className="grid grid-cols-3 gap-2 mb-3 text-xs">
        <StatBox label="Abonnés" value={fmt(data.subscribers as number)} />
        <StatBox label="Total vues" value={fmt(data.total_views as number)} />
        <StatBox label="Vidéos" value={fmt(data.video_count as number)} />
      </div>
      {typeof data.engagement_ratio === "number" && (
        <div className="flex items-center gap-2 mb-3">
          <ScoreBar score={data.engagement_score as number} />
          <span className="text-xs text-gray-400">Ratio vues/abonnés : {(data.engagement_ratio as number).toFixed(2)}</span>
        </div>
      )}
      {flags.map((f, i) => (
        <div key={i} className={`mb-2 p-2 rounded-lg text-xs ${
          f.severity === "suspicious" ? "bg-red-900/30 border border-red-800 text-red-300" : "bg-yellow-900/30 border border-yellow-800 text-yellow-300"
        }`}>
          {f.detail as string}
        </div>
      ))}
      {data.channel_url && <SourceLink href={data.channel_url as string} label="Voir la chaîne YouTube" />}
    </div>
  );
}

function OsintPillar({ data }: { data: Record<string, unknown> }) {
  const results = (data.results as Record<string, unknown>[]) || [];
  const alertCount = data.alert_count as number;
  const score = data.reputation_score as number;
  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <ScoreBar score={score} />
        {alertCount > 0 ? (
          <span className="text-xs text-red-400 font-semibold">{alertCount} alerte(s) trouvée(s)</span>
        ) : (
          <span className="text-xs text-green-400">Aucune alerte détectée</span>
        )}
      </div>
      {results.filter(r => r.is_alert).slice(0, 3).map((r, i) => (
        <div key={i} className="mb-2 p-2 rounded-lg bg-red-900/20 border border-red-900/50 text-xs">
          <a href={r.url as string} target="_blank" rel="noopener noreferrer" className="text-red-300 hover:underline font-medium">
            {r.title as string}
          </a>
          <p className="text-gray-500 mt-0.5 line-clamp-2">{r.snippet as string}</p>
        </div>
      ))}
    </div>
  );
}

function CompliancePillar({ data }: { data: Record<string, unknown> }) {
  const blacklisted = data.is_blacklisted as boolean;
  const matches = (data.matches as Record<string, unknown>[]) || [];
  return (
    <div>
      <StatusBadge
        ok={!blacklisted}
        okLabel="Absent de la liste noire"
        failLabel={`Liste noire AMF (${matches.length} correspondance${matches.length > 1 ? "s" : ""})`}
      />
      {matches.map((m, i) => (
        <div key={i} className="mt-2 p-2 rounded-lg bg-red-900/30 border border-red-800 text-xs text-red-300">
          <p className="font-semibold">{m.matched_value as string}</p>
          <p className="text-gray-400">{(m.categories as string[])?.join(", ")}</p>
          {m.source_url && <SourceLink href={m.source_url as string} label={m.source as string} />}
        </div>
      ))}
      {data.warning && <Warning text={data.warning as string} />}
      <SourceLink href="https://www.abe-infoservice.fr/liste-noire" label="Consulter la liste noire ABE Infoservice" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// UI atoms
// ---------------------------------------------------------------------------

function StatusBadge({ ok, okLabel, failLabel }: { ok: boolean; okLabel: string; failLabel: string }) {
  return (
    <span className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full border font-medium ${
      ok
        ? "bg-green-900/40 text-green-300 border-green-700"
        : "bg-red-900/40 text-red-300 border-red-700"
    }`}>
      {ok ? "✓ " : "✗ "}{ok ? okLabel : failLabel}
    </span>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? "bg-green-500" : score >= 40 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-20 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
      </div>
      <span className="text-xs text-gray-400">{score}/100</span>
    </div>
  );
}

function InfoRow({ label, value, alert }: { label: string; value?: string; alert?: boolean }) {
  if (!value) return null;
  return (
    <div>
      <p className="text-gray-600 text-xs">{label}</p>
      <p className={`text-xs font-medium ${alert ? "text-red-400" : "text-gray-200"}`}>{value}</p>
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-2 text-center">
      <p className="text-gray-500 text-xs">{label}</p>
      <p className="text-white text-sm font-semibold">{value}</p>
    </div>
  );
}

function Warning({ text }: { text: string }) {
  return <p className="text-yellow-400 text-xs mt-2">⚠ {text}</p>;
}

function SourceLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 mt-2 transition-colors"
    >
      ↗ {label}
    </a>
  );
}

function fmt(n?: number): string {
  if (n === null || n === undefined) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}
