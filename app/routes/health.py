from fastapi import APIRouter

from app.utils.logger import setup_logging

router = APIRouter()
logger = setup_logging()


@router.get("/health", tags=["health"])
def get_health() -> dict[str, str]:
    logger.info("Health endpoint called.")
    return {"status": "ok"}
