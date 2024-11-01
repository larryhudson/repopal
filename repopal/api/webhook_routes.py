from fastapi import APIRouter, Header, HTTPException, Request
from typing import Dict, Optional
from repopal.schemas.webhook import WebhookProvider
from repopal.services.webhook_factory import WebhookHandlerFactory

router = APIRouter()

@router.post("/webhooks/{provider}")
async def webhook_handler(
    provider: WebhookProvider,
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    x_slack_signature: Optional[str] = Header(None),
):
    # Get the raw payload
    payload = await request.json()
    
    # Get all headers for validation
    headers = dict(request.headers)
    
    try:
        handler = WebhookHandlerFactory.get_handler(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Validate the webhook
    if not handler.validate_webhook(headers, payload):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Process the webhook and return standardized event
    event = handler.process_webhook(payload)
    return event
