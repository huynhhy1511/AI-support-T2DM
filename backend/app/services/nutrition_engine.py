import json
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from app.models.food import Food
from app.models.health_profile import HealthProfile
from app.schemas.nutrition import (
    MealRecommendationRequest,
    MealType,
    NutritionTarget,
    RecommendedFoodItem,
)

# Synonym mapping for common allergens in Vietnamese cuisine
ALLERGEN_SYNONYMS: Dict[str, List[str]] = {
    "hải sản": ["tôm", "cua", "cá", "mực", "ghẹ", "hải sản", "shrimp", "fish", "salmon"],
    "seafood": ["tôm", "cua", "cá", "mực", "ghẹ", "hải sản", "shrimp", "fish", "salmon"],
    "tôm": ["tôm", "shrimp", "hải sản"],
    "cá": ["cá", "fish", "salmon"],
    "đậu nành": ["đậu nành", "đậu phụ", "đậu hũ", "tofu", "soy", "tương"],
    "soy": ["đậu nành", "đậu phụ", "đậu hũ", "tofu", "soy"],
    "đậu phộng": ["đậu phộng", "lạc", "peanut"],
    "lạc": ["đậu phộng", "lạc", "peanut"],
    "peanut": ["đậu phộng", "lạc", "peanut"],
    "trứng": ["trứng", "egg"],
    "egg": ["trứng", "egg"],
    "sữa": ["sữa", "dairy", "milk", "yogurt", "sữa chua"],
    "dairy": ["sữa", "dairy", "milk", "yogurt", "sữa chua"],
    "hạt": ["hạnh nhân", "đậu phộng", "lạc", "hạt", "almond", "nut"],
}


@lru_cache(maxsize=1)
def _load_food_extra_metadata() -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    """
    Tải thông tin sodium_mg và allergens từ food_database.json (nếu có)
    để bổ sung cho bảng foods trong PostgreSQL mà không cần sửa schema DB.
    """
    by_id: Dict[str, Dict] = {}
    by_name: Dict[str, Dict] = {}
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    candidates = [root_dir / "food_database.json", root_dir / "Docs" / "food_database.json"]
    for path in candidates:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    items = json.load(f)
                for item in items:
                    fid = str(item.get("food_id", "")).strip().upper()
                    fname = str(item.get("name", "")).strip().lower()
                    meta = {
                        "sodium_mg": float(item.get("sodium_mg") or 0.0),
                        "allergens": str(item.get("allergens") or "Không").strip(),
                    }
                    if fid:
                        by_id[fid] = meta
                    if fname:
                        by_name[fname] = meta
                break
            except Exception:
                pass
    return by_id, by_name


def get_food_extra(food: Food) -> Dict:
    """Lấy sodium_mg và allergens cho một đối tượng Food."""
    by_id, by_name = _load_food_extra_metadata()
    raw_name = food.name.strip()
    if raw_name.startswith("[") and "]" in raw_name:
        fid = raw_name[1:raw_name.index("]")].strip().upper()
        if fid in by_id:
            return by_id[fid]
        clean_name = raw_name[raw_name.index("]") + 1:].strip().lower()
        if clean_name in by_name:
            return by_name[clean_name]
    if raw_name.lower() in by_name:
        return by_name[raw_name.lower()]
    return {"sodium_mg": 0.0, "allergens": "Không"}


