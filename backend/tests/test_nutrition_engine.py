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


def test_allergy_exclusion_single_food():
    """Verify that when a user is allergic to a specific food (e.g. tôm), that food is excluded while safe foods remain."""
    shrimp = _make_dummy_food("Tôm hấp sả", "protein", 0, 24, 1)
    fish = _make_dummy_food("Cá basa hấp", "protein", 0, 18, 5)
    rice = _make_dummy_food("Gạo lứt", "staple", 35, 4, 1, fiber=3)

    req = MealRecommendationRequest(
        user_id=uuid.uuid4(),
        meal_type="lunch",
        excluded_keywords=["tôm"],
    )

    candidates = ConstraintEngine.filter_foods(
        foods=[shrimp, fish, rice],
        request=req,
    )

    assert len(candidates) == 2
    names = [f.name for f in candidates]
    assert "Tôm hấp sả" not in names
    assert "Cá basa hấp" in names
    assert "Gạo lứt" in names


def test_all_foods_excluded_returns_empty_candidates():
    """Verify that when all foods violate safety exclusions, ConstraintEngine returns an empty list without error."""
    food1 = _make_dummy_food("Ức gà luộc", "protein", 0, 30, 2)
    food2 = _make_dummy_food("Trứng luộc", "protein", 0, 12, 10)

    req = MealRecommendationRequest(
        user_id=uuid.uuid4(),
        meal_type="lunch",
        excluded_keywords=["gà", "trứng"],
    )

    candidates = ConstraintEngine.filter_foods(
        foods=[food1, food2],
        request=req,
    )

    assert candidates == []


def test_meal_composer_no_candidates_no_unsafe_fallback():
    """Verify that when candidate list is empty, MealComposer returns empty items and safe message, NEVER falling back."""
    items, meal_eval, safety_notes = MealComposer.compose(
        candidate_foods=[],
        meal_type="lunch",
    )

    assert items == []
    assert "Không tìm thấy thực phẩm phù hợp với các ràng buộc an toàn" in meal_eval
    assert any("Cảnh báo an toàn" in n for n in safety_notes)


def test_meal_composer_with_valid_foods_works_normally():
    """Verify that when valid foods are present, MealComposer still creates a balanced plate normally."""
    staple = _make_dummy_food("Gạo lứt", "staple", 35, 4, 1, fiber=3, gi=55, gl=19)
    protein = _make_dummy_food("Đậu phụ hấp", "protein", 2, 10, 5, fiber=1)
    veg = _make_dummy_food("Rau muống luộc", "vegetables", 4, 3, 0.5, fiber=3, gi=15)

    items, meal_eval, safety_notes = MealComposer.compose(
        candidate_foods=[staple, protein, veg],
        meal_type="lunch",
    )

    assert len(items) == 3
    assert any(i.category == "staple" for i in items)
    assert any(i.category == "protein" for i in items)
    assert any(i.category == "vegetables" for i in items)
    assert "Đĩa ăn" in meal_eval


def test_constraint_engine_vegan_excludes_eggs_and_dairy():
    """Verify vegan constraint excludes meats, fish, eggs, and dairy products."""
    chicken = _make_dummy_food("Ức gà phi lê", "protein", 0, 30, 3)
    salmon = _make_dummy_food("Cá hồi phi lê", "protein", 0, 22, 10)
    egg = _make_dummy_food("Trứng gà luộc", "protein", 0.6, 6.3, 5.3)
    yogurt = _make_dummy_food("Sữa chua không đường", "dairy", 4.5, 12, 0.5)
    tofu = _make_dummy_food("Đậu phụ trắng hấp", "protein", 2, 10, 5)
    broccoli = _make_dummy_food("Bông cải xanh luộc", "vegetables", 8, 3, 0.5, fiber=3.5)

    request = MealRecommendationRequest(
        user_id=uuid.uuid4(),
        meal_type="lunch",
        dietary_preference="vegan",
    )

    filtered = ConstraintEngine.filter_foods(
        foods=[chicken, salmon, egg, yogurt, tofu, broccoli],
        request=request,
    )

    filtered_names = [f.name for f in filtered]
    assert "Trứng gà luộc" not in filtered_names
    assert "Sữa chua không đường" not in filtered_names
    assert "Ức gà phi lê" not in filtered_names
    assert "Cá hồi phi lê" not in filtered_names
    assert "Đậu phụ trắng hấp" in filtered_names
    assert "Bông cải xanh luộc" in filtered_names

    # Also test Vietnamese keyword "thuần chay"
    request_vn = MealRecommendationRequest(
        user_id=uuid.uuid4(),
        meal_type="lunch",
        dietary_preference="thuần chay",
    )
    filtered_vn = ConstraintEngine.filter_foods(
        foods=[chicken, salmon, egg, yogurt, tofu, broccoli],
        request=request_vn,
    )
    filtered_vn_names = [f.name for f in filtered_vn]
    assert "Trứng gà luộc" not in filtered_vn_names
    assert "Sữa chua không đường" not in filtered_vn_names
    assert "Đậu phụ trắng hấp" in filtered_vn_names


