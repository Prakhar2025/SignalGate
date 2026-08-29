export interface ComparisonRow {
  metric: string;
  baseline: string;
  agent: string;
  change: string;
}

export interface SystemMetrics {
  spurious_catch_rate: number | null;
  spurious_catch_ci95: [number, number];
  false_reject_rate: number | null;
  false_rejects: number;
  sound_n: number;
  sound_promising: number;
  precision_reject: number | null;
  per_stratum: Record<string, { catch: number; n: number; ci95: [number, number] }>;
  cost_usd_mean: number;
  est_tokens_mean: number;
  n_cases: number;
}

export interface MetricsDoc {
  baseline: SystemMetrics;
  agent: SystemMetrics;
  delta_catch_rate: number;
  mcnemar: {
    baseline_only_correct: number;
    agent_only_correct: number;
    both_correct: number;
    both_wrong: number;
    p_value: number;
  };
  mode: string;
  model_id: string;
  prompt_version: string;
  dataset_seed: number;
}

export interface Snapshot {
  metrics?: MetricsDoc;
  metrics_holdout?: MetricsDoc;
  ablation_metrics?: Record<
    string,
    { stage: string; spurious_catch_rate: number; false_reject_rate: number; est_tokens_mean: number }
  >;
}

import snapshot from "@/data/snapshot.json";

/** Live API first; the committed snapshot keeps the site honest without a backend. */
export async function loadSnapshot(): Promise<Snapshot> {
  try {
    const res = await fetch("/api/metrics", { cache: "no-store" });
    if (res.ok) {
      const live = (await res.json()) as Partial<Snapshot>;
      if (live.metrics) return live as unknown as Snapshot;
    }
  } catch {
    /* backend not running: fall through to the committed snapshot */
  }
  return snapshot as unknown as Snapshot;
}