class NutritionSafetyGuard:
    """Kiểm tra điều kiện an toàn và mức độ đầy đủ của hồ sơ trước khi gợi ý thực đơn."""

    REQUIRED_FIELDS = ["date_of_birth", "sex", "height_cm", "weight_kg", "activity_level"]

    @classmethod
    def check_profile_completeness(
        cls, health_profile: Optional[HealthProfile]
    ) -> List[str]:
        """Trả về danh sách các trường thông tin cơ bản còn thiếu trong hồ sơ sức khỏe."""
        if health_profile is None:
            return list(cls.REQUIRED_FIELDS)
        missing = []
        for field in cls.REQUIRED_FIELDS:
            if getattr(health_profile, field, None) is None:
                missing.append(field)
        return missing

    @staticmethod
    def check_clinical_restrictions(
        comorbidities: Optional[List[str]] = None,
    ) -> Dict[str, object]:
        """
        Kiểm tra các bệnh đồng mắc cần giới hạn phạm vi khuyến nghị hoặc lọc natri nghiêm ngặt.
        """
        if not comorbidities:
            return {
                "is_restricted": False,
                "abstention_reason": None,
                "low_sodium_required": False,
                "notes": [],
            }

        lowered = [c.lower().strip() for c in comorbidities if c and c.strip()]
        notes: List[str] = []

        # 1. Bệnh thận mạn (CKD) -> Cần bác sĩ chuyên khoa đánh giá protein, kali, photpho, natri
        kidney_keywords = ["ckd", "thận", "suy thận", "kidney", "renal", "nephropathy"]
        if any(any(kw in c for kw in kidney_keywords) for c in lowered):
            return {
                "is_restricted": True,
                "abstention_reason": (
                    "Hồ sơ ghi nhận bệnh đồng mắc liên quan đến thận (CKD/suy thận). "
                    "Người mắc đái tháo đường kèm bệnh thận cần kiểm soát chặt chẽ lượng protein, kali, "
                    "photpho và natri theo phác đồ cá nhân hóa của bác sĩ chuyên khoa thận hoặc chuyên gia dinh dưỡng. "
                    "Hệ thống không tự động tạo thực đơn cho trường hợp này để bảo đảm an toàn."
                ),
                "low_sodium_required": True,
                "notes": [],
            }

        # 2. Tăng huyết áp / bệnh tim mạch -> Yêu cầu hạn chế natri (< 2000 mg/ngày)
        bp_keywords = ["hypertension", "tăng huyết áp", "huyết áp cao", "tim mạch", "cardiovascular"]
        low_sodium = any(any(kw in c for kw in bp_keywords) for c in lowered)
        if low_sodium:
            notes.append(
                "Hồ sơ có tăng huyết áp/bệnh tim mạch: hệ thống ưu tiên món ít natri (mục tiêu < 2000 mg natri/ngày, hạn chế đồ kho mặn và thực phẩm chế biến sẵn)."
            )

        return {
            "is_restricted": False,
            "abstention_reason": None,
            "low_sodium_required": low_sodium,
            "notes": notes,
        }


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


DEFAULT_SCORING_CONFIG = ScoringConfig()


class ConstraintEngine:
    """Rule-based filtering for meals based on user profile, allergies, comorbidities, and dietary constraints."""

    @staticmethod
    def _expand_exclusion_terms(
        excluded_keywords: Optional[List[str]],
        allergies: Optional[List[str]],
    ) -> Set[str]:
        terms: Set[str] = set()
        raw_list = list(excluded_keywords or []) + list(allergies or [])
        for raw in raw_list:
            kw = raw.lower().strip()
            if not kw or kw == "không":
                continue
            terms.add(kw)
            for key, synonyms in ALLERGEN_SYNONYMS.items():
                if key in kw or kw in key:
                    terms.update(synonyms)
        return terms

    @staticmethod
    def filter_foods(
        foods: List[Food],
        request: MealRecommendationRequest,
        health_profile: Optional[HealthProfile] = None,
        low_sodium_required: bool = False,
    ) -> List[Food]:
        filtered: List[Food] = []

        active_preference = (
            request.dietary_preference
            or (health_profile.dietary_preference if health_profile else None)
        )
        pref_lower = active_preference.lower().strip() if active_preference else ""

        if pref_lower in ["low_sodium", "it_muoi", "ít muối"]:
            low_sodium_required = True

        excluded_ids = set(request.excluded_food_ids or [])
        exclusion_terms = ConstraintEngine._expand_exclusion_terms(
            request.excluded_keywords,
            getattr(request, "allergies", None),
        )

        for food in foods:
            if food.id in excluded_ids:
                continue

            extra = get_food_extra(food)
            name_lower = food.name.lower()
            allergen_lower = extra["allergens"].lower()

            # Check allergen/exclusion keywords against BOTH food name and Food DB allergen metadata
            if exclusion_terms:
                hit_name = any(term in name_lower for term in exclusion_terms)
                hit_allergen = (
                    allergen_lower != "không"
                    and any(term in allergen_lower for term in exclusion_terms)
                )
                if hit_name or hit_allergen:
                    continue

            # Vegetarian / Vegan constraint
            if pref_lower in ["vegetarian", "chay", "vegan"]:
                meat_keywords = [
                    "gà", "thịt", "cá", "bò", "heo", "chicken",
                    "salmon", "meat", "tôm", "cua", "trứng",
                ]
                if pref_lower != "vegan":
                    meat_keywords.remove("trứng")
                if any(mk in name_lower for mk in meat_keywords):
                    continue

            # High added sugar filter for standalone staples/proteins
            sugar = float(food.sugar_g or 0)
            if food.category in ["staple", "protein"] and sugar > 15.0:
                continue

            # Strict sodium filter when hypertension / low_sodium is active
            if low_sodium_required and extra["sodium_mg"] > 500.0:
                continue

            filtered.append(food)

        return filtered


