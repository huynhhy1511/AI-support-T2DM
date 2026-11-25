import uuid
from datetime import datetime
from typing import Dict, List, Literal, Optional

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
    allergies: Optional[List[str]] = Field(default=None, description="Danh sách dị ứng thực phẩm của người dùng")
    comorbidities: Optional[List[str]] = Field(default=None, description="Bệnh đồng mắc (ví dụ: 'hypertension', 'ckd')")
    nutrition_goal: Optional[str] = Field(default=None, max_length=100, description="Mục tiêu dinh dưỡng (ví dụ: 'weight_loss', 'glucose_control')")
    require_complete_profile: bool = Field(default=False, description="Từ chối cá thể hóa nếu hồ sơ thiếu thông tin cơ bản")
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
    sodium_mg: Optional[float] = 0.0
    glycemic_index: Optional[float] = None
    glycemic_load: Optional[float] = None
    score: float
    reasons: List[str]
    item_warning: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MealRecommendationResponse(BaseModel):
    recommendation_id: uuid.UUID
    user_id: uuid.UUID
    meal_type: str
    algorithm_version: str
    generated_at: datetime
    items: List[RecommendedFoodItem]
    total_energy_kcal: float
    total_carbohydrate_g: float
    total_protein_g: float
    total_fat_g: float
    total_fiber_g: float
    total_sodium_mg: float = 0.0
    meal_balance_evaluation: str
    safety_notes: List[str]
    is_abstained: bool = False
    abstention_reason: Optional[str] = None
    missing_profile_fields: List[str] = Field(default_factory=list)
    clinical_safety_disclaimer: str

    model_config = ConfigDict(from_attributes=True)


class DailyMealPlanRequest(BaseModel):
    user_id: uuid.UUID
    dietary_preference: Optional[str] = Field(None, max_length=100)
    excluded_food_ids: Optional[List[uuid.UUID]] = Field(default=None)
    excluded_keywords: Optional[List[str]] = Field(default=None)
    allergies: Optional[List[str]] = Field(default=None)
    comorbidities: Optional[List[str]] = Field(default=None)
    nutrition_goal: Optional[str] = Field(default=None, max_length=100)
    require_complete_profile: bool = Field(default=False)


class DailyMealPlanResponse(BaseModel):
    plan_id: uuid.UUID
    user_id: uuid.UUID
    algorithm_version: str
    generated_at: datetime
    meals: Dict[str, MealRecommendationResponse]
    daily_total_energy_kcal: float
    daily_total_carbohydrate_g: float
    daily_total_protein_g: float
    daily_total_fat_g: float
    daily_total_fiber_g: float
    daily_total_sodium_mg: float
    macro_distribution_pct: Dict[str, float]
    safety_notes: List[str]
    is_abstained: bool = False
    abstention_reason: Optional[str] = None
    missing_profile_fields: List[str] = Field(default_factory=list)
    clinical_safety_disclaimer: str


class FoodSubstitutionRequest(BaseModel):
    user_id: uuid.UUID
    food_id_to_replace: uuid.UUID
    meal_type: MealType = "lunch"
    dietary_preference: Optional[str] = Field(None, max_length=100)
    excluded_food_ids: Optional[List[uuid.UUID]] = Field(default=None)
    excluded_keywords: Optional[List[str]] = Field(default=None)
    allergies: Optional[List[str]] = Field(default=None)
    comorbidities: Optional[List[str]] = Field(default=None)
    limit: int = Field(default=3, ge=1, le=10)


class FoodSubstitutionResponse(BaseModel):
    original_food_id: uuid.UUID
    original_food_name: str
    category: str
    substitutes: List[RecommendedFoodItem]
    message: str
