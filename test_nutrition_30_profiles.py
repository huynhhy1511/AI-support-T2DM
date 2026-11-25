"""
Benchmark: test_nutrition_30_profiles.py
Kiểm thử toàn diện P9.1B trên 30 hồ sơ giả lập (Synthetic User Profiles)
theo 7 tiêu chí đánh giá tự động.
"""

import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from nutrition_rag import NutritionRAGExplainer

client = TestClient(app)
explainer = NutritionRAGExplainer()


def _create_synthetic_user_and_profile(profile_cfg: Dict[str, Any]) -> str:
    email = f"syn_{profile_cfg['id']}_{uuid.uuid4().hex[:6]}@test.local"
    u_res = client.post("/api/v1/users", json={"email": email, "full_name": profile_cfg["name"]})
    assert u_res.status_code == 201
    uid = u_res.json()["id"]

    if not profile_cfg.get("skip_profile_record", False):
        hp_payload = {
            "user_id": uid,
            "date_of_birth": profile_cfg.get("dob"),
            "sex": profile_cfg.get("sex"),
            "height_cm": profile_cfg.get("height_cm"),
            "weight_kg": profile_cfg.get("weight_kg"),
            "diabetes_type": "type2",
            "activity_level": profile_cfg.get("activity_level"),
            "dietary_preference": profile_cfg.get("dietary_preference"),
        }
        hp_res = client.post("/api/v1/health-profiles", json=hp_payload)
        assert hp_res.status_code in (200, 201), hp_res.text
    return uid


