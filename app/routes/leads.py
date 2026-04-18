import logging

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse, Response

from app.database.connection import get_connection
from app.models.lead import LeadCreate, LeadProcessedData
from app.services.lead_dedup_service import lead_exists_by_email
from app.services.lead_priority_service import classify_lead_priority
from app.services.lead_repository_service import save_lead
from app.services.lead_scoring_service import calculate_lead_score
from app.services.lead_validation_service import validate_lead_business_rules
from app.services.webhook_service import send_lead_to_webhook
from app.utils.logger import log_event, setup_logging

router = APIRouter(prefix="/leads", tags=["leads"])
logger = setup_logging()
VALID_PRIORITIES = {"low", "medium", "high"}
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def api_response(status_code: int, content: dict) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=content, headers=CORS_HEADERS)


def fetch_leads(priority: str | None = None) -> list[dict]:
    query = """
    SELECT id, name, email, phone, company, role, source, score, priority, created_at
    FROM leads
    """
    params: tuple[str, ...] = ()
    if priority is not None:
        query += " WHERE lower(priority) = ?"
        params = (priority.lower(),)

    query += " ORDER BY datetime(created_at) DESC, id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


@router.post("", response_model=None)
def receive_lead(lead: LeadCreate) -> dict | JSONResponse:
    log_event(
        logger,
        logging.INFO,
        "Lead received",
        email=lead.email,
        source=lead.source,
    )

    errors = validate_lead_business_rules(lead)
    if errors:
        log_event(
            logger,
            logging.WARNING,
            "Business validation failed",
            email=lead.email,
            errors="; ".join(errors),
        )
        return api_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Business validation failed", "errors": errors},
        )

    if lead_exists_by_email(lead.email):
        log_event(
            logger,
            logging.WARNING,
            "Duplicate lead detected",
            email=lead.email,
        )
        return api_response(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "message": "Duplicate lead detected",
                "errors": ["A lead with this email already exists"],
            },
        )

    score = calculate_lead_score(lead)
    priority = classify_lead_priority(score)
    log_event(
        logger,
        logging.INFO,
        "Lead score and priority calculated",
        email=lead.email,
        score=score,
        priority=priority,
    )
    lead_data = LeadProcessedData(
        **lead.model_dump(),
        score=score,
        priority=priority,
    )

    lead_id = save_lead(lead_data)
    log_event(
        logger,
        logging.INFO,
        "Lead saved in database",
        lead_id=lead_id,
        email=lead.email,
    )

    log_event(logger, logging.INFO, "Sending lead to webhook", lead_id=lead_id)
    webhook_status = send_lead_to_webhook(lead_data.model_dump())

    webhook_log_level = (
        logging.WARNING if webhook_status == "failed" else logging.INFO
    )
    log_event(
        logger,
        webhook_log_level,
        "Webhook processing result",
        lead_id=lead_id,
        webhook_status=webhook_status,
    )

    return api_response(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Lead processed and saved successfully",
            "data": lead_data.model_dump(),
            "webhook_status": webhook_status,
        },
    )


@router.get("", response_model=None)
def list_leads(priority: str | None = Query(default=None)) -> dict | JSONResponse:
    normalized_priority = priority.lower().strip() if priority else None
    if normalized_priority and normalized_priority not in VALID_PRIORITIES:
        return api_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": "Invalid priority filter",
                "errors": ["Priority must be one of: low, medium, high"],
            },
        )

    leads = fetch_leads(priority=normalized_priority)
    log_event(
        logger,
        logging.INFO,
        "Leads listed",
        count=len(leads),
        priority=normalized_priority,
    )
    return api_response(
        status_code=status.HTTP_200_OK,
        content={"message": "Leads fetched successfully", "count": len(leads), "data": leads},
    )


@router.options("", response_model=None)
def options_leads() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=CORS_HEADERS)
