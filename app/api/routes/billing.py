from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.stripe_service import create_checkout_session

router = APIRouter()


class CheckoutRequest(BaseModel):
    tenant_id: str
    price_id: str
    success_url: str
    cancel_url: str


@router.post("/billing/checkout")
def create_checkout(request: CheckoutRequest):
    try:
        session = create_checkout_session(
            tenant_id=request.tenant_id,
            price_id=request.price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )

        return {
            "success": True,
            "tenant_id": request.tenant_id,
            "checkout_session_id": session["id"],
            "checkout_url": session["url"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Checkout creation failed: {str(e)}",
        )