SYNTHETIC_PROFILES: List[Dict[str, Any]] = [
    # 1-6: Weight Control (weight_loss / maintenance)
    {"id": "P01", "group": "weight_control", "name": "Nguyen Van A", "dob": "1972-04-12", "sex": "male", "height_cm": 168, "weight_kg": 82, "activity_level": "light", "nutrition_goal": "weight_loss"},
    {"id": "P02", "group": "weight_control", "name": "Tran Thi B", "dob": "1968-09-20", "sex": "female", "height_cm": 156, "weight_kg": 68, "activity_level": "sedentary", "nutrition_goal": "weight_loss"},
    {"id": "P03", "group": "weight_control", "name": "Le Van C", "dob": "1975-01-15", "sex": "male", "height_cm": 170, "weight_kg": 79, "activity_level": "moderate", "nutrition_goal": "weight_loss"},
    {"id": "P04", "group": "weight_control", "name": "Pham Thi D", "dob": "1980-06-05", "sex": "female", "height_cm": 160, "weight_kg": 56, "activity_level": "moderate", "nutrition_goal": "maintenance"},
    {"id": "P05", "group": "weight_control", "name": "Hoang Van E", "dob": "1965-11-30", "sex": "male", "height_cm": 165, "weight_kg": 74, "activity_level": "light", "nutrition_goal": "weight_loss"},
    {"id": "P06", "group": "weight_control", "name": "Vo Thi F", "dob": "1978-03-18", "sex": "female", "height_cm": 158, "weight_kg": 54, "activity_level": "light", "nutrition_goal": "glucose_control"},

    # 7-11: Physical Activity Levels (sedentary / light / moderate)
    {"id": "P07", "group": "activity_level", "name": "Dang Van G", "dob": "1960-08-22", "sex": "male", "height_cm": 164, "weight_kg": 65, "activity_level": "sedentary", "nutrition_goal": "glucose_control"},
    {"id": "P08", "group": "activity_level", "name": "Bui Thi H", "dob": "1971-12-01", "sex": "female", "height_cm": 155, "weight_kg": 58, "activity_level": "sedentary", "nutrition_goal": "maintenance"},
    {"id": "P09", "group": "activity_level", "name": "Do Van I", "dob": "1982-05-14", "sex": "male", "height_cm": 172, "weight_kg": 70, "activity_level": "moderate", "nutrition_goal": "maintenance"},
    {"id": "P10", "group": "activity_level", "name": "Ngo Thi K", "dob": "1967-07-09", "sex": "female", "height_cm": 159, "weight_kg": 60, "activity_level": "light", "nutrition_goal": "glucose_control"},
    {"id": "P11", "group": "activity_level", "name": "Duong Van L", "dob": "1974-10-25", "sex": "male", "height_cm": 169, "weight_kg": 67, "activity_level": "moderate", "nutrition_goal": "glucose_control"},

    # 12-16: Dietary Preferences (vegetarian, chay, low_carb, low_sodium)
    {"id": "P12", "group": "preference", "name": "Ly Thi M", "dob": "1970-02-11", "sex": "female", "height_cm": 157, "weight_kg": 57, "activity_level": "light", "dietary_preference": "vegetarian"},
    {"id": "P13", "group": "preference", "name": "Truong Van N", "dob": "1966-06-19", "sex": "male", "height_cm": 166, "weight_kg": 64, "activity_level": "sedentary", "dietary_preference": "chay"},
    {"id": "P14", "group": "preference", "name": "Vu Thi O", "dob": "1979-09-03", "sex": "female", "height_cm": 161, "weight_kg": 63, "activity_level": "moderate", "dietary_preference": "low_carb"},
    {"id": "P15", "group": "preference", "name": "Dinh Van P", "dob": "1964-01-27", "sex": "male", "height_cm": 167, "weight_kg": 69, "activity_level": "light", "dietary_preference": "low_sodium"},
    {"id": "P16", "group": "preference", "name": "Phan Thi Q", "dob": "1976-04-08", "sex": "female", "height_cm": 154, "weight_kg": 55, "activity_level": "light", "dietary_preference": "vegetarian"},

    # 17-21: Food Allergies
    {"id": "P17", "group": "allergy", "name": "Ha Van R", "dob": "1973-07-16", "sex": "male", "height_cm": 171, "weight_kg": 72, "activity_level": "moderate", "allergies": ["Hải sản"]},
    {"id": "P18", "group": "allergy", "name": "Ta Thi S", "dob": "1969-11-04", "sex": "female", "height_cm": 158, "weight_kg": 59, "activity_level": "light", "allergies": ["Đậu nành"]},
    {"id": "P19", "group": "allergy", "name": "Cao Van T", "dob": "1981-08-29", "sex": "male", "height_cm": 174, "weight_kg": 75, "activity_level": "moderate", "allergies": ["Đậu phộng"]},
    {"id": "P20", "group": "allergy", "name": "Lam Thi U", "dob": "1977-12-13", "sex": "female", "height_cm": 162, "weight_kg": 61, "activity_level": "light", "allergies": ["Trứng", "Hải sản"]},
    {"id": "P21", "group": "allergy", "name": "Quach Van V", "dob": "1963-05-21", "sex": "male", "height_cm": 165, "weight_kg": 66, "activity_level": "sedentary", "allergies": ["Hải sản", "Đậu nành"]},

    # 22-25: Hypertension / Cardiovascular Comorbidities
    {"id": "P22", "group": "hypertension", "name": "To Thi W", "dob": "1959-03-10", "sex": "female", "height_cm": 153, "weight_kg": 62, "activity_level": "sedentary", "comorbidities": ["hypertension"]},
    {"id": "P23", "group": "hypertension", "name": "Chau Van X", "dob": "1962-10-17", "sex": "male", "height_cm": 166, "weight_kg": 71, "activity_level": "light", "comorbidities": ["tăng huyết áp"]},
    {"id": "P24", "group": "hypertension", "name": "Mac Thi Y", "dob": "1965-02-28", "sex": "female", "height_cm": 157, "weight_kg": 64, "activity_level": "light", "comorbidities": ["hypertension"], "allergies": ["Hải sản"]},
    {"id": "P25", "group": "hypertension", "name": "Huynh Van Z", "dob": "1961-06-06", "sex": "male", "height_cm": 168, "weight_kg": 76, "activity_level": "sedentary", "comorbidities": ["bệnh tim mạch"], "nutrition_goal": "weight_loss"},

    # 26-28: Kidney Disease / CKD (Expect Abstention)
    {"id": "P26", "group": "ckd_abstention", "name": "Trinh Van AA", "dob": "1958-09-14", "sex": "male", "height_cm": 164, "weight_kg": 63, "activity_level": "sedentary", "comorbidities": ["CKD stage 3"], "expect_abstain": True},
    {"id": "P27", "group": "ckd_abstention", "name": "Kieu Thi AB", "dob": "1960-01-22", "sex": "female", "height_cm": 152, "weight_kg": 54, "activity_level": "sedentary", "comorbidities": ["suy thận mạn"], "expect_abstain": True},
    {"id": "P28", "group": "ckd_abstention", "name": "Tong Van AC", "dob": "1956-11-08", "sex": "male", "height_cm": 163, "weight_kg": 60, "activity_level": "sedentary", "comorbidities": ["bệnh thận"], "expect_abstain": True},

    # 29-30: Incomplete Profile (Expect Abstention when require_complete_profile=True)
    {"id": "P29", "group": "incomplete_abstention", "name": "Le Thi AD", "skip_profile_record": True, "require_complete_profile": True, "expect_abstain": True},
    {"id": "P30", "group": "incomplete_abstention", "name": "Nguyen Van AE", "dob": "1975-05-05", "sex": "male", "height_cm": None, "weight_kg": None, "activity_level": None, "require_complete_profile": True, "expect_abstain": True},
]

