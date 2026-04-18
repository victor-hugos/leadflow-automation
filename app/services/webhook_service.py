import json
import os
from urllib import error, request

from app.utils.logger import setup_logging

WEBHOOK_URL_ENV = "LEAD_WEBHOOK_URL"
logger = setup_logging()


def send_lead_to_webhook(payload: dict) -> str:
    webhook_url = os.getenv(WEBHOOK_URL_ENV, "").strip()
    if not webhook_url:
        logger.info("Webhook skipped: %s is not configured.", WEBHOOK_URL_ENV)
        return "skipped"

    body = json.dumps(payload).encode("utf-8")
    webhook_request = request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(webhook_request, timeout=5) as response:
            if 200 <= response.status < 300:
                logger.info("Webhook sent successfully with status=%s.", response.status)
                return "sent"
            logger.warning("Webhook failed with non-2xx status=%s.", response.status)
            return "failed"
    except (error.URLError, error.HTTPError, TimeoutError) as exc:
        logger.warning("Webhook call failed: %s", exc)
        return "failed"
