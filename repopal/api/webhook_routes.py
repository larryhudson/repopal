from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

from repopal.schemas.service_handler import ServiceProvider
from repopal.services.service_handler_factory import ServiceHandlerFactory

router = APIRouter()


@router.post("/webhooks/{provider}")
async def webhook_handler(
    provider: ServiceProvider,
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    x_slack_signature: Optional[str] = Header(None),
):
    # Get the raw payload
    payload = await request.json()

    # Get all headers for validation
    headers = dict(request.headers)

    try:
        handler = ServiceHandlerFactory.get_handler(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate the webhook
    if not handler.validate_webhook(headers, payload):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Process the webhook and return standardized event
    event = handler.process_webhook(payload)
    return event