def test_constraint_engine_vegetarian_allows_eggs_and_dairy():
    """Verify vegetarian constraint excludes meats and fish, but allows eggs and dairy."""
    chicken = _make_dummy_food("Ức gà phi lê", "protein", 0, 30, 3)
    salmon = _make_dummy_food("Cá hồi phi lê", "protein", 0, 22, 10)
    egg = _make_dummy_food("Trứng gà luộc", "protein", 0.6, 6.3, 5.3)
    yogurt = _make_dummy_food("Sữa chua không đường", "dairy", 4.5, 12, 0.5)
    tofu = _make_dummy_food("Đậu phụ trắng hấp", "protein", 2, 10, 5)

    request = MealRecommendationRequest(
        user_id=uuid.uuid4(),
        meal_type="lunch",
        dietary_preference="vegetarian",
    )

    filtered = ConstraintEngine.filter_foods(
        foods=[chicken, salmon, egg, yogurt, tofu],
        request=request,
    )

    filtered_names = [f.name for f in filtered]
    assert "Ức gà phi lê" not in filtered_names
    assert "Cá hồi phi lê" not in filtered_names
    assert "Trứng gà luộc" in filtered_names
    assert "Sữa chua không đường" in filtered_names
    assert "Đậu phụ trắng hấp" in filtered_names

    # Also test Vietnamese keyword "ăn chay"
    request_vn = MealRecommendationRequest(
        user_id=uuid.uuid4(),
        meal_type="lunch",
        dietary_preference="ăn chay",
    )
    filtered_vn = ConstraintEngine.filter_foods(
        foods=[chicken, salmon, egg, yogurt, tofu],
        request=request_vn,
    )
    filtered_vn_names = [f.name for f in filtered_vn]
    assert "Trứng gà luộc" in filtered_vn_names
    assert "Sữa chua không đường" in filtered_vn_names
    assert "Ức gà phi lê" not in filtered_vn_names


def test_meal_composer_default_multiplier_without_targets():
    """Verify serving_multiplier remains 1.0 when no energy or carb targets are provided."""
    staple = _make_dummy_food("Gạo lứt", "staple", 35, 4, 1, fiber=3, gi=55, gl=19)
    protein = _make_dummy_food("Đậu phụ hấp", "protein", 2, 10, 5, fiber=1)
    veg = _make_dummy_food("Rau muống luộc", "vegetables", 4, 3, 0.5, fiber=3, gi=15)

    items, meal_eval, safety_notes = MealComposer.compose(
        candidate_foods=[staple, protein, veg],
        meal_type="lunch",
        custom_target=None,
    )

    assert len(items) == 3
    for item in items:
        assert item.serving_multiplier == 1.0
        assert not any("Khẩu phần được điều chỉnh" in r for r in item.reasons)


def test_meal_composer_scales_portion_with_target_energy():
    """Verify serving_multiplier scales proportionally with target_energy_kcal and syncs all nutrients."""
    # Base kcal: staple = 165, protein = 93, veg = 32.5 -> Total base kcal = 290.5
    staple = _make_dummy_food("Gạo lứt", "staple", 35, 4, 1, fiber=3, gi=55, gl=19)
    protein = _make_dummy_food("Đậu phụ hấp", "protein", 2, 10, 5, fiber=1)
    veg = _make_dummy_food("Rau muống luộc", "vegetables", 4, 3, 0.5, fiber=3, gi=15)

    target_kcal = 435.75  # 1.5x of 290.5
    items, meal_eval, safety_notes = MealComposer.compose(
        candidate_foods=[staple, protein, veg],
        meal_type="lunch",
        custom_target=NutritionTarget(target_energy_kcal=target_kcal),
    )

    assert len(items) == 3
    for item in items:
        assert item.serving_multiplier == 1.5
        assert any("Khẩu phần được điều chỉnh x1.50" in r for r in item.reasons)

    # Verify scaled totals match sum of scaled items
    total_kcal = round(sum(i.energy_kcal for i in items), 2)
    assert abs(total_kcal - target_kcal) < 0.5
    # Verify GL scaled while GI stayed unchanged
    staple_item = next(i for i in items if i.category == "staple")
    assert staple_item.glycemic_index == 55.0
    assert staple_item.glycemic_load == round(19.0 * 1.5, 2)


