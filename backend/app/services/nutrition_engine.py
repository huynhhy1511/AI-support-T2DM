import uuid
from decimal import Decimal
from typing import List, Optional, Tuple

from app.models.food import Food
from app.models.health_profile import HealthProfile
from app.schemas.nutrition import (
    MealRecommendationRequest,
    MealType,
    NutritionTarget,
    RecommendedFoodItem,
)


class ScoringConfig:
    """Configurable scoring weights with explicit rationales for Type 2 Diabetes meal recommendation."""

    def __init__(
        self,
        base_score: float = 50.0,
        fiber_weight: float = 3.0,
        max_fiber_bonus: float = 15.0,
        low_gi_bonus: float = 15.0,
        medium_gi_bonus: float = 5.0,
        high_gi_penalty: float = 20.0,
        low_gl_bonus: float = 10.0,
        high_gl_penalty: float = 15.0,
        sugar_penalty_per_gram: float = 1.0,
        lean_protein_bonus: float = 10.0,
        high_fat_penalty: float = 8.0,
        preference_match_bonus: float = 10.0,
    ):
        self.base_score = base_score
        self.fiber_weight = fiber_weight
        self.max_fiber_bonus = max_fiber_bonus
        self.low_gi_bonus = low_gi_bonus
        self.medium_gi_bonus = medium_gi_bonus
        self.high_gi_penalty = high_gi_penalty
        self.low_gl_bonus = low_gl_bonus
        self.high_gl_penalty = high_gl_penalty
        self.sugar_penalty_per_gram = sugar_penalty_per_gram
        self.lean_protein_bonus = lean_protein_bonus
        self.high_fat_penalty = high_fat_penalty
        self.preference_match_bonus = preference_match_bonus


# Default scoring configuration
DEFAULT_SCORING_CONFIG = ScoringConfig()


class ConstraintEngine:
    """Rule-based filtering for meals based on user profile, exclusions, and dietary constraints."""

    @staticmethod
    def filter_foods(
        foods: List[Food],
        request: MealRecommendationRequest,
        health_profile: Optional[HealthProfile] = None,
    ) -> List[Food]:
        filtered: List[Food] = []

        # 1. Determine active dietary preference (from request or fallback to profile)
        active_preference = (
            request.dietary_preference
            or (health_profile.dietary_preference if health_profile else None)
        )
        pref_lower = active_preference.lower().strip() if active_preference else ""

        # 2. Build set of excluded food IDs
        excluded_ids = set(request.excluded_food_ids or [])

        # 3. Build list of lowercase exclusion keywords
        excluded_keywords = [
            k.lower().strip() for k in (request.excluded_keywords or []) if k.strip()
        ]

        # 4. Check each food item against constraints
        for food in foods:
            # Rule 1: Exclude by ID
            if food.id in excluded_ids:
                continue

            # Rule 2: Exclude by keywords (e.g. allergies, user dislikes)
            name_lower = food.name.lower()
            if any(kw in name_lower for kw in excluded_keywords):
                continue

            # Rule 3: Vegetarian constraint
            if pref_lower in ["vegetarian", "chay", "vegan"]:
                meat_keywords = [
                    "gà",
                    "thịt",
                    "cá",
                    "bò",
                    "heo",
                    "chicken",
                    "salmon",
                    "meat",
                    "tôm",
                    "cua",
                ]
                if any(mk in name_lower for mk in meat_keywords):
                    continue

            # Rule 4: Extreme sugar filter for standalone staples/proteins
            # Type 2 diabetes guideline recommends avoiding foods with excessive added sugar
            sugar = float(food.sugar_g or 0)
            if food.category in ["staple", "protein"] and sugar > 15.0:
                continue

            filtered.append(food)

        return filtered


