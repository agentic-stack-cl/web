import radarMetricsRaw from "@/data/radar-metrics.json";

export interface SparklineHistory {
  timestamps: string[];
  stars?: number[];
  downloads?: number[];
}

export interface CommunityMetrics {
  stars?: number;
  forks?: number;
  monthly_downloads?: number;
  issues_closed_ratio?: number;
  history?: SparklineHistory;
}

export interface CveDetail {
  id: string;
  summary?: string;
  url?: string;
  severity?: string;
}

export interface SecurityChecks {
  branch_protection?: boolean;
  code_review?: boolean;
  pinned_dependencies?: boolean;
}

export interface LicenseInfo {
  spdx?: string;
  type?: "permissive" | "copyleft" | "proprietary" | "other";
}

export type ShieldTier = "tier-a" | "tier-b" | "tier-c" | "enterprise" | "pattern" | "unknown";

export interface SecurityMetrics {
  tier?: ShieldTier;
  tier_label?: string;
  openssf_score?: number;
  days_since_last_release?: number;
  releases_last_year?: number;
  active_maintainers_6m?: number;
  open_cves?: number;
  cves_detail?: CveDetail[];
  license?: LicenseInfo;
  checks?: SecurityChecks;
  certifications?: string[];
  security_url?: string;
}

export interface BlipMetrics {
  kind?: "oss" | "proprietary" | "pattern";
  community?: CommunityMetrics;
  security?: SecurityMetrics;
}

export interface RadarMetricsFile {
  updated?: string;
  entries?: Record<string, BlipMetrics>;
}

const metricsFile = (radarMetricsRaw as unknown as RadarMetricsFile) ?? {};
const entries = metricsFile.entries ?? {};

/**
 * Retorna las métricas computadas de un blip por su ID, o null si no están registradas.
 */
export function getMetricsFor(blipId: string): BlipMetrics | null {
  if (!entries || typeof entries !== "object") return null;
  return entries[blipId] ?? null;
}

/**
 * Formatea números grandes a notación compacta legible (ej. 28450 -> 28.5k, 1200000 -> 1.2M).
 */
export function formatCompactNumber(value: number | undefined | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) return "—";
  if (value >= 1_000_000) {
    const formatted = (value / 1_000_000).toFixed(1);
    return `${formatted.endsWith(".0") ? formatted.slice(0, -2) : formatted}M`;
  }
  if (value >= 1_000) {
    const formatted = (value / 1_000).toFixed(1);
    return `${formatted.endsWith(".0") ? formatted.slice(0, -2) : formatted}k`;
  }
  return value.toLocaleString("es-CL");
}

export interface ShieldTierVisual {
  tier: ShieldTier;
  glyph: string;
  meter: string;
  label: string;
  badgeClass: string;
}

/**
 * Infografía heráldica y neutral para el nivel de seguridad.
 * No utiliza la paleta semafórica (verde/azul/amarillo/rojo) para no confundirse
 * con los anillos del radar tecnológico (Adoptar, Probar, Evaluar, Esperar).
 */
export function getShieldTierInfo(metrics: BlipMetrics | null): ShieldTierVisual {
  if (!metrics) {
    return {
      tier: "unknown",
      glyph: "—",
      meter: "—",
      label: "Sin telemetría",
      badgeClass:
        "border-slate-200 bg-slate-50 text-slate-500 dark:border-brand-900 dark:bg-brand-950 dark:text-slate-400",
    };
  }

  if (metrics.kind === "pattern" || metrics.security?.tier === "pattern") {
    return {
      tier: "pattern",
      glyph: "📐",
      meter: "—",
      label: "Práctica / Patrón",
      badgeClass:
        "border-slate-200 bg-slate-50/70 text-slate-500 italic dark:border-brand-900 dark:bg-brand-950/70 dark:text-slate-400",
    };
  }

  if (metrics.kind === "proprietary" || metrics.security?.tier === "enterprise") {
    return {
      tier: "enterprise",
      glyph: "🏛️",
      meter: "✓",
      label: "Certificado",
      badgeClass:
        "border-slate-300 bg-slate-100 font-semibold text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100",
    };
  }

  const tier = metrics.security?.tier;

  switch (tier) {
    case "tier-a":
      return {
        tier: "tier-a",
        glyph: "🛡️",
        meter: "▰▰▰",
        label: "Blindaje Alto",
        badgeClass:
          "border-slate-300 bg-slate-100 font-medium text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100",
      };
    case "tier-b":
      return {
        tier: "tier-b",
        glyph: "🛡️",
        meter: "▰▰▱",
        label: "Blindaje Medio",
        badgeClass:
          "border-slate-200 bg-slate-50 text-slate-700 dark:border-brand-800 dark:bg-brand-900/60 dark:text-slate-300",
      };
    case "tier-c":
      return {
        tier: "tier-c",
        glyph: "⚠️",
        meter: "▰▱▱",
        label: "Atención Requerida",
        badgeClass:
          "border-dashed border-slate-400 bg-slate-100 font-medium text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200",
      };
    default:
      return {
        tier: "unknown",
        glyph: "—",
        meter: "—",
        label: "Sin telemetría",
        badgeClass:
          "border-slate-200 bg-slate-50 text-slate-500 dark:border-brand-900 dark:bg-brand-950 dark:text-slate-400",
      };
  }
}
