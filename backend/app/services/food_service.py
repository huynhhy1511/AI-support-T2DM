import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.allergen import Allergen
from app.models.food import Food
from app.schemas.food import FoodAlternativeResponse, FoodCreate, FoodResponse, FoodUpdate


def _resolve_allergens_by_codes(db: Session, codes: Optional[List[str]]) -> List[Allergen]:
    if not codes:
        return []
    normalized = [c.strip().lower() for c in codes if c and c.strip()]
    if not normalized:
        return []
    stmt = select(Allergen).where(Allergen.code.in_(normalized))
    return list(db.scalars(stmt).all())


def get_food_by_id(db: Session, food_id: uuid.UUID) -> Optional[Food]:
    """Retrieve food item by UUID."""
    stmt = select(Food).where(Food.id == food_id)
    return db.scalars(stmt).first()


def get_food_by_name(db: Session, name: str) -> Optional[Food]:
    """Retrieve food item by name."""
    stmt = select(Food).where(Food.name.ilike(name.strip()))
    return db.scalars(stmt).first()


def list_foods(
    db: Session,
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_test_data: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Food]:
    """List food items with optional filtering and pagination."""
    stmt = select(Food)
    if category:
        stmt = stmt.where(Food.category == category)
    if search:
        stmt = stmt.where(Food.name.ilike(f"%{search.strip()}%"))
    if is_test_data is not None:
        stmt = stmt.where(Food.is_test_data == is_test_data)

    stmt = stmt.order_by(Food.category, Food.name).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def create_food(db: Session, food_in: FoodCreate) -> Food:
    """Create a new food item in the database."""
    allergens = _resolve_allergens_by_codes(db, food_in.allergen_codes)
    food = Food(
        name=food_in.name.strip(),
        category=food_in.category,
        serving_size_g=food_in.serving_size_g,
        energy_kcal=food_in.energy_kcal,
        carbohydrate_g=food_in.carbohydrate_g,
        protein_g=food_in.protein_g,
        fat_g=food_in.fat_g,
        fiber_g=food_in.fiber_g or Decimal("0.00"),
        sugar_g=food_in.sugar_g or Decimal("0.00"),
        glycemic_index=food_in.glycemic_index,
        glycemic_load=food_in.glycemic_load,
        sodium_mg=food_in.sodium_mg,
        saturated_fat_g=food_in.saturated_fat_g,
        preparation_state=food_in.preparation_state,
        data_source=food_in.data_source,
        data_version=food_in.data_version,
        is_test_data=food_in.is_test_data,
        source_name=food_in.source_name,
        source_url=food_in.source_url,
        allergens=allergens,
    )
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


def update_food(db: Session, food_id: uuid.UUID, food_in: FoodUpdate) -> Optional[Food]:
    """Update existing food item."""
    food = get_food_by_id(db, food_id)
    if not food:
        return None

    update_data = food_in.model_dump(exclude_unset=True)
    allergen_codes = update_data.pop("allergen_codes", None)
    for field, value in update_data.items():
        setattr(food, field, value)

    if allergen_codes is not None:
        food.allergens = _resolve_allergens_by_codes(db, allergen_codes)

    db.commit()
    db.refresh(food)
    return food


def delete_food(db: Session, food_id: uuid.UUID) -> bool:
    """Delete a food item."""
    food = get_food_by_id(db, food_id)
    if not food:
        return False
    db.delete(food)
    db.commit()
    return True