class NutritionScoringEngine:
    """Scoring and ranking algorithm assessing nutrient density, fiber, GI/GL, and meal balance."""

    @staticmethod
    def score_item(
        food: Food,
        config: ScoringConfig = DEFAULT_SCORING_CONFIG,
        preference: Optional[str] = None,
    ) -> Tuple[float, List[str], Optional[str]]:
        score = config.base_score
        reasons: List[str] = []
        warning: Optional[str] = None

        # 1. Fiber Assessment
        fiber = float(food.fiber_g or 0)
        if fiber > 0:
            fiber_bonus = min(fiber * config.fiber_weight, config.max_fiber_bonus)
            score += fiber_bonus
            reasons.append(
                f"Chất xơ cao ({fiber:.1f}g) hỗ trợ làm chậm hấp thu glucose (+{fiber_bonus:.1f}đ)"
            )

        # 2. Glycemic Index (GI) Assessment
        if food.glycemic_index is not None:
            gi = float(food.glycemic_index)
            if gi <= 55:
                score += config.low_gi_bonus
                reasons.append(
                    f"Chỉ số đường huyết thấp GI={gi:.0f} (<= 55) giảm nguy cơ tăng vọt đường huyết (+{config.low_gi_bonus:.0f}đ)"
                )
            elif gi <= 69:
                score += config.medium_gi_bonus
                reasons.append(
                    f"Chỉ số đường huyết trung bình GI={gi:.0f} (+{config.medium_gi_bonus:.0f}đ)"
                )
            else:
                score -= config.high_gi_penalty
                reasons.append(
                    f"Chỉ số đường huyết cao GI={gi:.0f} (>= 70) (-{config.high_gi_penalty:.0f}đ)"
                )
                warning = f"Chỉ số GI của món ({gi:.0f}) ở mức cao; nên kết hợp nhiều rau xanh và kiểm soát lượng ăn."
        else:
            reasons.append("Chưa có kiểm định GI chính thức từ nguồn (đánh giá dựa trên carb và chất xơ)")

        # 3. Glycemic Load (GL) Assessment
        if food.glycemic_load is not None:
            gl = float(food.glycemic_load)
            if gl <= 10:
                score += config.low_gl_bonus
                reasons.append(
                    f"Tải lượng đường huyết thấp GL={gl:.1f} (<= 10) an toàn trong mỗi khẩu phần (+{config.low_gl_bonus:.0f}đ)"
                )
            elif gl >= 20:
                score -= config.high_gl_penalty
                reasons.append(
                    f"Tải lượng đường huyết cao GL={gl:.1f} (>= 20) (-{config.high_gl_penalty:.0f}đ)"
                )

        # 4. Sugar Penalty
        sugar = float(food.sugar_g or 0)
        if sugar > 5.0:
            penalty = (sugar - 5.0) * config.sugar_penalty_per_gram
            score -= penalty
            reasons.append(
                f"Lượng đường đơn {sugar:.1f}g (> 5g/khẩu phần) (-{penalty:.1f}đ)"
            )

        # 5. Lean Protein & Healthy Fat
        protein = float(food.protein_g)
        fat = float(food.fat_g)
        if protein >= 10.0 and fat <= 6.0:
            score += config.lean_protein_bonus
            reasons.append(
                f"Nguồn đạm nạc chất lượng ({protein:.1f}g protein, ít chất béo bão hòa) (+{config.lean_protein_bonus:.0f}đ)"
            )
        elif fat > 15.0 and food.category != "snack":
            score -= config.high_fat_penalty
            reasons.append(
                f"Chất béo tương đối cao ({fat:.1f}g) (-{config.high_fat_penalty:.0f}đ)"
            )

        # 6. Dietary Preference Match
        if preference:
            pref = preference.lower().strip()
            name_lower = food.name.lower()
            if pref in ["vegetarian", "chay", "vegan"] and (
                food.category in ["vegetables", "fruits", "dairy"]
                or "tofu" in name_lower
                or "đậu" in name_lower
            ):
                score += config.preference_match_bonus
                reasons.append(
                    f"Phù hợp với sở thích ăn chay (+{config.preference_match_bonus:.0f}đ)"
                )
            elif pref in ["low_carb", "it_carb"] and float(food.carbohydrate_g) <= 15.0:
                score += config.preference_match_bonus
                reasons.append(
                    f"Carbohydrate thấp phù hợp chế độ ít carb (+{config.preference_match_bonus:.0f}đ)"
                )

        # Clamp score between 0.0 and 100.0
        final_score = max(0.0, min(100.0, score))
        return round(final_score, 1), reasons, warning