class NutritionScoringEngine:
    """Scoring and ranking algorithm assessing nutrient density, fiber, GI/GL, sodium, and meal balance."""

    @staticmethod
    def score_item(
        food: Food,
        config: ScoringConfig = DEFAULT_SCORING_CONFIG,
        preference: Optional[str] = None,
        low_sodium_required: bool = False,
        nutrition_goal: Optional[str] = None,
    ) -> Tuple[float, List[str], Optional[str]]:
        score = config.base_score
        reasons: List[str] = []
        warning: Optional[str] = None
        extra = get_food_extra(food)
        sodium = extra["sodium_mg"]

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

        # 6. Sodium Assessment
        if low_sodium_required:
            if sodium <= 120.0:
                score += 8.0
                reasons.append(f"Hàm lượng natri thấp ({sodium:.0f}mg) phù hợp kiểm soát huyết áp (+8đ)")
            elif sodium > 300.0:
                score -= 12.0
                reasons.append(f"Hàm lượng natri tương đối cao ({sodium:.0f}mg) (-12đ)")

        # 7. Dietary Preference & Goal Match
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

        if nutrition_goal and nutrition_goal.lower().strip() == "weight_loss":
            if float(food.energy_kcal) <= 200.0 and fiber >= 2.0:
                score += 5.0
                reasons.append("Năng lượng vừa phải, giàu chất xơ hỗ trợ kiểm soát cân nặng (+5đ)")

        final_score = max(0.0, min(100.0, score))
        return round(final_score, 1), reasons, warning


