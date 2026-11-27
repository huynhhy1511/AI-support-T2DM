import uuid
from datetime import date, datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.nutrition import MealType

MealLogStatusType = Literal["eaten", "partially_eaten", "skipped", "eaten_other"]


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


class MealLogItemCreate(BaseModel):
    food_id: Optional[uuid.UUID] = None
    custom_food_name: Optional[str] = Field(None, max_length=200)
    serving_g: float = Field(..., gt=0, le=5000)
    # Optional nutritional values when logging a custom food without food_id
    calories_kcal: Optional[float] = Field(None, ge=0)
    carbs_g: Optional[float] = Field(None, ge=0)
    protein_g: Optional[float] = Field(None, ge=0)
    fat_g: Optional[float] = Field(None, ge=0)
    fiber_g: Optional[float] = Field(None, ge=0)
    sodium_mg: Optional[float] = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_food_reference(self) -> "MealLogItemCreate":
        if self.food_id is None and not (
            self.custom_food_name and self.custom_food_name.strip()
        ):
            raise ValueError(
                "Either food_id or custom_food_name must be provided for a meal log item."
            )
        return self


class MealLogItemResponse(BaseModel):
    id: uuid.UUID
    food_id: Optional[uuid.UUID] = None
    food_name: Optional[str] = None
    custom_food_name: Optional[str] = None
    serving_g: float
    calories_kcal: float
    carbs_g: float
    protein_g: float
    fat_g: float
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ActualNutritionSummary(BaseModel):
    calories_kcal: float = 0.0
    carbs_g: float = 0.0
    protein_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None


class MealLogCreate(BaseModel):
    recommendation_id: Optional[uuid.UUID] = None
    meal_date: date = Field(default_factory=_today_utc)
    meal_type: MealType
    status: MealLogStatusType
    notes: Optional[str] = None
    items: List[MealLogItemCreate] = Field(default_factory=list)


class MealLogUpdate(BaseModel):
    status: Optional[MealLogStatusType] = None
    notes: Optional[str] = None
    items: Optional[List[MealLogItemCreate]] = None


class MealLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    recommendation_id: Optional[uuid.UUID] = None
    meal_date: date
    meal_type: str
    status: str
    notes: Optional[str] = None
    items: List[MealLogItemResponse]
    actual_nutrition: ActualNutritionSummary
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MealLogListResponse(BaseModel):
    items: List[MealLogResponse]
    total: int
    page: int
    page_size: int


class WeightRecordCreate(BaseModel):
    weight_kg: float = Field(..., gt=0, le=500)
    recorded_at: date = Field(default_factory=_today_utc)


class WeightRecordResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    weight_kg: float
    recorded_at: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProgressPeriod(BaseModel):
    date_from: date
    date_to: date


class ProgressSummary(BaseModel):
    total_meals_logged: int = 0
    total_meals_skipped: int = 0
    meal_logging_rate: float = 0.0


class NutritionTrendPoint(BaseModel):
    date: date
    planned_calories_kcal: float = 0.0
    actual_calories_kcal: float = 0.0
    planned_carbs_g: float = 0.0
    actual_carbs_g: float = 0.0


class WeightProgressSummary(BaseModel):
    latest_kg: Optional[float] = None
    previous_kg: Optional[float] = None
    records: List[WeightRecordResponse] = Field(default_factory=list)


class NutritionProgressResponse(BaseModel):
    period: ProgressPeriod
    summary: ProgressSummary
    nutrition_trends: List[NutritionTrendPoint]
    weight: WeightProgressSummary
