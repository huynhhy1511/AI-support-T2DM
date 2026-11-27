import uuid
from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

MealType = Literal["breakfast", "lunch", "dinner", "snack"]


class NutritionTarget(BaseModel):
    target_energy_kcal: Optional[float] = Field(None, gt=0, le=2500, description="Mục tiêu calo cho bữa ăn (nếu có)")
    target_carbohydrate_g: Optional[float] = Field(None, ge=0, le=150, description="Mục tiêu carbohydrate cho bữa ăn (nếu có)")
    max_carbohydrate_g: Optional[float] = Field(None, ge=10, le=120, description="Giới hạn tối đa carbohydrate cho bữa ăn")


class MealRecommendationRequest(BaseModel):
    user_id: uuid.UUID
    meal_type: MealType
    dietary_preference: Optional[str] = Field(None, max_length=100, description="Sở thích hoặc chế độ ăn (ví dụ: 'vegetarian', 'low_carb', 'low_sodium')")
    excluded_food_ids: Optional[List[uuid.UUID]] = Field(default=None, description="Danh sách ID thực phẩm muốn loại trừ")
    excluded_keywords: Optional[List[str]] = Field(default=None, description="Từ khóa thực phẩm kiêng hoặc dị ứng (ví dụ: 'tôm', 'đậu phộng')")
    excluded_allergens: Optional[List[str]] = Field(default=None, description="Danh sách mã hoặc tên dị ứng chuẩn hóa (ví dụ: 'shellfish', 'soy', 'egg')")
    custom_target: Optional[NutritionTarget] = Field(None, description="Mục tiêu dinh dưỡng cụ thể do người dùng cung cấp nếu có cơ sở phù hợp")


class RecommendedFoodItem(BaseModel):
    food_id: uuid.UUID
    food_name: str
    category: str
    serving_size_g: float
    serving_multiplier: float = 1.0
    energy_kcal: float
    carbohydrate_g: float
    protein_g: float
    fat_g: float
    fiber_g: Optional[float] = 0.0
    sugar_g: Optional[float] = 0.0
    glycemic_index: Optional[float] = None
    glycemic_load: Optional[float] = None
    sodium_mg: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    score: float
    reasons: List[str]
    item_warning: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MealRecommendationResponse(BaseModel):
    recommendation_id: uuid.UUID
    user_id: uuid.UUID
    meal_type: str
    status: Literal["generated", "abstained"] = "generated"
    reason_code: Optional[str] = None
    algorithm_version: str
    generated_at: datetime
    items: List[RecommendedFoodItem]
    total_energy_kcal: float
    total_carbohydrate_g: float
    total_protein_g: float
    total_fat_g: float
    total_fiber_g: float
    total_sodium_mg: Optional[float] = None
    total_saturated_fat_g: Optional[float] = None
    meal_balance_evaluation: str
    safety_notes: List[str]
    clinical_safety_disclaimer: str

    model_config = ConfigDict(from_attributes=True)


class FoodSubstitutionRequest(BaseModel):
    original_food_id: uuid.UUID
    replacement_food_id: uuid.UUID
    serving_g: Optional[float] = Field(
        None, gt=0, le=2000, description="Khẩu phần thay thế mong muốn tính theo gram (tùy chọn)"
    )


class DailyNutritionSummary(BaseModel):
    total_energy_kcal: float = 0.0
    total_carbohydrate_g: float = 0.0
    total_protein_g: float = 0.0
    total_fat_g: float = 0.0
    total_fiber_g: float = 0.0
    total_sodium_mg: float = 0.0
    total_saturated_fat_g: float = 0.0
    meals_count: int = 0


class DailyRecommendationsResponse(BaseModel):
    date: date
    user_id: uuid.UUID
    meals: List[MealRecommendationResponse]
    daily_summary: DailyNutritionSummary


class SafetyAlertSchema(BaseModel):
    code: str
    level: Literal["info", "warning", "error", "critical"]
    title: str
    message: str
    action_guidance: str
    details: List[str] = Field(default_factory=list)


class SafetyAlertsResponse(BaseModel):
    user_id: uuid.UUID
    has_blocking_condition: bool
    is_profile_complete: bool
    bmi: Optional[float] = None
    bmi_category: Optional[str] = None
    target_energy_kcal: Optional[float] = None
    alerts: List[SafetyAlertSchema]

