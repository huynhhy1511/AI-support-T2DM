import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.food import Food
from app.schemas.food import FoodCreate, FoodUpdate


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
        is_test_data=food_in.is_test_data,
        source_name=food_in.source_name,
        source_url=food_in.source_url,
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
    for field, value in update_data.items():
        setattr(food, field, value)

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

