import { getStoredToken } from './api';
import type {
  DailyMealPlan,
  FoodItem,
  HealthProfile,
  HealthProfilePayload,
  LocalClinicalPreferences,
  MealDiaryEntry,
  MealRecommendationRequest,
  MealRecommendationResponse,
  MealType,
  RagReferenceItem,
  RecommendedFoodItem,
  WeightLogEntry,
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
   1. REAL BACKEND API ADAPTERS (Kết nối trực tiếp FastAPI trên nhánh main)
   ========================================================================== */

export const healthProfileApi = {
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
};

export const nutritionBackendApi = {
  recommendMeal(payload: MealRecommendationRequest): Promise<MealRecommendationResponse> {
    return apiRequest<MealRecommendationResponse>('/nutrition/recommend', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
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
   2. LOCALSTORAGE ADAPTERS CHO CÁC PHẦN CHƯA CÓ ENDPOINT RIÊNG TRÊN MAIN
   (Nhật ký ăn uống, sở thích lâm sàng mở rộng, kế hoạch theo ngày, lịch sử cân nặng)
   ========================================================================== */

const keyFor = (prefix: string, userId: string) => `dc_${prefix}_${userId}`;

export const localPrefsAdapter = {
  get(userId: string): LocalClinicalPreferences {
    try {
      const raw = localStorage.getItem(keyFor('clinical_prefs', userId));
      if (raw) return JSON.parse(raw) as LocalClinicalPreferences;
    } catch {
      // ignore
    }
    return {
      nutrition_goal: 'maintenance',
      comorbidities: ['Type 2 Diabetes'],
      allergies: [],
    };
  },
  save(userId: string, prefs: LocalClinicalPreferences): void {
    localStorage.setItem(keyFor('clinical_prefs', userId), JSON.stringify(prefs));
  },
};

export const mealPlanStorage = {
  getByDate(userId: string, date: string): DailyMealPlan | null {
    try {
      const raw = localStorage.getItem(keyFor(`plan_${date}`, userId));
      return raw ? (JSON.parse(raw) as DailyMealPlan) : null;
    } catch {
      return null;
    }
  },
  save(userId: string, plan: DailyMealPlan): void {
    localStorage.setItem(keyFor(`plan_${plan.date}`, userId), JSON.stringify(plan));
  },
};

export const foodDiaryStorage = {
  getByDate(userId: string, date: string): Record<MealType, MealDiaryEntry> | null {
    try {
      const raw = localStorage.getItem(keyFor(`diary_${date}`, userId));
      return raw ? (JSON.parse(raw) as Record<MealType, MealDiaryEntry>) : null;
    } catch {
      return null;
    }
  },
  saveByDate(userId: string, date: string, entries: Record<MealType, MealDiaryEntry>): void {
    localStorage.setItem(keyFor(`diary_${date}`, userId), JSON.stringify(entries));
  },
  listDates(userId: string): string[] {
    const prefix = `dc_diary_`;
    const suffix = `_${userId}`;
    const dates: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith(prefix) && k.endsWith(suffix)) {
        dates.push(k.slice(prefix.length, k.length - suffix.length));
      }
    }
    return dates.sort();
  },
};

export const weightHistoryStorage = {
  getAll(userId: string): WeightLogEntry[] {
    try {
      const raw = localStorage.getItem(keyFor('weights', userId));
      return raw ? (JSON.parse(raw) as WeightLogEntry[]) : [];
    } catch {
      return [];
    }
  },
  addEntry(userId: string, entry: WeightLogEntry): void {
    const list = this.getAll(userId).filter((e) => e.date !== entry.date);
    list.push(entry);
    list.sort((a, b) => a.date.localeCompare(b.date));
    localStorage.setItem(keyFor('weights', userId), JSON.stringify(list));
  },
};

/** Tính tổng natri cho một bữa ăn (từ các món có sodium_mg xác thực) */
export function sumMealSodium(items: RecommendedFoodItem[]): number {
  return Math.round(
    items.reduce((acc, it) => acc + (it.sodium_mg ?? 0) * it.serving_multiplier, 0)
  );
}

/**
 * Tính nhu cầu năng lượng tham khảo hiển thị (khi backend chưa trả về target_kcal trực tiếp).
 * Frontend KHÔNG ghi đè số liệu dinh dưỡng của từng món từ backend.
 */
export function estimateReferenceDailyKcal(
  profile: HealthProfile | null,
  goal: 'weight_loss' | 'maintenance'
): number | null {
  if (
    !profile ||
    !profile.date_of_birth ||
    !profile.sex ||
    !profile.height_cm ||
    !profile.weight_kg ||
    !profile.activity_level
  ) {
    return null;
  }
  const dob = new Date(profile.date_of_birth);
  const now = new Date();
  let age = now.getFullYear() - dob.getFullYear();
  if (
    now.getMonth() < dob.getMonth() ||
    (now.getMonth() === dob.getMonth() && now.getDate() < dob.getDate())
  ) {
    age -= 1;
  }
  const w = Number(profile.weight_kg);
  const h = Number(profile.height_cm);
  const bmr =
    profile.sex === 'male'
      ? 10 * w + 6.25 * h - 5 * age + 5
      : 10 * w + 6.25 * h - 5 * age - 161;
  const factors: Record<string, number> = {
    sedentary: 1.2,
    light: 1.375,
    moderate: 1.55,
    active: 1.725,
    very_active: 1.9,
  };
  const tdee = bmr * (factors[profile.activity_level] ?? 1.2);
  const floor = profile.sex === 'male' ? 1400 : 1200;
  if (goal === 'weight_loss') {
    return Math.round(Math.max(floor, tdee - 400));
  }
  return Math.round(Math.max(floor, tdee));
}

/**
 * Mock/Adapter cho nguồn trích dẫn RAG (dùng khi nhánh main chưa ghép endpoint /nutrition/explain).
 * Các nguồn trích dẫn tuân thủ đúng danh mục nguồn đã xác minh (ADA 2024, Bộ Y tế QĐ 5481/QĐ-BYT, WHO 2020).
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
