export type WorkActivityLevel =
  | "sedentary"
  | "light"
  | "moderate"
  | "heavy"
  | "very_heavy";

export type ExerciseIntensity = "low" | "moderate" | "high" | "very_high";

export type FlowAmount = "light" | "medium" | "heavy";

export interface BasicIndicatorRecord {
  id: number;
  user_id: number;
  recorded_at: string;
  height_ft: number;
  weight_lbs: number;
}

export interface DietRecord {
  id: number;
  user_id: number;
  recorded_at: string;
  calorie_intake: number;
  food_image_path: string | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
}

export interface SleepRecord {
  id: number;
  user_id: number;
  sleep_start: string;
  wake_time: string;
}

export interface ExerciseRecord {
  id: number;
  user_id: number;
  recorded_at: string;
  work_activity_level: WorkActivityLevel;
  exercise_type: string;
  exercise_intensity: ExerciseIntensity;
  duration_min: number;
  met_value: number;
}

export interface PeriodRecord {
  id: number;
  user_id: number;
  recorded_at: string;
  has_flow: boolean;
  flow_amount: FlowAmount | null;
}