def test_meal_composer_respects_target_carbohydrate_limit():
    """Verify min(energy_ratio, carb_ratio) prioritizes glycemic control when carb target is strict."""
    # Base kcal = 290.5, Base carb = 35 + 2 + 4 = 41g
    staple = _make_dummy_food("Gạo lứt", "staple", 35, 4, 1, fiber=3, gi=55, gl=19)
    protein = _make_dummy_food("Đậu phụ hấp", "protein", 2, 10, 5, fiber=1)
    veg = _make_dummy_food("Rau muống luộc", "vegetables", 4, 3, 0.5, fiber=3, gi=15)

    # High energy target (500 kcal -> ratio ~1.72) vs strict carb target (30g -> ratio ~0.73)
    items, meal_eval, safety_notes = MealComposer.compose(
        candidate_foods=[staple, protein, veg],
        meal_type="lunch",
        custom_target=NutritionTarget(
            target_energy_kcal=500.0,
            target_carbohydrate_g=30.0,
        ),
    )

    assert len(items) == 3
    expected_multiplier = round(30.0 / 41.0, 2)  # 0.73
    for item in items:
        assert item.serving_multiplier == expected_multiplier

    total_carb = round(sum(i.carbohydrate_g for i in items), 2)
    assert total_carb <= 30.5  # Within rounding tolerance of 30g


def test_meal_composer_clamps_extreme_targets_with_warning():
    """Verify extreme low/high targets clamp serving_multiplier to [0.5, 2.0] and emit clear warnings."""
    staple = _make_dummy_food("Gạo lứt", "staple", 35, 4, 1, fiber=3, gi=55, gl=19)
    protein = _make_dummy_food("Đậu phụ hấp", "protein", 2, 10, 5, fiber=1)
    veg = _make_dummy_food("Rau muống luộc", "vegetables", 4, 3, 0.5, fiber=3, gi=15)

    # Case 1: Extremely low target (50 kcal -> raw ~0.17, clamped to 0.5)
    low_items, _, low_warnings = MealComposer.compose(
        candidate_foods=[staple, protein, veg],
        meal_type="lunch",
        custom_target=NutritionTarget(target_energy_kcal=50.0),
    )
    assert all(i.serving_multiplier == 0.5 for i in low_items)
    assert any("tối thiểu 0.5x" in w for w in low_warnings)

    # Case 2: Extremely high target (2500 kcal -> raw ~8.6, clamped to 2.0)
    high_items, _, high_warnings = MealComposer.compose(
        candidate_foods=[staple, protein, veg],
        meal_type="lunch",
        custom_target=NutritionTarget(target_energy_kcal=2500.0),
    )
    assert all(i.serving_multiplier == 2.0 for i in high_items)
    assert any("tối đa 2.0x" in w for w in high_warnings)


def test_scoring_and_safety_notes_sodium_and_saturated_fat():
    """Verify high sodium (>500mg) and high saturated fat (>5g) incur penalties and trigger cardiovascular safety notes (>700mg / >7g), while None is handled safely."""
    staple = _make_dummy_food("Gạo lứt", "staple", 35, 4, 1, fiber=3, gi=55, gl=19)
    staple.sodium_mg = 5.0
    staple.saturated_fat_g = 0.3

    salty_fatty_protein = _make_dummy_food("Thịt kho mặn", "protein", 2, 20, 18, fiber=0)
    salty_fatty_protein.sodium_mg = 850.0  # > 500mg item & > 700mg meal
    salty_fatty_protein.saturated_fat_g = 8.0  # > 5g item & > 7g meal

    veg = _make_dummy_food("Bông cải xanh", "vegetables", 8, 3, 0.5, fiber=3.5, gi=15)
    # Intentionally leave sodium_mg and saturated_fat_g as None on veg to test safe None handling

    # 1. Verify item-level scoring penalties
    score, reasons, _ = NutritionScoringEngine.score_item(salty_fatty_protein)
    assert any("Natri cao" in r for r in reasons)
    assert any("Chất béo bão hòa cao" in r for r in reasons)

    # 2. Verify meal-level cardiovascular safety notes
    items, _, safety_notes = MealComposer.compose(
        candidate_foods=[staple, salty_fatty_protein, veg],
        meal_type="lunch",
    )
    assert any("Cảnh báo tim mạch: Tổng lượng natri bữa ăn" in note for note in safety_notes)
    assert any("Cảnh báo tim mạch: Tổng chất béo bão hòa" in note for note in safety_notes)
    protein_item = next(i for i in items if i.food_name == "Thịt kho mặn")
    assert protein_item.sodium_mg == 850.0
    assert protein_item.saturated_fat_g == 8.0





