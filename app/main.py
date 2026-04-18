from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database.init_db import init_db
from app.routes.health import router as health_router
from app.routes.leads import router as leads_router
from app.utils.logger import setup_logging

logger = setup_logging()

app = FastAPI(
    title="Leadflow Automation API",
    version="0.1.0",
    description="Base API for leadflow automation project.",
)
app.include_router(health_router)
app.include_router(leads_router)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    logger.info("Database initialized successfully.")
    logger.info("Application started successfully.")
