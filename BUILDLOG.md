 Build Log
 Project

Usage Metering & Billing Engine**

FlyRank Backend Track Capstone

---

 Phase 1 — Design and Database

Database architecture

Designed the system around the following core entities:

- `tenants`
- `plans`
- `subscriptions`
- `usage_events`
- `stripe_events`

The database uses PostgreSQL for persistent storage.

Alembic was added for database migrations.

 Tenant model

A tenant represents a customer using the billing system.

Usage events are associated with a `tenant_id` so usage can be calculated independently for each customer.

Plans

Implemented Free and Pro plans with configurable:

- API-call limits
- AI-token limits

The Free plan uses:

```text
1,000 API calls/month
100,000 AI tokens/month


 Phase 2 — Core Billing Logic

Usage metering

Implemented a metering service that calculates billable usage from:

- input tokens
- cached input tokens
- reasoning tokens
- output tokens

Cached input is excluded from full-price input usage.

Reasoning tokens are included in billable output usage.

 Idempotency

Added an idempotency key to billable requests.

The database enforces uniqueness on the idempotency key.

Repeated requests with the same key return the existing usage event instead of creating a duplicate.

Quota enforcement

Implemented quota checks before creating usage events.

API-call quota violations return:

text
429 Too Many Requests

AI-token quota violations return:

text
402 Payment Required


 Input validation

Added Pydantic validation to reject negative token values.

Example:

text
input_tokens = -100


returns:

text
422 Unprocessable Content


---

 Phase 3 — Cost Calculation

Implemented billing calculations using integer cents.

Pinned project pricing:

text
API call:             1 cent
Input:              300 cents / 1M tokens
Cached input:        75 cents / 1M tokens
Output:           1,500 cents / 1M tokens


Implemented the required AI-token rules:

text
billable input = input - cached input

billable output = reasoning + output


Verified a test calculation producing:

text
Input cost:        240 cents
Cached cost:        15 cents
Output cost:       600 cents

Total token cost:  855 cents


Phase 4 — Usage Rollups

Implemented:

text
GET /usage/{tenant_id}


The endpoint:
