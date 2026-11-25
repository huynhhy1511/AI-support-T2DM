import uuid
from decimal import Decimal

from app.models.food import Food
from app.models.health_profile import HealthProfile
from app.schemas.nutrition import (
    MealRecommendationRequest,
    NutritionTarget,
)
from app.services.nutrition_engine import (
    ConstraintEngine,
    MealComposer,
    NutritionScoringEngine,
    ScoringConfig,
)


def _make_dummy_food(
    name: str,
    category: str,
    carb: float,
    protein: float,
    fat: float,
    fiber: float = 0.0,
    sugar: float = 0.0,
    gi: float = None,
    gl: float = None,
) -> Food:
    return Food(
        id=uuid.uuid4(),
        name=name,
        category=category,
        serving_size_g=Decimal("100.00"),
        energy_kcal=Decimal(str(carb * 4 + protein * 4 + fat * 9)),
        carbohydrate_g=Decimal(str(carb)),
        protein_g=Decimal(str(protein)),
        fat_g=Decimal(str(fat)),
        fiber_g=Decimal(str(fiber)),
        sugar_g=Decimal(str(sugar)),
        glycemic_index=Decimal(str(gi)) if gi is not None else None,
        glycemic_load=Decimal(str(gl)) if gl is not None else None,
        is_test_data=True,
    )


def test_scoring_engine_fiber_and_gi():
    """Verify that fiber and low GI increase the food score."""
    low_gi_high_fiber_food = _make_dummy_food(
        name="Brown Rice",
        category="staple",
        carb=30.0,
        protein=4.0,
        fat=1.0,
        fiber=4.0,  # +12 pts
        gi=50.0,     # +15 pts
        gl=15.0,     # 0 pts
    )
    score, reasons, warning = NutritionScoringEngine.score_item(low_gi_high_fiber_food)
    # base 50 + 12 (fiber) + 15 (low gi) = 77
    assert score >= 75.0
    assert any("Chất xơ cao" in r for r in reasons)
    assert any("Chỉ số đường huyết thấp" in r for r in reasons)
    assert warning is None


def test_scoring_engine_high_gi_penalty():
    """Verify high GI food incurs score penalty and warning."""
    high_gi_food = _make_dummy_food(
        name="White Bread",
        category="staple",
        carb=50.0,
        protein=4.0,
        fat=1.0,
        fiber=0.5,
        gi=75.0,  # -20 pts
    )
    score, reasons, warning = NutritionScoringEngine.score_item(high_gi_food)
    assert score < 50.0
    assert any("Chỉ số đường huyết cao" in r for r in reasons)
    assert warning is not None


def test_constraint_engine_exclusions():
    """Verify keyword and ID exclusion rules."""
    food1 = _make_dummy_food("Tôm hấp", "protein", 0, 20, 1)
    food2 = _make_dummy_food("Ức gà luộc", "protein", 0, 25, 2)
    food3 = _make_dummy_food("Đậu phụ sốt cà", "protein", 5, 10, 5)

    request = MealRecommendationRequest(
        user_id=uuid.uuid4(),
        meal_type="lunch",
        excluded_keywords=["tôm"],
        excluded_food_ids=[food2.id],
    )

    filtered = ConstraintEngine.filter_foods(
        foods=[food1, food2, food3],
        request=request,
    )

    assert len(filtered) == 1
    assert filtered[0].name == "Đậu phụ sốt cà"


def test_constraint_engine_vegetarian_preference():
    """Verify vegetarian constraint excludes meats and fish."""
    chicken = _make_dummy_food("Ức gà phi lê", "protein", 0, 30, 3)
    salmon = _make_dummy_food("Cá hồi áp chảo", "protein", 0, 22, 10)
    tofu = _make_dummy_food("Đậu phụ trắng hấp", "protein", 2, 10, 5)

    request = MealRecommendationRequest(
        user_id=uuid.uuid4(),
        meal_type="lunch",
        dietary_preference="vegetarian",
    )

    filtered = ConstraintEngine.filter_foods(
        foods=[chicken, salmon, tofu],
        request=request,
    )

    assert len(filtered) == 1
    assert filtered[0].name == "Đậu phụ trắng hấp"


def test_meal_composer_plate_method_and_safety_disclaimer():
    """Verify meal composer balances staple, protein, and vegetables with clinical disclaimer."""
    staple = _make_dummy_food("Gạo lứt", "staple", 35, 4, 1, fiber=3, gi=55, gl=19)
    protein = _make_dummy_food("Ức gà", "protein", 0, 30, 3)
    veg = _make_dummy_food("Bông cải xanh", "vegetables", 8, 3, 0.5, fiber=3.5, gi=15)

    items, meal_eval, safety_notes = MealComposer.compose(
        candidate_foods=[staple, protein, veg],
        meal_type="lunch",
    )

    assert len(items) >= 3
    categories = [i.category for i in items]
    assert "staple" in categories
    assert "protein" in categories
    assert "vegetables" in categories
    assert "Đĩa ăn" in meal_eval
    assert MealComposer.CLINICAL_DISCLAIMER is not None

