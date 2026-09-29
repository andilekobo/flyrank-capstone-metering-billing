from fastapi import FastAPI

from app.api.routes import generate


app = FastAPI(
    title="Usage Metering & Billing API",
    description="FlyRank Capstone - Usage Metering and Billing Engine",
    version="1.0.0",
)


app.include_router(generate.router)