class MealComposer:
    """Assembles balanced meals according to the Diabetes Plate Method (ADA / VN Ministry of Health)."""

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
        low_sodium_required: bool = False,
        nutrition_goal: Optional[str] = None,
        avoid_food_ids: Optional[Set[uuid.UUID]] = None,
    ) -> Tuple[List[RecommendedFoodItem], str, List[str]]:
        if not candidate_foods:
            return [], "Không tìm thấy thực phẩm phù hợp với các ràng buộc hiện tại.", [
                "Không thể tạo thực đơn vì không có món ăn nào thỏa mãn tất cả điều kiện dị ứng/kiêng khem của người dùng."
            ]

        scored_items: List[Tuple[Food, float, List[str], Optional[str]]] = []
        for food in candidate_foods:
            score, reasons, warning = NutritionScoringEngine.score_item(
                food,
                preference=preference,
                low_sodium_required=low_sodium_required,
                nutrition_goal=nutrition_goal,
            )
            # Slight diversity penalty if food was already used in another meal of the same day
            if avoid_food_ids and food.id in avoid_food_ids:
                score = round(max(0.0, score - 6.0), 1)
            scored_items.append((food, score, reasons, warning))

        scored_items.sort(key=lambda x: x[1], reverse=True)

        selected_foods: List[RecommendedFoodItem] = []
        safety_notes: List[str] = []

        if meal_type in ["lunch", "dinner"]:
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
            breakfast_candidates = [
                item
                for item in scored_items
                if item[0].category in ["staple", "dairy", "protein", "fruits"]
            ]
            categories_seen = set()
            for item in breakfast_candidates:
                cat = item[0].category
                if cat not in categories_seen:
                    selected_foods.append(cls._to_recommended_item(item))
                    categories_seen.add(cat)
                if len(selected_foods) >= 2:
                    break

        elif meal_type == "snack":
            snack_candidates = [
                item
                for item in scored_items
                if item[0].category in ["fruits", "snack", "dairy"]
                or float(item[0].carbohydrate_g) <= 20.0
            ]
            if snack_candidates:
                selected_foods.append(cls._to_recommended_item(snack_candidates[0]))

        if not selected_foods and scored_items:
            for item in scored_items[:2]:
                selected_foods.append(cls._to_recommended_item(item))

        # Portion adjustment (serving_multiplier) if carb exceeds target or weight_loss goal is set
        max_carb_allowed = 55.0
        if custom_target and custom_target.max_carbohydrate_g:
            max_carb_allowed = custom_target.max_carbohydrate_g
        elif meal_type == "snack":
            max_carb_allowed = 20.0

        total_carb = sum(f.carbohydrate_g * f.serving_multiplier for f in selected_foods)
        if total_carb > max_carb_allowed:
            # Try adjusting staple serving_multiplier to 0.75 if staple carb is large
            for f in selected_foods:
                if f.category == "staple" and f.carbohydrate_g > 25.0:
                    f.serving_multiplier = 0.75
                    f.reasons.append("Điều chỉnh khẩu phần 0.75x để kiểm soát tổng carbohydrate bữa ăn")
                    break
            total_carb = sum(f.carbohydrate_g * f.serving_multiplier for f in selected_foods)

        total_energy = sum(f.energy_kcal * f.serving_multiplier for f in selected_foods)
        total_protein = sum(f.protein_g * f.serving_multiplier for f in selected_foods)
        total_fiber = sum((f.fiber_g or 0) * f.serving_multiplier for f in selected_foods)
        total_sodium = sum((f.sodium_mg or 0) * f.serving_multiplier for f in selected_foods)

        if total_carb > max_carb_allowed:
            safety_notes.append(
                f"Lưu ý: Bữa ăn có tổng lượng carbohydrate {total_carb:.1f}g (vượt ngưỡng gợi ý {max_carb_allowed:.1f}g). "
                f"Khuyến nghị cân nhắc giảm khẩu phần tinh bột hoặc tăng vận động nhẹ sau ăn nếu chỉ số đường huyết trước ăn đang cao."
            )

        if meal_type in ["lunch", "dinner"] and total_fiber < 4.0:
            safety_notes.append(
                "Lượng chất xơ trong bữa ăn còn thấp (< 4g). Hãy bổ sung thêm rau xanh luộc hoặc salad để làm chậm hấp thu đường."
            )

        if low_sodium_required and total_sodium > 650.0:
            safety_notes.append(
                f"Lưu ý natri: Bữa ăn ước tính khoảng {total_sodium:.0f}mg natri. Cần nêm nhạt và hạn chế nước chấm mặn."
            )

        meal_eval = (
            f"Bữa ăn cấu trúc theo nguyên tắc Đĩa ăn cho bệnh nhân đái tháo đường: "
            f"Tổng năng lượng {total_energy:.0f} kcal, "
            f"Carbohydrate {total_carb:.1f}g, Đạm {total_protein:.1f}g, "
            f"Chất xơ {total_fiber:.1f}g, Natri {total_sodium:.0f}mg."
        )

        return selected_foods, meal_eval, safety_notes

    @classmethod
    def suggest_substitutes(
        cls,
        candidate_foods: List[Food],
        food_to_replace: Food,
        preference: Optional[str] = None,
        low_sodium_required: bool = False,
        limit: int = 3,
    ) -> List[RecommendedFoodItem]:
        """Tìm các món ăn thay thế phù hợp trong cùng nhóm thực phẩm và thỏa mãn ràng buộc."""
        same_cat = [
            f for f in candidate_foods
            if f.id != food_to_replace.id and f.category == food_to_replace.category
        ]
        scored = []
        for food in same_cat:
            score, reasons, warning = NutritionScoringEngine.score_item(
                food,
                preference=preference,
                low_sodium_required=low_sodium_required,
            )
            scored.append((food, score, reasons, warning))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [cls._to_recommended_item(item) for item in scored[:limit]]

    @staticmethod
    def _to_recommended_item(
        item_tuple: Tuple[Food, float, List[str], Optional[str]]
    ) -> RecommendedFoodItem:
        food, score, reasons, warning = item_tuple
        extra = get_food_extra(food)
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
            sodium_mg=extra["sodium_mg"],
            glycemic_index=float(food.glycemic_index) if food.glycemic_index is not None else None,
            glycemic_load=float(food.glycemic_load) if food.glycemic_load is not None else None,
            score=score,
            reasons=reasons,
            item_warning=warning,
        )
