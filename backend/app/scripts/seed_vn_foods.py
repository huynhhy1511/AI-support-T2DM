"""Idempotent CLI script to seed standard Vietnamese T2DM foods and normalized allergens.

Usage:
    .venv\\Scripts\\python.exe -m app.scripts.seed_vn_foods
"""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.allergen import Allergen
from app.models.food import Food

DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "vn_t2dm_foods_v1.json"
)


def _to_decimal(value: Optional[float]) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value))


def seed_vn_foods(
    db: Session,
    dataset_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Upsert allergens and Vietnamese T2DM foods from JSON dataset idempotently."""
    path = dataset_path or DEFAULT_DATASET_PATH
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    # 1. Upsert allergens catalog by code
    allergen_map: Dict[str, Allergen] = {}
    existing_allergens = {
        a.code: a for a in db.scalars(select(Allergen)).all()
    }
    allergens_inserted = 0
    allergens_updated = 0

    for item in payload.get("allergens", []):
        code = item["code"].strip().lower()
        name_vi = item["name_vi"].strip()
        name_en = item["name_en"].strip()

        allergen = existing_allergens.get(code)
        if allergen is None:
            allergen = Allergen(code=code, name_vi=name_vi, name_en=name_en)
            db.add(allergen)
            existing_allergens[code] = allergen
            allergens_inserted += 1
        else:
            allergen.name_vi = name_vi
            allergen.name_en = name_en
            allergens_updated += 1
        allergen_map[code] = allergen

    db.flush()

    # 2. Upsert foods by case-insensitive name
    foods_inserted = 0
    foods_updated = 0
    category_counts: Counter[str] = Counter()

    for item in payload.get("foods", []):
        name = item["name"].strip()
        category = item["category"].strip()
        category_counts[category] += 1

        item_allergens = []
        for raw_code in item.get("allergen_codes", []):
            code = raw_code.strip().lower()
            if code in allergen_map:
                item_allergens.append(allergen_map[code])

        data_source = item.get("data_source", "VN_NIN_USDA")
        data_version = item.get("data_version", "v1.0")
        source_name = (
            "Viện Dinh Dưỡng Quốc Gia Việt Nam (2007)"
            if data_source == "VN_NIN_2007"
            else "USDA FoodData Central"
        )
        source_url = (
            "https://viendinhduong.vn/"
            if data_source == "VN_NIN_2007"
            else "https://fdc.nal.usda.gov/"
        )

        existing = db.scalars(
            select(Food).where(Food.name.ilike(name))
        ).first()

        field_values = {
            "name": name,
            "category": category,
            "serving_size_g": _to_decimal(item["serving_size_g"]),
            "energy_kcal": _to_decimal(item["calories"]),
            "carbohydrate_g": _to_decimal(item["carbs_g"]),
            "protein_g": _to_decimal(item["protein_g"]),
            "fat_g": _to_decimal(item["fat_g"]),
            "fiber_g": _to_decimal(item.get("fiber_g", 0.0)),
            "sugar_g": _to_decimal(item.get("sugar_g", 0.0)),
            "glycemic_index": _to_decimal(item.get("glycemic_index")),
            "glycemic_load": _to_decimal(item.get("glycemic_load")),
            "sodium_mg": item.get("sodium_mg"),
            "saturated_fat_g": item.get("saturated_fat_g"),
            "preparation_state": item.get("preparation_state", "cooked"),
            "data_source": data_source,
            "data_version": data_version,
            "is_test_data": False,
            "source_name": source_name,
            "source_url": source_url,
        }

        if existing is None:
            food = Food(**field_values)
            food.allergens = item_allergens
            db.add(food)
            foods_inserted += 1
        else:
            for key, value in field_values.items():
                setattr(existing, key, value)
            existing.allergens = item_allergens
            foods_updated += 1

    db.commit()

    return {
        "dataset_version": payload.get("dataset_version", "v1.0"),
        "allergens_total": len(allergen_map),
        "allergens_inserted": allergens_inserted,
        "allergens_updated": allergens_updated,
        "foods_total_in_dataset": len(payload.get("foods", [])),
        "foods_inserted": foods_inserted,
        "foods_updated": foods_updated,
        "by_category": dict(sorted(category_counts.items())),
    }


def main() -> None:
    db = SessionLocal()
    try:
        summary = seed_vn_foods(db)
        print("=== SEED VN T2DM FOODS SUMMARY ===")
        print(f"Dataset version : {summary['dataset_version']}")
        print(
            f"Allergens       : {summary['allergens_total']} "
            f"(inserted={summary['allergens_inserted']}, updated={summary['allergens_updated']})"
        )
        print(
            f"Foods in dataset: {summary['foods_total_in_dataset']} "
            f"(inserted={summary['foods_inserted']}, updated={summary['foods_updated']})"
        )
        print("Breakdown by category:")
        for cat, count in summary["by_category"].items():
            print(f"  - {cat}: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
