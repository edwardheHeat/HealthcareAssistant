export interface ChartPoint {
  date: string;
  value: number | null;
}

export interface BasicStats {
  avg_weight_7d: number | null;
  avg_weight_30d: number | null;
  previous_avg_weight_30d: number | null;
  weight_trend: number | null;
  latest_weight_kg: number | null;
  bar_chart_data: {
    last_7_days: ChartPoint[];
    last_30_days: ChartPoint[];
  };
}

export interface DietStats {
  avg_calories_7d: number | null;
  avg_calories_30d: number | null;
  previous_avg_calories_30d: number | null;
  calories_trend: number | null;
  avg_protein_g_7d: number | null;
  avg_protein_g_30d: number | null;
  avg_carbs_g_7d: number | null;
  avg_carbs_g_30d: number | null;
  avg_fat_g_7d: number | null;
  avg_fat_g_30d: number | null;
  bar_chart_data: {
    last_7_days: ChartPoint[];
    last_30_days: ChartPoint[];
  };
}

export interface ExerciseStats {
  avg_duration_7d: number | null;
  avg_duration_30d: number | null;
  previous_avg_duration_30d: number | null;
  duration_trend: number | null;
  intensity_distribution: {
    low: number;
    medium: number;
    high: number;
  };
  bar_chart_data: {
    last_7_days: ChartPoint[];
    last_30_days: ChartPoint[];
  };
  // Apple Health step data (injected when synced)
  avg_daily_steps?: number;
  avg_daily_steps_7d?: number;
  total_steps_7d?: number;
  total_steps_30d?: number;
  steps_bar_chart_7d?: ChartPoint[];
  steps_bar_chart_30d?: ChartPoint[];
  // Apple Health workout data (injected from export)
  active_energy_7d?: number;
}

export interface SleepStats {
  avg_sleep_duration_7d: number | null;
  avg_sleep_duration_30d: number | null;
  previous_avg_sleep_duration_30d: number | null;
  sleep_trend: number | null;
  avg_quality_7d: number | null;
  avg_quality_30d: number | null;
  bar_chart_data: {
    last_7_days: ChartPoint[];
    last_30_days: ChartPoint[];
  };
}

export interface PeriodCycleStats {
  last_cycle_start: string | null;
  last_cycle_end: string | null;
  avg_cycle_length_days: number | null;
  predicted_next_start_start: string | null;
  predicted_next_start_end: string | null;
}

export interface HealthStats {
  basic: BasicStats;
  diet: DietStats;
  exercise: ExerciseStats;
  sleep: SleepStats;
  period_cycle: PeriodCycleStats;
}

export interface IndicatorAnalysisPeriods {
  "7d": string | null;
  "30d": string | null;
}

export interface DashboardAnalysis {
  basic: IndicatorAnalysisPeriods;
  diet: IndicatorAnalysisPeriods;
  exercise: IndicatorAnalysisPeriods;
  sleep: IndicatorAnalysisPeriods;
}

export interface OverallAnalysisSummary {
  summary: string;
  created_at: string;
}

export interface AppleHealthData {
  id: number;
  synced_at: string;
  source?: "mock" | "export";
  // Legacy mock format
  steps?: number[];
  sleep?: number[];
  // Summary stats (common to both)
  total_steps_7d: number;
  avg_daily_steps: number;
  avg_sleep_hrs?: number;
  midweek_sleep_drop?: boolean;
  high_activity_fluctuation?: boolean;
  // Export format
  totals?: Record<string, unknown>;
  daily_steps?: Record<string, number>;
  daily_workouts?: Record<string, unknown>;
  daily_sleep?: Record<string, number>;
  daily_active_energy?: Record<string, number>;
}

export interface DashboardResponse {
  stats: HealthStats;
  analysis: DashboardAnalysis;
  overall_analysis: OverallAnalysisSummary | null;
  apple_health: AppleHealthData | null;
}

export interface Alert {
  id: number;
  user_id: number;
  created_at: string;
  alert_type: "abnormal" | "stale";
  severity: "warning" | "critical";
  metric: string;
  message: string;
  is_read: boolean;
}
