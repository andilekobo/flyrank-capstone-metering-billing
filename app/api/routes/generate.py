from fastapi import APIRouter, HTTPException

from app.schemas.generate import GenerateRequest
from app.services.meter_service import calculate_usage
from app.services.quota_service import check_quota
from app.services.idempotency_service import (
    get_processed_request,
    save_processed_request,
)


router = APIRouter()


@router.post("/generate")
def generate(request: GenerateRequest):

    existing_response = get_processed_request(
        request.idempotency_key
    )

    if existing_response:
        return {
            **existing_response,
            "idempotent_replay": True,
        }

    usage = calculate_usage(
        input_tokens=request.input_tokens,
        cached_input_tokens=request.cached_input_tokens,
        reasoning_tokens=request.reasoning_tokens,
        output_tokens=request.output_tokens,
    )

    quota = check_quota(
        api_calls_used=0,
        tokens_used=0,
        requested_tokens=usage["total_billable_tokens"],
    )

    if not quota["allowed"]:
        raise HTTPException(
            status_code=quota["status_code"],
            detail=quota["reason"],
        )

    response = {
        "success": True,
        "message": "Generation completed",
        "tenant_id": request.tenant_id,
        "usage": usage,
        "quota": quota,
        "idempotency_key": request.idempotency_key,
    }

    save_processed_request(
        request.idempotency_key,
        response,
    )

    return response