def get_food_alternatives(
    db: Session,
    food_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 5,
    dietary_preference: Optional[str] = None,
) -> Optional[List[FoodAlternativeResponse]]:
    """Find safe same-category alternative foods filtered by user allergies/diet and ranked by Kcal & GI closeness."""
    from app.schemas.nutrition import MealRecommendationRequest
    from app.services.health_profile_service import get_profile_by_user_id
    from app.services.nutrition_engine import ConstraintEngine

    original = get_food_by_id(db, food_id)
    if not original:
        return None

    health_profile = get_profile_by_user_id(db, user_id)
    effective_pref = dietary_preference or (
        health_profile.dietary_preference if health_profile else None
    )
    profile_allergies = (
        list(health_profile.allergies or []) if health_profile else []
    )

    stmt = (
        select(Food)
        .where(Food.category == original.category, Food.id != original.id)
        .order_by(Food.name)
    )
    same_category_foods = list(db.scalars(stmt).all())

    filter_request = MealRecommendationRequest(
        user_id=user_id,
        meal_type="lunch",
        dietary_preference=effective_pref,
        excluded_food_ids=[original.id],
        excluded_allergens=profile_allergies or None,
    )
    safe_candidates = ConstraintEngine.filter_foods(
        foods=same_category_foods,
        request=filter_request,
        health_profile=health_profile,
    )

    orig_kcal = float(original.energy_kcal)
    orig_gi = float(original.glycemic_index) if original.glycemic_index is not None else None

    def _rank_key(cand: Food) -> tuple:
        cand_kcal = float(cand.energy_kcal)
        kcal_gap = abs(cand_kcal - orig_kcal)
        cand_gi = float(cand.glycemic_index) if cand.glycemic_index is not None else None

        if orig_gi is not None and cand_gi is not None:
            # Prefer lower or equal GI; penalize higher GI more strongly
            gi_penalty = (cand_gi - orig_gi) * 3.0 if cand_gi > orig_gi else abs(cand_gi - orig_gi) * 0.5
        else:
            gi_penalty = 0.0
        return (round(gi_penalty + kcal_gap, 2), round(kcal_gap, 2), cand.name)

    ranked = sorted(safe_candidates, key=_rank_key)[:limit]

    results: List[FoodAlternativeResponse] = []
    for cand in ranked:
        kcal_diff = round(float(cand.energy_kcal) - orig_kcal, 1)
        cand_gi = float(cand.glycemic_index) if cand.glycemic_index is not None else None
        gi_diff = (
            round(cand_gi - orig_gi, 1)
            if orig_gi is not None and cand_gi is not None
            else None
        )

        kcal_sign = "+" if kcal_diff > 0 else ""
        parts = [f"Cùng nhóm {original.category}, chênh lệch năng lượng {kcal_sign}{kcal_diff:.1f} kcal"]
        if gi_diff is not None:
            if gi_diff < 0:
                parts.append(f"GI thấp hơn {abs(gi_diff):.0f} điểm (tốt cho kiểm soát đường huyết)")
            elif gi_diff == 0:
                parts.append("GI tương đương")
            else:
                parts.append(f"GI cao hơn +{gi_diff:.0f} điểm")
        else:
            parts.append("an toàn theo ràng buộc dị ứng & chế độ ăn")

        base_data = FoodResponse.model_validate(cand).model_dump()
        results.append(
            FoodAlternativeResponse(
                **base_data,
                kcal_diff=kcal_diff,
                gi_diff=gi_diff,
                similarity_reason="; ".join(parts),
            )
        )

    return results


