import { getStoredToken } from './api';
import type {
  DailyRecommendationsResponse,
  FoodAlternativeItem,
  FoodItem,
  FoodSubstitutionRequest,
  HealthProfile,
  HealthProfileCompleteness,
  HealthProfilePayload,
  MealLog,
  MealLogCreate,
  MealLogListResponse,
  MealLogUpdate,
  MealRecommendationRequest,
  MealRecommendationResponse,
  MealType,
  NutritionProgressResponse,
  RagReferenceItem,
  RecommendedFoodItem,
  SafetyAlertsResponse,
  WeightRecord,
  WeightRecordCreate,
} from '../types/nutrition';

const BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
).replace(/\/+$/, '');

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  const response = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers });
  const isJson = (response.headers.get('content-type') || '').includes('application/json');
  const data = isJson ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : `HTTP ${response.status}`;
    const err = new Error(detail) as Error & { status?: number; detail?: unknown };
    err.status = response.status;
    err.detail = data?.detail;
    throw err;
  }
  return data as T;
}

/* ==========================================================================
   1. HEALTH PROFILE API
   ========================================================================== */

export const healthProfileApi = {
  getMe(): Promise<HealthProfile> {
    return apiRequest<HealthProfile>('/health-profiles/me');
  },
  upsertMe(payload: HealthProfilePayload): Promise<HealthProfile> {
    return apiRequest<HealthProfile>('/health-profiles/me', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },
  getCompleteness(): Promise<HealthProfileCompleteness> {
    return apiRequest<HealthProfileCompleteness>('/health-profiles/me/completeness');
  },
  getByUser(userId: string): Promise<HealthProfile> {
    return apiRequest<HealthProfile>(`/health-profiles/user/${userId}`);
  },
  create(payload: HealthProfilePayload): Promise<HealthProfile> {
    return apiRequest<HealthProfile>('/health-profiles', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  update(userId: string, payload: HealthProfilePayload): Promise<HealthProfile> {
    return apiRequest<HealthProfile>(`/health-profiles/user/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },
};

/* ==========================================================================
   2. FOODS & ALTERNATIVES API
   ========================================================================== */

export const foodsApi = {
  list(params?: { category?: string; search?: string; limit?: number }): Promise<FoodItem[]> {
    const qs = new URLSearchParams();
    if (params?.category) qs.set('category', params.category);
    if (params?.search) qs.set('search', params.search);
    qs.set('limit', String(params?.limit ?? 100));
    return apiRequest<FoodItem[]>(`/foods?${qs.toString()}`);
  },
  getById(foodId: string): Promise<FoodItem> {
    return apiRequest<FoodItem>(`/foods/${foodId}`);
  },
  getAlternatives(
    foodId: string,
    params?: { limit?: number; dietary_preference?: string | null }
  ): Promise<FoodAlternativeItem[]> {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.dietary_preference) qs.set('dietary_preference', params.dietary_preference);
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return apiRequest<FoodAlternativeItem[]>(`/foods/${foodId}/alternatives${suffix}`);
  },
};

/* ==========================================================================
   3. NUTRITION RECOMMENDATIONS, SUBSTITUTIONS & SAFETY API
   ========================================================================== */

export const nutritionBackendApi = {
  recommendMeal(payload: MealRecommendationRequest): Promise<MealRecommendationResponse> {
    return apiRequest<MealRecommendationResponse>('/nutrition/recommend', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  getToday(targetDate?: string): Promise<DailyRecommendationsResponse> {
    const suffix = targetDate ? `?target_date=${encodeURIComponent(targetDate)}` : '';
    return apiRequest<DailyRecommendationsResponse>(`/nutrition/recommendations/today${suffix}`);
  },
  substituteFood(
    recommendationId: string,
    payload: FoodSubstitutionRequest
  ): Promise<MealRecommendationResponse> {
    return apiRequest<MealRecommendationResponse>(
      `/nutrition/recommendations/${recommendationId}/substitutions`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },
  getSafetyAlerts(): Promise<SafetyAlertsResponse> {
    return apiRequest<SafetyAlertsResponse>('/nutrition/safety-alerts');
  },
  getHistory(userId: string, limit = 20): Promise<Array<{
    id: string;
    meal_type: string;
    algorithm_version: string;
    generated_at: string;
    result: MealRecommendationResponse;
  }>> {
    return apiRequest(`/nutrition/recommendations/user/${userId}?limit=${limit}`);
  },
};

/* ==========================================================================
   4. MEAL DIARY API (Migration 006)
   ========================================================================== */

export const mealDiaryApi = {
  createLog(payload: MealLogCreate): Promise<MealLog> {
    return apiRequest<MealLog>('/nutrition/meal-logs', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  listLogs(params?: {
    date_from?: string;
    date_to?: string;
    meal_type?: MealType;
    page?: number;
    page_size?: number;
  }): Promise<MealLogListResponse> {
    const qs = new URLSearchParams();
    if (params?.date_from) qs.set('date_from', params.date_from);
    if (params?.date_to) qs.set('date_to', params.date_to);
    if (params?.meal_type) qs.set('meal_type', params.meal_type);
    if (params?.page) qs.set('page', String(params.page));
    if (params?.page_size) qs.set('page_size', String(params.page_size));
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return apiRequest<MealLogListResponse>(`/nutrition/meal-logs${suffix}`);
  },
  getLog(logId: string): Promise<MealLog> {
    return apiRequest<MealLog>(`/nutrition/meal-logs/${logId}`);
  },
  updateLog(logId: string, payload: MealLogUpdate): Promise<MealLog> {
    return apiRequest<MealLog>(`/nutrition/meal-logs/${logId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },
  deleteLog(logId: string): Promise<{ message: string; log_id: string }> {
    return apiRequest<{ message: string; log_id: string }>(`/nutrition/meal-logs/${logId}`, {
      method: 'DELETE',
    });
  },
};

/* ==========================================================================
   5. WEIGHT & NUTRITION PROGRESS API (Migration 006)
   ========================================================================== */

export const progressApi = {
  getProgress(params?: { date_from?: string; date_to?: string }): Promise<NutritionProgressResponse> {
    const qs = new URLSearchParams();
    if (params?.date_from) qs.set('date_from', params.date_from);
    if (params?.date_to) qs.set('date_to', params.date_to);
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return apiRequest<NutritionProgressResponse>(`/nutrition/progress${suffix}`);
  },
  listWeights(params?: { date_from?: string; date_to?: string }): Promise<WeightRecord[]> {
    const qs = new URLSearchParams();
    if (params?.date_from) qs.set('date_from', params.date_from);
    if (params?.date_to) qs.set('date_to', params.date_to);
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return apiRequest<WeightRecord[]>(`/nutrition/progress/weight${suffix}`);
  },
  logWeight(payload: WeightRecordCreate): Promise<WeightRecord> {
    return apiRequest<WeightRecord>('/nutrition/progress/weight', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

/**
 * Tính tổng natri cho một bữa ăn.
 * Lưu ý: `sodium_mg` trả về từ Backend trong RecommendedFoodItem ĐÃ được nhân sẵn `serving_multiplier`.
 */
export function sumMealSodium(items: RecommendedFoodItem[]): number {
  return Math.round(
    items.reduce((acc, it) => acc + (it.sodium_mg ?? 0), 0)
  );
}

/**
 * Mock/Adapter cho nguồn trích dẫn RAG (chờ endpoint /nutrition/explain từ nhánh AI ở đợt sau).
 */
export const VERIFIED_RAG_REFERENCES: RagReferenceItem[] = [
  {
    kb_id: 'K001',
    source_id: 'M001',
    title: 'ADA Standards of Care in Diabetes — Section 5: Facilitating Positive Health Behaviors',
    organization: 'American Diabetes Association (ADA)',
    year: 2024,
    excerpt: 'Kế hoạch dinh dưỡng cần được cá thể hóa theo sở thích, mục tiêu chuyển hóa và tình trạng bệnh lý.',
    url: 'https://diabetesjournals.org/care/issue/49/Supplement_1',
  },
  {
    kb_id: 'K003',
    source_id: 'M001',
    title: 'ADA Standards of Care in Diabetes — Dietary Fiber & Whole Foods',
    organization: 'American Diabetes Association (ADA)',
    year: 2024,
    excerpt: 'Khuyến khích bổ sung chất xơ (tối thiểu 14g/1000 kcal) từ rau xanh, ngũ cốc nguyên hạt và thực phẩm ít qua chế biến.',
    url: 'https://diabetesjournals.org/care/issue/49/Supplement_1',
  },
  {
    kb_id: 'K014',
    source_id: 'M004',
    title: 'Hướng dẫn chẩn đoán và điều trị đái tháo đường típ 2 (QĐ 5481/QĐ-BYT)',
    organization: 'Bộ Y tế Việt Nam',
    year: 2020,
    excerpt: 'Ưu tiên thực phẩm có chỉ số đường huyết (GI) thấp (<= 55) và kiểm soát tải lượng đường huyết (GL) trong mỗi bữa.',
    url: 'https://bvcdn.org.vn/wp-content/uploads/2024/12/5481-qd-byt-huong-dan-chan-doan-va-dieu-tri-dai-thao-duong-tip-2_11120219.pdf',
  },
  {
    kb_id: 'K025',
    source_id: 'M001',
    title: 'ADA Standards of Care in Diabetes — Sodium & Hypertension Management',
    organization: 'American Diabetes Association (ADA)',
    year: 2024,
    excerpt: 'Người bệnh đái tháo đường có tăng huyết áp cần giới hạn lượng natri dưới 2.000–2.300 mg/ngày.',
    url: 'https://diabetesjournals.org/care/issue/49/Supplement_1',
  },
];
