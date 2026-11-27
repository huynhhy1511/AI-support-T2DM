import re
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
        high_sodium_penalty: float = 8.0,
        high_saturated_fat_penalty: float = 8.0,
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
        self.high_sodium_penalty = high_sodium_penalty
        self.high_saturated_fat_penalty = high_saturated_fat_penalty
        self.preference_match_bonus = preference_match_bonus


# Default scoring configuration
DEFAULT_SCORING_CONFIG = ScoringConfig()


MEAT_AND_SEAFOOD_KEYWORDS = [
    "gà",
    "thịt",
    "cá",
    "bò",
    "heo",
    "lợn",
    "vịt",
    "chicken",
    "salmon",
    "meat",
    "pork",
    "beef",
    "tôm",
    "cua",
    "mực",
    "hải sản",
    "seafood",
]

ANIMAL_BYPRODUCT_KEYWORDS = [
    "trứng",
    "egg",
    "sữa",
    "milk",
    "yogurt",
    "sữa chua",
    "cheese",
    "phô mai",
    "bơ",
    "butter",
    "mật ong",
    "honey",
]


ALLERGEN_FALLBACK_KEYWORDS = {
    "seafood": ["cá", "tôm", "cua", "mực", "ngao", "nghêu", "sò", "hải sản", "fish", "salmon", "shrimp", "crab", "squid", "clam", "seafood"],
    "shellfish": ["tôm", "cua", "mực", "ngao", "nghêu", "sò", "ốc", "shrimp", "crab", "squid", "clam", "shellfish"],
    "fish": ["cá", "fish", "salmon", "mackerel", "tilapia", "basa"],
    "egg": ["trứng", "egg"],
    "dairy": ["sữa", "sữa chua", "phô mai", "milk", "yogurt", "cheese", "butter", "dairy"],
    "soy": ["đậu nành", "đậu phụ", "tàu hũ", "tempeh", "tofu", "soy"],
    "peanut": ["đậu phộng", "lạc", "peanut"],
    "tree_nut": ["hạnh nhân", "óc chó", "hạt điều", "almond", "walnut", "cashew", "tree_nut"],
    "gluten": ["bánh mì", "lúa mì", "lúa mạch", "mì soba", "wheat", "rye", "gluten"],
    "sesame": ["mè", "vừng", "sesame"],
}