class MealComposer:
    """Assembles a balanced meal plan according to the Diabetes Plate Method (ADA / VN Ministry of Health)."""

    CLINICAL_DISCLAIMER = (
        "Gợi ý dinh dưỡng mang tính chất hỗ trợ tự quản lý và tham khảo theo chuẩn Plate Method "
        "(ADA/Bộ Y tế). Không phải chỉ định điều trị y khoa. Người bệnh tuyệt đối không tự ý thay đổi thuốc điều trị "
        "và cần tham khảo ý kiến bác sĩ hoặc chuyên gia dinh dưỡng khi điều chỉnh chế độ ăn cá nhân."
    )

    @classmethod
    def compose(
        cls,
        candidate_foods: List[Food],
        meal_type: MealType,
        preference: Optional[str] = None,
        custom_target: Optional[NutritionTarget] = None,
    ) -> Tuple[List[RecommendedFoodItem], str, List[str]]:
        # 1. Score all candidates
        scored_items: List[Tuple[Food, float, List[str], Optional[str]]] = []
        for food in candidate_foods:
            score, reasons, warning = NutritionScoringEngine.score_item(
                food, preference=preference
            )
            scored_items.append((food, score, reasons, warning))

        # Sort items descending by score
        scored_items.sort(key=lambda x: x[1], reverse=True)

        selected_foods: List[RecommendedFoodItem] = []
        safety_notes: List[str] = []

        # 2. Structure composition based on meal_type
        if meal_type in ["lunch", "dinner"]:
            # Plate Method: 1/4 Carb (Staple) + 1/4 Protein + 1/2 Vegetables
            staples = [item for item in scored_items if item[0].category == "staple"]
            proteins = [item for item in scored_items if item[0].category == "protein"]
            vegetables = [item for item in scored_items if item[0].category == "vegetables"]

            if staples:
                selected_foods.append(cls._to_recommended_item(staples[0]))
            if proteins:
                selected_foods.append(cls._to_recommended_item(proteins[0]))
            if vegetables:
                selected_foods.append(cls._to_recommended_item(vegetables[0]))
                if len(vegetables) > 1:
                    selected_foods.append(cls._to_recommended_item(vegetables[1]))

        elif meal_type == "breakfast":
            # Breakfast: 1 staple/dairy + 1 protein or light fruit
            breakfast_candidates = [
                item
                for item in scored_items
                if item[0].category in ["staple", "dairy", "protein", "fruits"]
            ]
            # Pick top 2 complementary items
            categories_seen = set()
            for item in breakfast_candidates:
                cat = item[0].category
                if cat not in categories_seen:
                    selected_foods.append(cls._to_recommended_item(item))
                    categories_seen.add(cat)
                if len(selected_foods) >= 2:
                    break

        elif meal_type == "snack":
            # Snack: 1 healthy low-GL item (fruits, snack, dairy)
            snack_candidates = [
                item
                for item in scored_items
                if item[0].category in ["fruits", "snack", "dairy"]
                or float(item[0].carbohydrate_g) <= 20.0
            ]
            if snack_candidates:
                selected_foods.append(cls._to_recommended_item(snack_candidates[0]))

        # Fallback if specific category was empty: pick top items
        if not selected_foods and scored_items:
            for item in scored_items[:2]:
                selected_foods.append(cls._to_recommended_item(item))

        # 3. Calculate summary nutrients
        total_carb = sum(f.carbohydrate_g for f in selected_foods)
        total_fiber = sum(f.fiber_g or 0 for f in selected_foods)

        # 4. Safety evaluation on Carbohydrates
        max_carb_allowed = 55.0  # Default safe upper bound for main meals (ADA recommendation)
        if custom_target and custom_target.max_carbohydrate_g:
            max_carb_allowed = custom_target.max_carbohydrate_g
        elif meal_type == "snack":
            max_carb_allowed = 20.0

        if total_carb > max_carb_allowed:
            safety_notes.append(
                f"Lưu ý: Bữa ăn có tổng lượng carbohydrate {total_carb:.1f}g (vượt ngưỡng gợi ý {max_carb_allowed:.1f}g). "
                f"Khuyến nghị cân nhắc giảm khẩu phần tinh bột hoặc tăng vận động nhẹ sau ăn nếu chỉ số đường huyết trước ăn đang cao."
            )

        if total_fiber < 4.0:
            safety_notes.append(
                "Lượng chất xơ trong bữa ăn còn thấp (< 4g). Hãy bổ sung thêm rau xanh luộc hoặc salad để làm chậm hấp thu đường."
            )

        meal_eval = (
            f"Bữa ăn cấu trúc theo nguyên tắc Đĩa ăn cho bệnh nhân đái tháo đường: "
            f"Tổng năng lượng {sum(f.energy_kcal for f in selected_foods):.0f} kcal, "
            f"Carbohydrate {total_carb:.1f}g, Đạm {sum(f.protein_g for f in selected_foods):.1f}g, "
            f"Chất xơ {total_fiber:.1f}g. Giữ ổn định chỉ số đường huyết sau bữa ăn."
        )

        return selected_foods, meal_eval, safety_notes

    @staticmethod
    def _to_recommended_item(
        item_tuple: Tuple[Food, float, List[str], Optional[str]]
    ) -> RecommendedFoodItem:
        food, score, reasons, warning = item_tuple
        return RecommendedFoodItem(
            food_id=food.id,
            food_name=food.name,
            category=food.category,
            serving_size_g=float(food.serving_size_g),
            serving_multiplier=1.0,
            energy_kcal=float(food.energy_kcal),
            carbohydrate_g=float(food.carbohydrate_g),
            protein_g=float(food.protein_g),
            fat_g=float(food.fat_g),
            fiber_g=float(food.fiber_g or 0),
            sugar_g=float(food.sugar_g or 0),
            glycemic_index=float(food.glycemic_index) if food.glycemic_index is not None else None,
            glycemic_load=float(food.glycemic_load) if food.glycemic_load is not None else None,
            score=score,
            reasons=reasons,
            item_warning=warning,
        )