FORBIDDEN_MAP = {
    "hải sản": ["tôm", "cua", "cá", "mực", "hải sản", "salmon"],
    "đậu nành": ["đậu nành", "đậu phụ", "đậu hũ", "tofu"],
    "đậu phộng": ["đậu phộng", "lạc"],
    "trứng": ["trứng"],
}


def run_benchmark() -> Dict[str, Any]:
    print("=" * 72)
    print("CHẠY KIỂM THỬ 30 SYNTHETIC USER PROFILES (P9.1B)")
    print("=" * 72)

    total_profiles = len(SYNTHETIC_PROFILES)
    non_abstain_cases = 0
    expected_abstain_cases = 0

    calc_accurate_count = 0
    constraint_satisfied_count = 0
    allergy_checked_cases = 0
    allergy_violation_count = 0
    personalization_checked = 0
    personalization_matched = 0
    rag_grounded_count = 0
    citation_accurate_count = 0
    abstention_correct_count = 0

    details = []

    for prof in SYNTHETIC_PROFILES:
        uid = _create_synthetic_user_and_profile(prof)
        payload = {
            "user_id": uid,
            "dietary_preference": prof.get("dietary_preference"),
            "allergies": prof.get("allergies"),
            "comorbidities": prof.get("comorbidities"),
            "nutrition_goal": prof.get("nutrition_goal"),
            "require_complete_profile": prof.get("require_complete_profile", False),
        }
        res = client.post("/api/v1/nutrition/recommend-daily", json=payload)
        assert res.status_code == 200, f"{prof['id']} failed: {res.text}"
        plan = res.json()

        expect_abstain = prof.get("expect_abstain", False)
        is_abstained = plan["is_abstained"]

        if expect_abstain:
            expected_abstain_cases += 1
            if is_abstained:
                abstention_correct_count += 1
            details.append({"id": prof["id"], "group": prof["group"], "abstained": is_abstained, "ok": is_abstained})
            continue

        non_abstain_cases += 1
        assert not is_abstained, f"{prof['id']} unexpectedly abstained: {plan.get('abstention_reason')}"

        # 1. Nutritional Calculation Accuracy
        calc_ok = True
        sum_kcal = 0.0
        sum_carb = 0.0
        sum_sodium = 0.0
        for m in plan["meals"].values():
            m_kcal = round(sum(it["energy_kcal"] * it["serving_multiplier"] for it in m["items"]), 1)
            m_carb = round(sum(it["carbohydrate_g"] * it["serving_multiplier"] for it in m["items"]), 1)
            if abs(m["total_energy_kcal"] - m_kcal) > 0.2 or abs(m["total_carbohydrate_g"] - m_carb) > 0.2:
                calc_ok = False
            sum_kcal += m["total_energy_kcal"]
            sum_carb += m["total_carbohydrate_g"]
            sum_sodium += m["total_sodium_mg"]

        if abs(plan["daily_total_energy_kcal"] - round(sum_kcal, 1)) > 0.3 or abs(plan["daily_total_sodium_mg"] - round(sum_sodium, 1)) > 0.3:
            calc_ok = False
        if calc_ok:
            calc_accurate_count += 1

        # 2. Allergy Violation Rate
        user_allergies = [a.lower().strip() for a in (prof.get("allergies") or [])]
        if user_allergies:
            allergy_checked_cases += 1
            violated = False
            for m in plan["meals"].values():
                for it in m["items"]:
                    nm = it["food_name"].lower()
                    for al in user_allergies:
                        for term in FORBIDDEN_MAP.get(al, [al]):
                            if term in nm:
                                violated = True
            if violated:
                allergy_violation_count += 1

        # 3. Constraint Satisfaction (vegetarian / hypertension sodium <= 2000mg / plate structure)
        cons_ok = True
        pref = (prof.get("dietary_preference") or "").lower()
        if pref in ["vegetarian", "chay", "vegan"]:
            for m in plan["meals"].values():
                for it in m["items"]:
                    if any(mk in it["food_name"].lower() for mk in ["gà", "thịt", "cá", "bò", "heo", "tôm"]):
                        cons_ok = False
        if prof["group"] == "hypertension" and plan["daily_total_sodium_mg"] > 2000.0:
            cons_ok = False
        if cons_ok:
            constraint_satisfied_count += 1

        # 4. Personalization Check
        if pref or prof.get("nutrition_goal"):
            personalization_checked += 1
            if cons_ok:
                personalization_matched += 1

        # 5 & 6. RAG Groundedness & Citation Accuracy
        rag_res = explainer.explain_meal_plan(meal_plan=plan, user_profile=prof, top_k=5)
        exp_text = rag_res["explanation"]
        kb_ids = rag_res["retrieved_kb_ids"]
        citations = rag_res["citations"]

        grounded = (
            str(plan["daily_total_energy_kcal"]) in exp_text
            and len(kb_ids) > 0
            and any(f"[{kid}]" in exp_text for kid in kb_ids)
        )
        if grounded:
            rag_grounded_count += 1

        cit_ok = (
            len(citations) == len(kb_ids)
            and all(c.get("title") and c.get("source_id") for c in citations)
        )
        if cit_ok:
            citation_accurate_count += 1

        details.append({
            "id": prof["id"],
            "group": prof["group"],
            "kcal": plan["daily_total_energy_kcal"],
            "carb": plan["daily_total_carbohydrate_g"],
            "sodium": plan["daily_total_sodium_mg"],
            "calc_ok": calc_ok,
            "cons_ok": cons_ok,
            "grounded": grounded,
            "cit_ok": cit_ok,
        })

    metrics = {
        "total_profiles": total_profiles,
        "non_abstain_cases": non_abstain_cases,
        "expected_abstain_cases": expected_abstain_cases,
        "nutritional_calculation_accuracy_pct": round(calc_accurate_count / non_abstain_cases * 100, 2),
        "constraint_satisfaction_rate_pct": round(constraint_satisfied_count / non_abstain_cases * 100, 2),
        "allergy_violation_rate_pct": round(allergy_violation_count / max(1, allergy_checked_cases) * 100, 2),
        "personalization_rate_pct": round(personalization_matched / max(1, personalization_checked) * 100, 2),
        "rag_groundedness_pct": round(rag_grounded_count / non_abstain_cases * 100, 2),
        "citation_accuracy_pct": round(citation_accurate_count / non_abstain_cases * 100, 2),
        "abstention_accuracy_pct": round(abstention_correct_count / expected_abstain_cases * 100, 2),
    }

    print("\n--- KẾT QUẢ 7 TIÊU CHÍ ĐÁNH GIÁ ---")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    out_path = BASE_DIR / "p9_1b_benchmark_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "details": details}, f, ensure_ascii=False, indent=2)
    print(f"\nĐã lưu chi tiết kết quả tại: {out_path}")
    return metrics


if __name__ == "__main__":
    m = run_benchmark()
    assert m["nutritional_calculation_accuracy_pct"] == 100.0
    assert m["allergy_violation_rate_pct"] == 0.0
    assert m["abstention_accuracy_pct"] == 100.0
    assert m["citation_accuracy_pct"] == 100.0
