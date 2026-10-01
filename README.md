 Usage Metering & Billing Engine

A backend API that records tenant usage, enforces subscription quotas, calculates usage-based costs, and synchronizes subscription state through Stripe-style webhooks.

Built as a FlyRank Backend Track capstone.



Overview

The system demonstrates the core backend concepts required for a usage metering and billing platform:

- Multi-tenant usage tracking
- Idempotent billable requests
- API-call and AI-token quotas
- Usage-based cost calculation
- Cached-input and reasoning-token pricing
- Subscription management
- Stripe-style Checkout flow
- Signed webhook verification
- Webhook deduplication
- PostgreSQL persistence
- Alembic database migrations

AI generation itself is simulated. No AI API key is required.



 Architecture


                         ┌─────────────────────┐
                         │       Client        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   POST /generate   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Idempotency Check   │
                         └──────────┬──────────┘
                                    │
                         duplicate? │
                         ┌──────────┴──────────┐
                         │                     │
                        YES                   NO
                         │                     │
                         ▼                     ▼
                  Return original      Calculate usage
                  usage event                │
                                           ▼
                                  Check tenant plan
                                           │
                                           ▼
                                     Quota check
                                      │       │
                                  allowed    exceeded
                                      │       │
                                      │    429 / 402
                                      ▼
                               Store usage event
                                      │
                                      ▼
                                  Return result


       ┌──────────────────────┐
       │ GET /usage/{tenant}  │
       └──────────┬───────────┘
                  │
                  ▼
          Roll up usage_events
                  │
                  ▼
          Calculate total cost


       ┌──────────────────────┐
       │  Mock Stripe Checkout│
       └──────────┬───────────┘
                  │
                  ▼
       /webhooks/stripe
                  │
                  ▼
        Verify webhook signature
                  │
                  ▼
        Deduplicate event ID
                  │
                  ▼
        Update subscription/plan

 Technology Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Alembic
- Docker
- Docker Compose
- Uvicorn


 Project Structure

text
app/
├── api/
│   └── routes/
│       ├── billing.py
│       ├── generate.py
│       ├── usage.py
│       └── webhooks.py
├── db/
│   └── database.py
├── models/
│   ├── plan.py
│   ├── stripe_event.py
│   ├── subscription.py
│   ├── tenant.py
│   └── usage_event.py
├── schemas/
│   └── generate.py
├── services/
│   ├── billing_service.py
│   ├── meter_service.py
│   ├── quota_service.py
│   └── stripe_service.py
└── main.py

alembic/
├── versions/
└── env.py

tests/


 Plans and Quotas

Free

text
API calls:    1,000 per month
AI tokens:  100,000 per month

 Pro

The Pro plan is represented as a separate plan and can use higher limits configured in the database.

Usage Metering

Every successful billable generation creates one `usage_event`.

Each event records:

- tenant
- idempotency key
- input tokens
- cached input tokens
- reasoning tokens
- output tokens
- total billable tokens
- creation timestamp

Idempotency

The `idempotency_key` is unique.

If the same request is submitted again using the same key, the existing usage event is returned instead of creating another event.

This prevents retry requests from producing duplicate charges.


 Quota Enforcement

Before creating a new usage event, the API checks:

text
current API calls + requested API call
current tokens + requested tokens


against the tenant's plan.

Responses:

text
429 Too Many Requests
API call quota exceeded


or:

text
402 Payment Required
AI token quota exceeded

AI Token Billing

The project uses pinned test pricing:

| Usage | Price |
|---|---:|
| API call | 1 cent |
| Input | 300 cents / 1M tokens |
| Cached input | 75 cents / 1M tokens |
| Output | 1,500 cents / 1M tokens |

Cached input is removed from full-price input before calculating the input cost.

Reasoning tokens are included in the output-priced category.

For example:

text
Input tokens:          1,000,000
Cached input:            200,000
Reasoning:               100,000
Output:                  300,000


The calculation is:

text
Billable input  = 1,000,000 - 200,000
                = 800,000

Billable output = 100,000 + 300,000
                = 400,000


This produces:

text
Input cost:        240 cents
Cached cost:        15 cents
Output cost:       600 cents

Total:             855 cents


All money calculations use integer cents.


API Endpoints

 Generate

text
POST /generate


Creates a simulated billable generation and records usage.

Example:

json
{
  "tenant_id": "tenant-test-001",
  "input_tokens": 1000,
  "cached_input_tokens": 200,
  "reasoning_tokens": 100,
  "output_tokens": 300,
  "idempotency_key": "example-request-001"
}


 Usage

text
GET /usage/{tenant_id}

Returns the tenant's current billing-period usage, plan limits, and calculated cost.

 Checkout

text
POST /billing/checkout


Creates a mock Stripe Checkout session for a Pro subscription.


 Stripe Webhook

text
POST /webhooks/stripe


Handles:

text
checkout.session.completed
customer.subscription.updated
customer.subscription.deleted


Webhook processing:

1. Reads the raw request body.
2. Verifies the signature.
3. Validates the event.
4. Checks whether the event was already processed.
5. Updates subscription state.
6. Records the processed event.


Strip
e Environment

The project uses a Stripe-shaped mock/test-fixture implementation.

A real Stripe account was not available for this development environment, so the external Stripe interaction is simulated while preserving the required Checkout and webhook architecture.

The implementation demonstrates:

- Checkout session creation
- Signed webhook requests
- Signature verification
- Event deduplication
- Subscription state synchronization

No real payment credentials are stored in the repository.



Database

PostgreSQL is used for persistent storage.

Core tables:

text
tenants
plans
subscriptions
usage_events
stripe_events


Alembic manages schema migrations.


 Running the Project
 1. Clone the repository

bash
git clone https://github.com/andilekobo/flyrank-capstone-metering-billing.git
cd flyrank-capstone-metering-billing


 2. Create a virtual environment

Windows:

powershell
python -m venv .venv
.venv\Scripts\Activate.ps1


Codespaces/Linux:

bash
python -m venv .venv
source .venv/bin/activate


3. Install dependencies

bash
pip install -r requirements.txt


 4. Configure environment variables

Copy:

text
.env.example


to:

text
.env

Set:

text
DATABASE_URL=postgresql://metering_user:your_password@localhost:5432/metering_billing
MOCK_WEBHOOK_SECRET=your_mock_webhook_secret


Never commit `.env`.

5. Start PostgreSQL

bash
docker compose up -d


Verify:

bash
docker ps


 6. Run migrations

bash
alembic upgrade head


7. Start FastAPI

bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

API documentation:

text
http://localhost:8000/docs




Testing

The implementation was tested for:

- Idempotent requests
- Duplicate usage prevention
- API quota boundaries
- AI-token quota enforcement
- Invalid token values
- Usage rollups
- Cost calculation
- Checkout processing
- Webhook signature rejection
- Webhook event replay/deduplication
- Subscription cancellation

Detailed evidence is available in:

text
EVIDENCE.md



 Required Capstone Files

text
README.md
EVIDENCE.md
BUILDLOG.md
capstone.yaml
.env.example

 Security

Secrets and local configuration are excluded through `.gitignore`.

The repository must never contain:

text
.env
database passwords
webhook secrets
API keys


Only placeholder configuration belongs in `.env.example`.

 Scope

The project intentionally keeps the billing system small.

It does not implement:

- Real AI generation
- Production payment processing
- Invoicing
- Proration
- Overage billing

The purpose is to demonstrate correct usage metering, quota enforcement, billing calculations, and subscription synchronization.