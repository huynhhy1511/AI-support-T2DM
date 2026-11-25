"""
Script: import_to_postgres.py
Chức năng: Chuyển toàn bộ dữ liệu thực phẩm (35 món VN), nguồn tài liệu y khoa (M001-M008)
và tri thức y khoa (K001-K029) vào cơ sở dữ liệu PostgreSQL (diabetes_ai_dev).
"""

import sys
import json
import uuid
from decimal import Decimal
from pathlib import Path

# Bảo đảm console hiển thị tốt tiếng Việt trên Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thêm thư mục backend vào sys.path để import models và session
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, delete
from app.db.session import SessionLocal
from app.models.food import Food
from app.models.medical_knowledge import MedicalSource, MedicalKnowledge
from source_resolver import STATIC_SOURCES

CATEGORY_MAPPING = {
    "Tinh bột": "staple",
    "Chất đạm": "protein",
    "Rau củ": "vegetables",
    "Trái cây": "fruits",
    "Chất béo & Hạt": "snack",
    "Món ăn chế biến": "staple",  # hoặc món ăn hỗn hợp
}


def import_medical_sources(session) -> int:
    """Nạp 8 tài liệu nguồn y khoa vào bảng medical_sources."""
    print("--- 1. Import Medical Sources (M001-M008) ---")
    count = 0
    for sid, data in STATIC_SOURCES.items():
        existing = session.scalar(select(MedicalSource).where(MedicalSource.id == sid))
        if existing:
            existing.organization = data["organization"]
            existing.document_name = data["title"]
            existing.year = data.get("year")
            existing.section_page = data.get("section_page")
            existing.url = data.get("url")
        else:
            source = MedicalSource(
                id=sid,
                organization=data["organization"],
                document_name=data["title"],
                year=data.get("year"),
                section_page=data.get("section_page"),
                url=data.get("url"),
            )
            session.add(source)
            count += 1
    session.commit()
    print(f"-> Đã đồng bộ thành công {len(STATIC_SOURCES)} nguồn y khoa vào bảng medical_sources.")
    return len(STATIC_SOURCES)


def import_medical_knowledge(session) -> int:
    """Nạp 29 entries tri thức y khoa vào bảng medical_knowledges."""
    print("\n--- 2. Import Medical Knowledge (K001-K029) ---")
    json_path = BASE_DIR / "medical_knowledge_base.json"
    with open(json_path, "r", encoding="utf-8") as f:
        entries = json.load(f)

    count = 0
    for item in entries:
        eid = item.get("kb_id") or item.get("entry_id")
        existing = session.scalar(select(MedicalKnowledge).where(MedicalKnowledge.entry_id == eid))
        topic = item.get("topic", "")
        subtopic = item.get("subtopic", "")
        population = item.get("population")
        knowledge = item.get("knowledge") or item.get("source_text", "")
        evidence = item.get("evidence_grade") or item.get("evidence_type")
        source_id = item.get("source_id", "M001")
        rec_en = item.get("recommendation_en")

        if existing:
            existing.topic = topic
            existing.subtopic = subtopic
            existing.population = population
            existing.knowledge = knowledge
            existing.evidence_grade = evidence
            existing.source_id = source_id
            existing.recommendation_en = rec_en
        else:
            mk = MedicalKnowledge(
                entry_id=eid,
                topic=topic,
                subtopic=subtopic,
                population=population,
                knowledge=knowledge,
                evidence_grade=evidence,
                source_id=source_id,
                recommendation_en=rec_en,
            )
            session.add(mk)
            count += 1
    session.commit()
    print(f"-> Đã đồng bộ thành công {len(entries)} knowledge entries vào bảng medical_knowledges.")
    return len(entries)


def import_foods(session) -> int:
    """Nạp 35 thực phẩm/món ăn Việt Nam vào bảng foods."""
    print("\n--- 3. Import Food Database (35 món ăn Việt Nam) ---")
    json_path = BASE_DIR / "food_database.json"
    with open(json_path, "r", encoding="utf-8") as f:
        food_list = json.load(f)

    inserted = 0
    updated = 0
    for f in food_list:
        fid = f["food_id"]
        # Đặt tên kèm Food ID để dễ tra cứu và không trùng lặp
        food_name = f"[{fid}] {f['name']}"
        backend_cat = CATEGORY_MAPPING.get(f["category"], "staple")
        carb = float(f.get("carb_g", 0))
        gi = float(f.get("glycemic_index", 0))
        gl = round((gi * carb) / 100.0, 2)

        existing = session.scalar(select(Food).where(Food.name == food_name))
        if existing:
            existing.category = backend_cat
            existing.serving_size_g = Decimal(str(f["serving_size"]))
            existing.energy_kcal = Decimal(str(f["energy_kcal"]))
            existing.carbohydrate_g = Decimal(str(carb))
            existing.protein_g = Decimal(str(f.get("protein_g", 0)))
            existing.fat_g = Decimal(str(f.get("fat_g", 0)))
            existing.fiber_g = Decimal(str(f.get("fiber_g", 0)))
            existing.sugar_g = Decimal("0.0")
            existing.glycemic_index = Decimal(str(gi))
            existing.glycemic_load = Decimal(str(gl))
            existing.is_test_data = False
            existing.source_name = f.get("source", "Viện Dinh dưỡng Quốc gia")
            existing.source_url = "https://viendinhduong.vn/"
            updated += 1
        else:
            # Tạo UUID ngẫu nhiên
            new_food = Food(
                id=uuid.uuid4(),
                name=food_name,
                category=backend_cat,
                serving_size_g=Decimal(str(f["serving_size"])),
                energy_kcal=Decimal(str(f["energy_kcal"])),
                carbohydrate_g=Decimal(str(carb)),
                protein_g=Decimal(str(f.get("protein_g", 0))),
                fat_g=Decimal(str(f.get("fat_g", 0))),
                fiber_g=Decimal(str(f.get("fiber_g", 0))),
                sugar_g=Decimal("0.0"),
                glycemic_index=Decimal(str(gi)),
                glycemic_load=Decimal(str(gl)),
                is_test_data=False,
                source_name=f.get("source", "Viện Dinh dưỡng Quốc gia"),
                source_url="https://viendinhduong.vn/",
            )
            session.add(new_food)
            inserted += 1

    session.commit()
    print(f"-> Đã đồng bộ thành công {len(food_list)} thực phẩm vào bảng foods (thêm mới: {inserted}, cập nhật: {updated}).")
    return len(food_list)


def main():
    print("==================================================")
    print("TIẾN TRÌNH IMPORT DỮ LIỆU VÀO POSTGRESQL (diabetes_ai_dev)")
    print("==================================================")
    db = SessionLocal()
    try:
        import_medical_sources(db)
        import_medical_knowledge(db)
        import_foods(db)
        print("\nHOÀN TẤT 100%: Toàn bộ dữ liệu đã được lưu trữ an toàn trong PostgreSQL!")
    except Exception as e:
        db.rollback()
        print(f"LỖI XẢY RA: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
