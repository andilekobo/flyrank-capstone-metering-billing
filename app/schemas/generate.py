from pydantic import BaseModel


class GenerateRequest(BaseModel):
    tenant_id: str
    input_tokens: int
    cached_input_tokens: int
    reasoning_tokens: int
    output_tokens: int
    idempotency_key: str