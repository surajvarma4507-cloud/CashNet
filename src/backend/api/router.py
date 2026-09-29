"""Main API Router aggregating all endpoint routes."""

from fastapi import APIRouter

from src.backend.api.routes import accounts, cases, health, locations, predictions

api_router = APIRouter()

# Include health router (also available directly at root /health)
api_router.include_router(health.router)

# Include domain resources
api_router.include_router(cases.router)
api_router.include_router(accounts.router)
api_router.include_router(locations.router)
api_router.include_router(predictions.router)

