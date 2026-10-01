from fastapi import FastAPI

from app.api.routes import billing, generate, usage, webhooks

app = FastAPI(
    title="Usage Metering & Billing API",
    description="FlyRank Capstone - Usage Metering and Billing Engine",
    version="1.0.0",
)

app.include_router(generate.router)
app.include_router(usage.router)
app.include_router(webhooks.router)
app.include_router(billing.router)
