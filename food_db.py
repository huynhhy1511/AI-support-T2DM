"""
Food Database Interface - Phân hệ Dinh dưỡng Đái tháo đường Type 2
Hỗ trợ tra cứu, lọc và kiểm tra ràng buộc dinh dưỡng dựa trên Bảng thành phần thực phẩm VN.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

# Bảo đảm console hiển thị tốt tiếng Việt trên Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_JSON_PATH = BASE_DIR / "food_database.json"


class FoodDatabase:
    """Quản lý và truy vấn cơ sở dữ liệu thực phẩm chuẩn hóa."""

    def __init__(self, json_path: Optional[Path] = None, use_postgres: bool = True):
        self.json_path = json_path or DEFAULT_JSON_PATH
        self.use_postgres = use_postgres
        self.foods: List[Dict[str, Any]] = []
        self._food_map: Dict[str, Dict[str, Any]] = {}
        self.source_storage: str = "JSON"
        self.load()

    def load(self) -> None:
        """Tải dữ liệu thực phẩm, ưu tiên PostgreSQL, fallback sang JSON."""
        if self.use_postgres:
            try:
                self._load_from_postgres()
                self.source_storage = "PostgreSQL"
                return
            except Exception as e:
                # Fallback sang JSON nếu không kết nối được PostgreSQL
                pass

        self._load_from_json()
        self.source_storage = "JSON"

    def _load_from_json(self) -> None:
        """Tải dữ liệu thực phẩm từ file JSON."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file cơ sở dữ liệu: {self.json_path}")
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.foods = json.load(f)
        self._food_map = {item["food_id"]: item for item in self.foods}

    def _load_from_postgres(self) -> None:
        """Tải dữ liệu thực phẩm từ PostgreSQL (bảng foods)."""
        backend_dir = BASE_DIR / "backend"
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from app.db.session import SessionLocal
        from app.models.food import Food
        from app.services.nutrition_engine import get_food_extra
        from sqlalchemy import select

        session = SessionLocal()
        try:
            db_foods = session.scalars(select(Food).where(Food.is_test_data == False)).all()
            if not db_foods:
                raise ValueError("Bảng foods trong PostgreSQL chưa có dữ liệu chính thức.")

            loaded = []
            for item in db_foods:
                # Tách food_id từ name nếu có định dạng [F001] ...
                raw_name = item.name
                food_id = ""
                clean_name = raw_name
                if raw_name.startswith("[") and "]" in raw_name:
                    food_id = raw_name[1:raw_name.index("]")]
                    clean_name = raw_name[raw_name.index("]") + 1:].strip()

                gi = float(item.glycemic_index) if item.glycemic_index is not None else 0.0
                if gi == 0:
                    gi_cat = "Rất thấp (0)"
                elif gi < 55:
                    gi_cat = "Thấp"
                elif gi <= 69:
                    gi_cat = "Trung bình"
                else:
                    gi_cat = "Cao"

                extra = get_food_extra(item)
                loaded.append({
                    "food_id": food_id,
                    "name": clean_name,
                    "category": item.category,
                    "serving_size": float(item.serving_size_g),
                    "serving_unit": f"{float(item.serving_size_g)}g",
                    "energy_kcal": float(item.energy_kcal),
                    "carb_g": float(item.carbohydrate_g),
                    "protein_g": float(item.protein_g),
                    "fat_g": float(item.fat_g),
                    "fiber_g": float(item.fiber_g or 0.0),
                    "sodium_mg": extra["sodium_mg"],
                    "allergens": extra["allergens"],
                    "glycemic_index": gi,
                    "gi_category": gi_cat,
                    "source": item.source_name or "Viện Dinh dưỡng Quốc gia",
                })
            self.foods = loaded
            self._food_map = {item["food_id"]: item for item in self.foods if item["food_id"]}
        finally:
            session.close()

    def get_by_id(self, food_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin thực phẩm theo Food ID (vd: F001)."""
        return self._food_map.get(food_id.strip().upper())

    def search_by_name(self, keyword: str) -> List[Dict[str, Any]]:
        """Tìm kiếm thực phẩm theo tên (không phân biệt hoa thường)."""
        kw = keyword.lower().strip()
        return [item for item in self.foods if kw in item["name"].lower()]

    def filter(
        self,
        category: Optional[str] = None,
        gi_category: Optional[str] = None,
        max_carb: Optional[float] = None,
        max_sodium: Optional[float] = None,
        exclude_allergens: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lọc danh sách thực phẩm theo các tiêu chí:
        - category: Nhóm thực phẩm (Tinh bột, Đạm, Rau củ, Trái cây, Chất béo lành mạnh & Hạt, Món ăn chế biến)
        - gi_category: Thấp, Trung bình, Cao
        - max_carb: Lượng carb tối đa trong khẩu phần (g)
        - max_sodium: Lượng natri tối đa trong khẩu phần (mg)
        - exclude_allergens: Danh sách dị nguyên cần tránh (vd: ["Hải sản", "Đậu nành"])
        """
        results = []
        exclude_allergens_clean = (
            [a.lower().strip() for a in exclude_allergens] if exclude_allergens else []
        )

        for item in self.foods:
            if category and item["category"] != category:
                continue

            if gi_category and item.get("gi_category") != gi_category:
                continue

            if max_carb is not None and item.get("carb_g", 0) > max_carb:
                continue

            if max_sodium is not None and item.get("sodium_mg", 0) > max_sodium:
                continue

            # Kiểm tra dị ứng
            if exclude_allergens_clean:
                item_allergens = item.get("allergens", "").lower()
                has_allergen = any(
                    allergen in item_allergens
                    for allergen in exclude_allergens_clean
                    if item_allergens != "không"
                )
                if has_allergen:
                    continue

            results.append(item)

        return results

    def get_categories(self) -> List[str]:
        """Danh sách tất cả các nhóm thực phẩm hiện có."""
        return sorted(list({item["category"] for item in self.foods}))

    def summary(self) -> Dict[str, Any]:
        """Thống kê tổng quan cơ sở dữ liệu thực phẩm."""
        cat_counts = {}
        for item in self.foods:
            c = item["category"]
            cat_counts[c] = cat_counts.get(c, 0) + 1

        gi_counts = {}
        for item in self.foods:
            g = item.get("gi_category", "Chưa phân loại")
            gi_counts[g] = gi_counts.get(g, 0) + 1

        return {
            "total_items": len(self.foods),
            "categories": cat_counts,
            "gi_distribution": gi_counts,
        }


if __name__ == "__main__":
    db = FoodDatabase()
    stats = db.summary()
    print("=== THỐNG KÊ CƠ SỞ DỮ LIỆU THỰC PHẨM ===")
    print(f"Tổng số thực phẩm: {stats['total_items']}")
    print("\nTheo nhóm thực phẩm:")
    for cat, count in stats["categories"].items():
        print(f"  - {cat}: {count} món")
    print("\nTheo phân loại GI:")
    for gi, count in stats["gi_distribution"].items():
        print(f"  - GI {gi}: {count} món")

    # Thử nghiệm lọc món GI thấp giàu chất xơ
    print("\n=== DEMO: CÁC MÓN GI THẤP (<55) ===")
    low_gi = db.filter(gi_category="Thấp")
    for f in low_gi[:5]:
        print(f"  [{f['food_id']}] {f['name']} - GI: {f['glycemic_index']} - Carb: {f['carb_g']}g - Xơ: {f['fiber_g']}g")

