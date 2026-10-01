from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    tenant_id: str
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    idempotency_key: str