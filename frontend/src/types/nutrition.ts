export type SexType = 'male' | 'female' | 'other';
export type ActivityLevelType = 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';
export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

/** Khớp chính xác schema backend HealthProfileResponse */
export interface HealthProfile {
  id: string;
  user_id: string;
  date_of_birth: string | null;
  sex: SexType | null;
  height_cm: number | null;
  weight_kg: number | null;
  diabetes_type: string;
  diagnosis_year: number | null;
  activity_level: ActivityLevelType | null;
  dietary_preference: string | null;
  bmi: number | null;
  updated_at: string;
}

export interface HealthProfilePayload {
  user_id?: string;
  date_of_birth?: string | null;
  sex?: SexType | null;
  height_cm?: number | null;
  weight_kg?: number | null;
  diabetes_type?: string;
  diagnosis_year?: number | null;
  activity_level?: ActivityLevelType | null;
  dietary_preference?: string | null;
}

/**
 * Thông tin mở rộng phục vụ module Nutrition ở FE khi backend HealthProfile chưa có các cột này.
 * Lưu trữ cục bộ theo user_id (LocalStorage adapter).
 */
export interface LocalClinicalPreferences {
  nutrition_goal: 'weight_loss' | 'maintenance';
  comorbidities: string[]; // vd: ['Type 2 Diabetes', 'Hypertension', 'CKD']
  allergies: string[];     // vd: ['Hải sản', 'Đậu nành', 'Đậu phộng', 'Trứng']
  weight_updated_at?: string;
}

/** Khớp chính xác schema backend FoodResponse */
export interface FoodItem {
  id: string;
  name: string;
  category: string;
  serving_size_g: number;
  energy_kcal: number;
  carbohydrate_g: number;
  protein_g: number;
  fat_g: number;
  fiber_g: number | null;
  sugar_g: number | null;
  glycemic_index: number | null;
  glycemic_load: number | null;
  sodium_mg: number | null;
  saturated_fat_g: number | null;
  is_test_data: boolean;
  source_name: string | null;
  source_url: string | null;
  created_at: string;
  updated_at: string;
}

/** Khớp chính xác schema backend RecommendedFoodItem */
export interface RecommendedFoodItem {
  food_id: string;
  food_name: string;
  category: string;
  serving_size_g: number;
  serving_multiplier: number;
  energy_kcal: number;
  carbohydrate_g: number;
  protein_g: number;
  fat_g: number;
  fiber_g: number | null;
  sugar_g: number | null;
  glycemic_index: number | null;
  glycemic_load: number | null;
  sodium_mg: number | null;
  saturated_fat_g: number | null;
  score: number;
  reasons: string[];
  item_warning?: string | null;
}

export interface MealRecommendationRequest {
  user_id: string;
  meal_type: MealType;
  dietary_preference?: string | null;
  excluded_food_ids?: string[] | null;
  excluded_keywords?: string[] | null;
  custom_target?: {
    target_energy_kcal?: number | null;
    target_carbohydrate_g?: number | null;
    max_carbohydrate_g?: number | null;
  } | null;
}

/** Khớp chính xác schema backend MealRecommendationResponse */
export interface MealRecommendationResponse {
  recommendation_id: string;
  user_id: string;
  meal_type: MealType;
  algorithm_version: string;
  generated_at: string;
  items: RecommendedFoodItem[];
  total_energy_kcal: number;
  total_carbohydrate_g: number;
  total_protein_g: number;
  total_fat_g: number;
  total_fiber_g: number;
  meal_balance_evaluation: string;
  safety_notes: string[];
  clinical_safety_disclaimer: string;
}

export interface DailyMealPlan {
  date: string; // YYYY-MM-DD
  generated_at: string;
  meals: Partial<Record<MealType, MealRecommendationResponse>>;
  status: 'active' | 'draft' | 'abstained';
  abstention_reason?: string | null;
  missing_fields?: string[];
  applied_preference?: string | null;
  applied_goal?: string | null;
}

export type DiaryLogStatus = 'planned' | 'eaten_full' | 'eaten_partial' | 'eaten_other' | 'skipped';

export interface MealDiaryEntry {
  id: string;
  date: string;
  meal_type: MealType;
  status: DiaryLogStatus;
  portion_ratio: number; // 1.0, 0.75, 0.5, 0
  logged_at: string;
  note?: string;
  custom_food_name?: string;
  photo_preview_url?: string;
  actual_energy_kcal: number;
  actual_carbohydrate_g: number;
  actual_protein_g: number;
  actual_fat_g: number;
  actual_fiber_g: number;
  actual_sodium_mg: number;
}

export interface WeightLogEntry {
  date: string;
  weight_kg: number;
}

export interface SafetyAlertItem {
  id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  code: 'missing_profile' | 'ckd_restriction' | 'allergy_conflict' | 'no_valid_plan' | 'energy_out_of_range';
  title: string;
  cause: string;
  details: string[];
  action_guidance: string;
  action_label: string;
  action_route: string;
}

export interface RagReferenceItem {
  kb_id: string;
  source_id: string;
  title: string;
  organization: string;
  year: number;
  excerpt: string;
  url: string;
}