SAMPLE_TEST_FOODS = [
    # Staples (Tinh bột)
    {
        "name": "Gạo lứt nấu chín (Cooked Brown Rice)",
        "category": "staple",
        "serving_size_g": Decimal("150.00"),
        "energy_kcal": Decimal("168.00"),
        "carbohydrate_g": Decimal("35.00"),
        "protein_g": Decimal("3.80"),
        "fat_g": Decimal("1.40"),
        "fiber_g": Decimal("2.80"),
        "sugar_g": Decimal("0.20"),
        "glycemic_index": Decimal("55.00"),
        "glycemic_load": Decimal("19.25"),
        "sodium_mg": 5.0,
        "saturated_fat_g": 0.3,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    {
        "name": "Yến mạch cán dẹt nấu chín (Rolled Oats)",
        "category": "staple",
        "serving_size_g": Decimal("150.00"),
        "energy_kcal": Decimal("110.00"),
        "carbohydrate_g": Decimal("19.00"),
        "protein_g": Decimal("4.00"),
        "fat_g": Decimal("2.00"),
        "fiber_g": Decimal("3.00"),
        "sugar_g": Decimal("0.50"),
        "glycemic_index": Decimal("55.00"),
        "glycemic_load": Decimal("10.45"),
        "sodium_mg": 3.0,
        "saturated_fat_g": 0.4,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    {
        "name": "Khoai lang luộc (Boiled Sweet Potato)",
        "category": "staple",
        "serving_size_g": Decimal("120.00"),
        "energy_kcal": Decimal("103.00"),
        "carbohydrate_g": Decimal("24.00"),
        "protein_g": Decimal("2.00"),
        "fat_g": Decimal("0.20"),
        "fiber_g": Decimal("3.60"),
        "sugar_g": Decimal("5.00"),
        "glycemic_index": Decimal("54.00"),
        "glycemic_load": Decimal("12.96"),
        "sodium_mg": 32.0,
        "saturated_fat_g": 0.05,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    {
        "name": "Cơm trắng nấu chín (Cooked White Rice)",
        "category": "staple",
        "serving_size_g": Decimal("150.00"),
        "energy_kcal": Decimal("195.00"),
        "carbohydrate_g": Decimal("43.00"),
        "protein_g": Decimal("4.10"),
        "fat_g": Decimal("0.40"),
        "fiber_g": Decimal("0.60"),
        "sugar_g": Decimal("0.10"),
        "glycemic_index": Decimal("73.00"),
        "glycemic_load": Decimal("31.39"),
        "sodium_mg": 2.0,
        "saturated_fat_g": 0.1,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    # Protein (Đạm)
    {
        "name": "Ức gà phi lê áp chảo (Skinless Chicken Breast)",
        "category": "protein",
        "serving_size_g": Decimal("100.00"),
        "energy_kcal": Decimal("165.00"),
        "carbohydrate_g": Decimal("0.00"),
        "protein_g": Decimal("31.00"),
        "fat_g": Decimal("3.60"),
        "fiber_g": Decimal("0.00"),
        "sugar_g": Decimal("0.00"),
        "glycemic_index": None,
        "glycemic_load": None,
        "sodium_mg": 74.0,
        "saturated_fat_g": 1.0,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    {
        "name": "Cá hồi áp chảo (Pan-seared Salmon)",
        "category": "protein",
        "serving_size_g": Decimal("100.00"),
        "energy_kcal": Decimal("206.00"),
        "carbohydrate_g": Decimal("0.00"),
        "protein_g": Decimal("22.00"),
        "fat_g": Decimal("12.00"),
        "fiber_g": Decimal("0.00"),
        "sugar_g": Decimal("0.00"),
        "glycemic_index": None,
        "glycemic_load": None,
        "sodium_mg": 59.0,
        "saturated_fat_g": 2.5,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    {
        "name": "Đậu phụ trắng hấp (Steamed Tofu)",
        "category": "protein",
        "serving_size_g": Decimal("120.00"),
        "energy_kcal": Decimal("91.00"),
        "carbohydrate_g": Decimal("2.30"),
        "protein_g": Decimal("9.70"),
        "fat_g": Decimal("5.10"),
        "fiber_g": Decimal("1.40"),
        "sugar_g": Decimal("0.60"),
        "glycemic_index": Decimal("15.00"),
        "glycemic_load": Decimal("0.35"),
        "sodium_mg": 8.0,
        "saturated_fat_g": 0.7,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    {
        "name": "Trứng gà luộc (Boiled Egg)",
        "category": "protein",
        "serving_size_g": Decimal("60.00"),
        "energy_kcal": Decimal("78.00"),
        "carbohydrate_g": Decimal("0.60"),
        "protein_g": Decimal("6.30"),
        "fat_g": Decimal("5.30"),
        "fiber_g": Decimal("0.00"),
        "sugar_g": Decimal("0.60"),
        "glycemic_index": None,
        "glycemic_load": None,
        "sodium_mg": 62.0,
        "saturated_fat_g": 1.6,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    # Vegetables (Rau củ)
    {
        "name": "Bông cải xanh luộc (Boiled Broccoli)",
        "category": "vegetables",
        "serving_size_g": Decimal("150.00"),
        "energy_kcal": Decimal("52.00"),
        "carbohydrate_g": Decimal("10.50"),
        "protein_g": Decimal("3.60"),
        "fat_g": Decimal("0.60"),
        "fiber_g": Decimal("3.90"),
        "sugar_g": Decimal("2.10"),
        "glycemic_index": Decimal("15.00"),
        "glycemic_load": Decimal("1.58"),
        "sodium_mg": 49.0,
        "saturated_fat_g": 0.1,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    {
        "name": "Rau muống luộc (Boiled Water Spinach)",
        "category": "vegetables",
        "serving_size_g": Decimal("150.00"),
        "energy_kcal": Decimal("30.00"),
        "carbohydrate_g": Decimal("4.20"),
        "protein_g": Decimal("3.90"),
        "fat_g": Decimal("0.50"),
        "fiber_g": Decimal("3.00"),
        "sugar_g": Decimal("0.50"),
        "glycemic_index": Decimal("15.00"),
        "glycemic_load": Decimal("0.63"),
        "sodium_mg": 169.0,
        "saturated_fat_g": 0.1,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    {
        "name": "Dưa chuột tươi (Fresh Cucumber)",
        "category": "vegetables",
        "serving_size_g": Decimal("100.00"),
        "energy_kcal": Decimal("15.00"),
        "carbohydrate_g": Decimal("3.60"),
        "protein_g": Decimal("0.70"),
        "fat_g": Decimal("0.10"),
        "fiber_g": Decimal("0.50"),
        "sugar_g": Decimal("1.70"),
        "glycemic_index": Decimal("15.00"),
        "glycemic_load": Decimal("0.54"),
        "sodium_mg": 2.0,
        "saturated_fat_g": 0.03,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    # Fruits & Dairy & Snacks
    {
        "name": "Táo tươi để vỏ (Fresh Apple with skin)",
        "category": "fruits",
        "serving_size_g": Decimal("120.00"),
        "energy_kcal": Decimal("62.00"),
        "carbohydrate_g": Decimal("16.50"),
        "protein_g": Decimal("0.30"),
        "fat_g": Decimal("0.20"),
        "fiber_g": Decimal("2.90"),
        "sugar_g": Decimal("12.40"),
        "glycemic_index": Decimal("36.00"),
        "glycemic_load": Decimal("5.94"),
        "sodium_mg": 1.0,
        "saturated_fat_g": 0.03,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    {
        "name": "Sữa chua không đường (Plain Greek Yogurt)",
        "category": "dairy",
        "serving_size_g": Decimal("125.00"),
        "energy_kcal": Decimal("74.00"),
        "carbohydrate_g": Decimal("4.50"),
        "protein_g": Decimal("12.00"),
        "fat_g": Decimal("0.50"),
        "fiber_g": Decimal("0.00"),
        "sugar_g": Decimal("4.00"),
        "glycemic_index": Decimal("12.00"),
        "glycemic_load": Decimal("0.54"),
        "sodium_mg": 45.0,
        "saturated_fat_g": 0.3,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
    {
        "name": "Hạt hạnh nhân sấy mộc (Roasted Almonds)",
        "category": "snack",
        "serving_size_g": Decimal("28.00"),
        "energy_kcal": Decimal("164.00"),
        "carbohydrate_g": Decimal("6.10"),
        "protein_g": Decimal("6.00"),
        "fat_g": Decimal("14.20"),
        "fiber_g": Decimal("3.50"),
        "sugar_g": Decimal("1.20"),
        "glycemic_index": None,
        "glycemic_load": None,
        "sodium_mg": 1.0,
        "saturated_fat_g": 1.1,
        "is_test_data": True,
        "source_name": "Test Dataset (Tham khảo Viện Dinh Dưỡng & USDA)",
        "source_url": "https://fdc.nal.usda.gov/",
    },
]


def seed_sample_foods_if_empty(db: Session) -> int:
    """Seed sample test foods into the database if table is empty. Returns count added."""
    count = db.query(Food).count()
    if count > 0:
        return 0

    added = 0
    for item in SAMPLE_TEST_FOODS:
        food = Food(**item)
        db.add(food)
        added += 1

    db.commit()
    return added