class ConstraintEngine:
    """Rule-based filtering for meals based on user profile, exclusions, structured allergens, and dietary constraints."""

    @staticmethod
    def _term_matches_text(term: str, text: str) -> bool:
        if not term or not text:
            return False
        if term == text:
            return True
        return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None

    @classmethod
    def _matches_structured_allergens(cls, food: Food, terms: List[str]) -> bool:
        """Check user allergy/exclusion terms against normalized food.allergens (code, name_vi, name_en)."""
        allergens = getattr(food, "allergens", None) or []
        if not allergens or not terms:
            return False

        for allergen in allergens:
            code = (getattr(allergen, "code", "") or "").lower().strip()
            name_vi = (getattr(allergen, "name_vi", "") or "").lower().strip()
            name_en = (getattr(allergen, "name_en", "") or "").lower().strip()

            for term in terms:
                normalized_code = term.replace(" ", "_").replace("-", "_")
                if normalized_code == code or term == code:
                    return True
                if cls._term_matches_text(term, name_vi) or cls._term_matches_text(term, name_en):
                    return True
        return False

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

        # 3. Build lists of lowercase exclusion keywords and structured allergen terms
        excluded_keywords = [
            k.lower().strip() for k in (request.excluded_keywords or []) if k and k.strip()
        ]
        excluded_allergens = [
            a.lower().strip() for a in (request.excluded_allergens or []) if a and a.strip()
        ]
        all_allergy_terms = list(dict.fromkeys(excluded_allergens + excluded_keywords))

        # 4. Check each food item against constraints
        for food in foods:
            # Rule 1: Exclude by ID
            if food.id in excluded_ids:
                continue

            name_lower = food.name.lower()
            food_allergens = getattr(food, "allergens", None) or []
            food_allergen_codes = {
                (getattr(a, "code", "") or "").lower().strip() for a in food_allergens
            }

            # Rule 2A (Priority): Structured allergen relation check (code, name_vi, name_en)
            if ConstraintEngine._matches_structured_allergens(food, all_allergy_terms):
                continue

            # Rule 2B (Backward-compatible fallback & name keyword exclusion)
            if any(kw in name_lower for kw in excluded_keywords):
                continue

            if not food_allergens and all_allergy_terms:
                # Fallback for legacy/untagged records without rows in food_allergens
                fallback_matched = False
                for term in all_allergy_terms:
                    normalized_code = term.replace(" ", "_").replace("-", "_")
                    fallback_kws = ALLERGEN_FALLBACK_KEYWORDS.get(normalized_code, [])
                    if term in name_lower or any(fkw in name_lower for fkw in fallback_kws):
                        fallback_matched = True
                        break
                if fallback_matched:
                    continue

            # Rule 3: Vegetarian vs Vegan constraints
            # Group 3A: Vegan (Thuần chay) - Loai bo thit, ca/hai san VA toan bo pham vat tu dong vat (trung, sua, etc.)
            if pref_lower in ["vegan", "thuần chay"]:
                if food.category == "dairy":
                    continue
                if food_allergen_codes & {"fish", "shellfish", "seafood", "egg", "dairy"}:
                    continue
                if any(mk in name_lower for mk in MEAT_AND_SEAFOOD_KEYWORDS):
                    continue
                if any(ak in name_lower for ak in ANIMAL_BYPRODUCT_KEYWORDS):
                    continue

            # Group 3B: Vegetarian (An chay co trung/sua) - Chi loai bo thit/hai san, van cho phep trung va sua
            elif pref_lower in ["vegetarian", "chay", "ăn chay"]:
                if food_allergen_codes & {"fish", "shellfish", "seafood"}:
                    continue
                if any(ek in name_lower for ek in ["trứng", "egg"]):
                    # Trứng gà / trứng vịt được phép cho người ăn chay, trừ khi có kèm thịt/hải sản thực sự
                    real_meat_keywords = [
                        "thịt",
                        "bò",
                        "heo",
                        "lợn",
                        "cá",
                        "tôm",
                        "cua",
                        "mực",
                        "hải sản",
                        "salmon",
                        "pork",
                        "beef",
                        "meat",
                        "seafood",
                    ]
                    if any(rmk in name_lower for rmk in real_meat_keywords):
                        continue
                elif any(mk in name_lower for mk in MEAT_AND_SEAFOOD_KEYWORDS):
                    continue

            # Rule 3C: Low-sodium dietary preference
            elif pref_lower in ["low_sodium", "ít muối", "it_muoi"]:
                if food.sodium_mg is not None and float(food.sodium_mg) > 500.0:
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

        # 5b. Cardiovascular Risk Micronutrients (Sodium & Saturated Fat)
        if food.sodium_mg is not None and float(food.sodium_mg) > 500.0:
            score -= config.high_sodium_penalty
            reasons.append(
                f"Natri cao ({float(food.sodium_mg):.0f}mg/khẩu phần) (-{config.high_sodium_penalty:.0f}đ)"
            )

        if food.saturated_fat_g is not None and float(food.saturated_fat_g) > 5.0:
            score -= config.high_saturated_fat_penalty
            reasons.append(
                f"Chất béo bão hòa cao ({float(food.saturated_fat_g):.1f}g/khẩu phần) (-{config.high_saturated_fat_penalty:.0f}đ)"
            )

        # 6. Dietary Preference Match
        if preference:
            pref = preference.lower().strip()
            name_lower = food.name.lower()
            if pref in ["vegan", "thuần chay"]:
                is_animal_product = (
                    food.category == "dairy"
                    or any(mk in name_lower for mk in MEAT_AND_SEAFOOD_KEYWORDS)
                    or any(ak in name_lower for ak in ANIMAL_BYPRODUCT_KEYWORDS)
                )
                if not is_animal_product and (
                    food.category in ["vegetables", "fruits"]
                    or "tofu" in name_lower
                    or "đậu" in name_lower
                    or food.category == "staple"
                ):
                    score += config.preference_match_bonus
                    reasons.append(
                        f"Phù hợp với chế độ thuần chay (+{config.preference_match_bonus:.0f}đ)"
                    )
            elif pref in ["vegetarian", "chay", "ăn chay"] and (
                food.category in ["vegetables", "fruits", "dairy"]
                or "tofu" in name_lower
                or "đậu" in name_lower
                or "trứng" in name_lower
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
        # 0. Guard against empty candidate list (all foods filtered out by safety constraints)
        if not candidate_foods:
            meal_eval = (
                "Không tìm thấy thực phẩm phù hợp với các ràng buộc an toàn và chế độ ăn của bạn. "
                "Hệ thống không đề xuất thực đơn để đảm bảo an toàn, tránh vi phạm các yếu tố dị ứng hoặc kiêng khem đã khai báo."
            )
            safety_notes = [
                "Cảnh báo an toàn: Toàn bộ thực phẩm đã bị loại bỏ do vi phạm các ràng buộc an toàn "
                "(dị ứng thực phẩm, món kiêng khem hoặc chế độ ăn). "
                "Hệ thống tuân thủ nguyên tắc an toàn y tế và tuyệt đối không tự động bỏ qua các ràng buộc an toàn."
            ]
            return [], meal_eval, safety_notes

        # 1. Score all candidates
        scored_items: List[Tuple[Food, float, List[str], Optional[str]]] = []
        for food in candidate_foods:
            score, reasons, warning = NutritionScoringEngine.score_item(
                food, preference=preference
            )
            scored_items.append((food, score, reasons, warning))

        # Sort items descending by score
        scored_items.sort(key=lambda x: x[1], reverse=True)

        selected_tuples: List[Tuple[Food, float, List[str], Optional[str]]] = []
        safety_notes: List[str] = []

        # 2. Structure composition based on meal_type
        if meal_type in ["lunch", "dinner"]:
            # Plate Method: 1/4 Carb (Staple) + 1/4 Protein + 1/2 Vegetables
            staples = [item for item in scored_items if item[0].category == "staple"]
            proteins = [item for item in scored_items if item[0].category == "protein"]
            vegetables = [item for item in scored_items if item[0].category == "vegetables"]

            if staples:
                selected_tuples.append(staples[0])
            if proteins:
                selected_tuples.append(proteins[0])
            if vegetables:
                selected_tuples.append(vegetables[0])
                if len(vegetables) > 1:
                    selected_tuples.append(vegetables[1])

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
                    selected_tuples.append(item)
                    categories_seen.add(cat)
                if len(selected_tuples) >= 2:
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
                selected_tuples.append(snack_candidates[0])

        # Fallback if specific category was empty: pick top items from safe candidates
        if not selected_tuples and scored_items:
            for item in scored_items[:2]:
                selected_tuples.append(item)

        if not selected_tuples:
            meal_eval = (
                "Không tìm thấy thực phẩm phù hợp cho loại bữa ăn này theo các ràng buộc an toàn đã thiết lập. "
                "Hệ thống không đề xuất thực đơn để đảm bảo an toàn."
            )
            safety_notes.append(
                "Cảnh báo: Không có thực phẩm nào đạt điều kiện an toàn và cấu trúc cho loại bữa ăn này."
            )
            return [], meal_eval, safety_notes

        # 2b. Compute dynamic serving multiplier based on target_energy_kcal / target_carbohydrate_g
        final_multiplier, clamp_warnings = cls._calculate_serving_multiplier(
            selected_tuples=selected_tuples,
            custom_target=custom_target,
        )
        safety_notes.extend(clamp_warnings)

        selected_foods: List[RecommendedFoodItem] = [
            cls._to_recommended_item(item_tuple, multiplier=final_multiplier)
            for item_tuple in selected_tuples
        ]

        # 3-5. Calculate totals, safety evaluation, and meal summary via shared helper
        meal_eval, eval_notes = cls.evaluate_meal_safety(
            selected_foods=selected_foods,
            meal_type=meal_type,
            custom_target=custom_target,
        )
        safety_notes.extend(eval_notes)

        return selected_foods, meal_eval, safety_notes

    @staticmethod
    def evaluate_meal_safety(
        selected_foods: List[RecommendedFoodItem],
        meal_type: MealType,
        custom_target: Optional[NutritionTarget] = None,
    ) -> Tuple[str, List[str]]:
        """Evaluate meal totals and emit clinical glycemic & cardiovascular safety notes."""
        notes: List[str] = []
        total_energy = round(sum(f.energy_kcal for f in selected_foods), 2)
        total_carb = round(sum(f.carbohydrate_g for f in selected_foods), 2)
        total_protein = round(sum(f.protein_g for f in selected_foods), 2)
        total_fiber = round(sum(f.fiber_g or 0 for f in selected_foods), 2)

        # Safety evaluation on Carbohydrates
        max_carb_allowed = 55.0  # Default safe upper bound for main meals (ADA recommendation)
        if custom_target and custom_target.max_carbohydrate_g:
            max_carb_allowed = custom_target.max_carbohydrate_g
        elif meal_type == "snack":
            max_carb_allowed = 20.0

        if total_carb > max_carb_allowed:
            notes.append(
                f"Lưu ý: Bữa ăn có tổng lượng carbohydrate {total_carb:.1f}g (vượt ngưỡng gợi ý {max_carb_allowed:.1f}g). "
                f"Khuyến nghị cân nhắc giảm khẩu phần tinh bột hoặc tăng vận động nhẹ sau ăn nếu chỉ số đường huyết trước ăn đang cao."
            )

        if total_fiber < 4.0:
            notes.append(
                "Lượng chất xơ trong bữa ăn còn thấp (< 4g). Hãy bổ sung thêm rau xanh luộc hoặc salad để làm chậm hấp thu đường."
            )

        # Cardiovascular safety notes (Sodium & Saturated Fat)
        total_sodium = round(
            sum(f.sodium_mg for f in selected_foods if f.sodium_mg is not None), 2
        )
        total_sat_fat = round(
            sum(f.saturated_fat_g for f in selected_foods if f.saturated_fat_g is not None), 2
        )

        if total_sodium > 700.0:
            notes.append(
                f"Cảnh báo tim mạch: Tổng lượng natri bữa ăn ({total_sodium:.0f}mg) vượt ngưỡng 700mg/bữa. "
                f"Khuyến nghị hạn chế muối và nước chấm để kiểm soát huyết áp."
            )

        if total_sat_fat > 7.0:
            notes.append(
                f"Cảnh báo tim mạch: Tổng chất béo bão hòa ({total_sat_fat:.1f}g) vượt ngưỡng 7g/bữa. "
                f"Khuyến nghị giảm mỡ động vật để bảo vệ tim mạch."
            )

        meal_eval = (
            f"Bữa ăn cấu trúc theo nguyên tắc Đĩa ăn cho bệnh nhân đái tháo đường: "
            f"Tổng năng lượng {total_energy:.0f} kcal, "
            f"Carbohydrate {total_carb:.1f}g, Đạm {total_protein:.1f}g, "
            f"Chất xơ {total_fiber:.1f}g. Giữ ổn định chỉ số đường huyết sau bữa ăn."
        )
        return meal_eval, notes

    @staticmethod
    def _calculate_serving_multiplier(
        selected_tuples: List[Tuple[Food, float, List[str], Optional[str]]],
        custom_target: Optional[NutritionTarget],
    ) -> Tuple[float, List[str]]:
        """
        Calculate a safe serving multiplier in [0.5, 2.0] based on target_energy_kcal and target_carbohydrate_g.
        Prioritizes glycemic control by taking min(energy_ratio, carb_ratio) when both targets are specified.
        """
        if not custom_target or (
            custom_target.target_energy_kcal is None
            and custom_target.target_carbohydrate_g is None
        ):
            return 1.0, []

        base_kcal = sum(float(t[0].energy_kcal) for t in selected_tuples)
        base_carb = sum(float(t[0].carbohydrate_g) for t in selected_tuples)

        ratios: List[float] = []
        if custom_target.target_energy_kcal is not None and base_kcal > 0:
            ratios.append(custom_target.target_energy_kcal / base_kcal)
        if custom_target.target_carbohydrate_g is not None and base_carb > 0:
            ratios.append(custom_target.target_carbohydrate_g / base_carb)

        if not ratios:
            return 1.0, []

        # Glycemic control priority: take the stricter (smaller) ratio
        raw_multiplier = min(ratios)
        warnings: List[str] = []

        if raw_multiplier < 0.5:
            clamped = 0.5
            warnings.append(
                "Cảnh báo khẩu phần: Mục tiêu năng lượng/carbohydrate quá thấp so với khẩu phần tối thiểu an toàn. "
                "Hệ thống đã giữ mức khẩu phần tối thiểu 0.5x để tránh thiếu hụt dinh dưỡng."
            )
        elif raw_multiplier > 2.0:
            clamped = 2.0
            warnings.append(
                "Cảnh báo khẩu phần: Mục tiêu năng lượng/carbohydrate quá cao cho một bữa ăn. "
                "Hệ thống đã giới hạn mức khẩu phần tối đa 2.0x để tránh quá tải chuyển hóa và tăng đường huyết sau ăn."
            )
        else:
            clamped = raw_multiplier

        return round(clamped, 2), warnings

    @staticmethod
    def _to_recommended_item(
        item_tuple: Tuple[Food, float, List[str], Optional[str]],
        multiplier: float = 1.0,
    ) -> RecommendedFoodItem:
        food, score, reasons, warning = item_tuple
        item_reasons = list(reasons)
        if multiplier != 1.0:
            item_reasons.append(
                f"Khẩu phần được điều chỉnh x{multiplier:.2f} theo mục tiêu năng lượng/carbohydrate"
            )

        return RecommendedFoodItem(
            food_id=food.id,
            food_name=food.name,
            category=food.category,
            serving_size_g=float(food.serving_size_g),
            serving_multiplier=multiplier,
            energy_kcal=round(float(food.energy_kcal) * multiplier, 2),
            carbohydrate_g=round(float(food.carbohydrate_g) * multiplier, 2),
            protein_g=round(float(food.protein_g) * multiplier, 2),
            fat_g=round(float(food.fat_g) * multiplier, 2),
            fiber_g=round(float(food.fiber_g or 0) * multiplier, 2),
            sugar_g=round(float(food.sugar_g or 0) * multiplier, 2),
            glycemic_index=float(food.glycemic_index) if food.glycemic_index is not None else None,
            glycemic_load=(
                round(float(food.glycemic_load) * multiplier, 2)
                if food.glycemic_load is not None
                else None
            ),
            sodium_mg=(
                round(float(food.sodium_mg) * multiplier, 2)
                if food.sodium_mg is not None
                else None
            ),
            saturated_fat_g=(
                round(float(food.saturated_fat_g) * multiplier, 2)
                if food.saturated_fat_g is not None
                else None
            ),
            score=score,
            reasons=item_reasons,
            item_warning=warning,
        )

