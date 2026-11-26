from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.foods import router as foods_router
from app.api.v1.glucose_records import router as glucose_router
from app.api.v1.health import router as health_router
from app.api.v1.health_profiles import router as health_profiles_router
from app.api.v1.nutrition import router as nutrition_router
from app.api.v1.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(health_profiles_router)
api_router.include_router(glucose_router)
api_router.include_router(foods_router)
api_router.include_router(nutrition_router)

__all__ = ["api_router"]
