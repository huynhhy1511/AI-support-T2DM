import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.food import FoodCreate, FoodResponse, FoodUpdate
from app.services import food_service

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get(
    "",
    response_model=List[FoodResponse],
    summary="List Foods",
    description="Retrieve food items with category, search, and pagination filters.",
)
def list_foods_endpoint(
    category: Optional[str] = Query(None, description="Filter by category (e.g. 'staple', 'vegetables', 'protein')"),
    search: Optional[str] = Query(None, description="Search by food name"),
    is_test_data: Optional[bool] = Query(None, description="Filter test vs real official foods"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[FoodResponse]:
    return food_service.list_foods(
        db, category=category, search=search, is_test_data=is_test_data, skip=skip, limit=limit
    )


@router.post(
    "",
    response_model=FoodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Food Item",
    description="Add a new food item with nutrition facts per standard serving size.",
)
def create_food_endpoint(
    food_in: FoodCreate,
    db: Session = Depends(get_db),
) -> FoodResponse:
    return food_service.create_food(db, food_in)


@router.post(
    "/seed-sample",
    summary="Seed Sample Test Foods",
    description="Seed initial test food items (labeled as test data) if database table is currently empty.",
)
def seed_sample_endpoint(
    db: Session = Depends(get_db),
) -> dict:
    added = food_service.seed_sample_foods_if_empty(db)
    return {"message": "Sample foods seeded successfully", "added_count": added}


@router.get(
    "/{food_id}",
    response_model=FoodResponse,
    summary="Get Food by ID",
    description="Retrieve details of a single food item.",
)
def get_food_endpoint(
    food_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> FoodResponse:
    food = food_service.get_food_by_id(db, food_id)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food item with id '{food_id}' not found.",
        )
    return food


@router.put(
    "/{food_id}",
    response_model=FoodResponse,
    summary="Update Food Item",
    description="Update nutritional content or details of a food item.",
)
def update_food_endpoint(
    food_id: uuid.UUID,
    food_in: FoodUpdate,
    db: Session = Depends(get_db),
) -> FoodResponse:
    food = food_service.update_food(db, food_id, food_in)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food item with id '{food_id}' not found.",
        )
    return food


@router.delete(
    "/{food_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Food Item",
    description="Delete a food item from the database.",
)
def delete_food_endpoint(
    food_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> dict:
    success = food_service.delete_food(db, food_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food item with id '{food_id}' not found.",
        )
    return {"message": "Food item deleted successfully", "food_id": str(food_id)}

