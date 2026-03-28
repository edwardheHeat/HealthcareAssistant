export interface DietStats {
  avg_calories_7d: number | null;
  calorie_variance_7d: number | null;
  calorie_deficit_surplus_vs_tdee: number | null;
  estimated_tdee: number | null;
  avg_protein_g_7d: number | null;
  avg_carbs_g_7d: number | null;
  avg_fat_g_7d: number | null;
  last_recorded_at: string | null;
}

export interface SleepStats {
  avg_duration_hrs_7d: number | null;
  sleep_consistency_score: number | null;
  deviation_from_recommended_hrs: number | null;
  last_recorded_at: string | null;
}

export interface ExerciseStats {
  avg_daily_met_30d: number | null;
  cardio_sessions_per_week: number | null;
  activity_trend: string | null;
  last_recorded_at: string | null;
}

export interface PeriodStats {
  cycle_phase: string | null;
  current_flow_amount: string | null;
  last_recorded_at: string | null;
}

export interface HealthStats {
  user_id: number;
  current_weight_lbs: number | null;
  current_height_ft: number | null;
  bmi: number | null;
  weight_trend: string | null;
  height_trend: string | null;
  last_bi_recorded_at: string | null;
  diet: DietStats;
  sleep: SleepStats;
  exercise: ExerciseStats;
  period: PeriodStats;
}

export interface Alert {
  id: number;
  user_id: number;
  created_at: string;
  alert_type: "abnormal" | "stale";
  metric: string;
  message: string;
  is_read: boolean;
}
