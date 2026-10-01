# Evidence

 1. Metering and Idempotency

 Requirement

A billable action must create exactly one usage event. Sending the same request again with the same idempotency key must not create another usage event or duplicate the charge.

 Test

First request:

text
POST /generate
tenant_id: tenant-test-001
idempotency_key: api-test-001
input_tokens: 1000
cached_input_tokens: 200
reasoning_tokens: 100
output_tokens: 300
```

Result:

json
{
  "success": true,
  "idempotent_replay": false,
  "usage": {
    "input_tokens": 1000,
    "cached_input_tokens": 200,
    "reasoning_tokens": 100,
    "output_tokens": 300,
    "total_billable_tokens": 1200
  }
}


The same request was sent again using the same idempotency key.

Result:

json
{
  "success": true,
  "idempotent_replay": true,
  "idempotency_key": "api-test-001"
}


Database verification showed only one usage event for the idempotency key:

text
(3, 'api-test-001', 1200)


Conclusion

The same request and idempotency key return the original usage event instead of creating a second billable event.

 2. API Call Quota

Requirement

Requests exceeding the tenant's API-call quota must be rejected with HTTP 429.

Test

A Free-plan tenant was seeded with 999 usage events.

The 1000th API call succeeded.

The 1001st API call returned:

text
HTTP 429


Response reason:

text
API call quota exceeded


 Conclusion

The API correctly allows usage up to the plan limit and rejects the next request with HTTP 429.


 3. AI Token Quota

 Requirement

Requests exceeding the tenant's AI-token quota must be rejected with HTTP 402.

 Test

The tenant was seeded with:

text
100000 billable tokens

A new request that would exceed the Free-plan token limit returned:

text
HTTP 402


Response reason:

text
AI token quota exceeded


 Conclusion

The token quota is enforced before a new usage event is created.


 4. Input Validation

Requirement

Invalid usage values must be rejected at the API boundary.

Test

A request was submitted with:

json
{
  "input_tokens": -100
}


The API returned:

text
HTTP 422 Unprocessable Content


Validation error:

text
Input should be greater than or equal to 0


Conclusion

Negative token values are rejected by Pydantic request validation before billing logic executes.

---

 5. AI Token Cost Calculation

Requirement

The billing engine must correctly handle:

- normal input tokens
- cached input tokens at a cheaper rate
- reasoning tokens as output
- output tokens
- integer money calculations

 Pinned project pricing

text
API call:             1 cent per call
Input:              300 cents per 1,000,000 tokens
Cached input:        75 cents per 1,000,000 tokens
Output:           1,500 cents per 1,000,000 tokens

 Test

Input:

text
input tokens:           1,000,000
cached input tokens:      200,000
reasoning tokens:         100,000
output tokens:            300,000


Calculation:

text
Billable input = 1,000,000 - 200,000
               = 800,000

Billable output = 100,000 reasoning + 300,000 output
                = 400,000

Cost:

text
Input cost:        800,000 × 300 / 1,000,000 = 240 cents
Cached cost:       200,000 × 75  / 1,000,000 = 15 cents
Output cost:       400,000 × 1500 / 1,000,000 = 600 cents

Total token cost = 855 cents


 Conclusion

Cached input is priced separately and reasoning tokens are included in the output-priced category rather than simply adding all token categories together.

---

6. Monthly Usage Rollup

 Requirement

`GET /usage/{tenant_id}` must roll up the tenant's usage for the current billing period and calculate its cost.

Test

The API returned:

```json
{
  "usage": {
    "api_calls": 2,
    "tokens": {
      "input_tokens": 2000,
      "cached_input_tokens": 400,
      "reasoning_tokens": 200,
      "output_tokens": 600,
      "total_billable_tokens": 2400
    }
  },
  "cost": {
    "api_call_cost_cents": 2,
    "input_cost_cents": 0,
    "cached_input_cost_cents": 0,
    "output_cost_cents": 1,
    "total_cost_cents": 3
  }
}


Conclusion

The usage endpoint rolls up persisted usage events and applies the same pinned pricing rules used by the billing service.



7. Stripe Checkout

Requirement

A tenant must be able to start a subscription Checkout flow.

Test

The project generated a mock Stripe Checkout session:

json
{
  "success": true,
  "tenant_id": "tenant-test-001",
  "checkout_session_id": "cs_test_mock_4815af6bde42",
  "checkout_url": "http://localhost:8000/mock-checkout/..."
}


 Stripe environment note

This project uses a Stripe-shaped mock/test-fixture implementation because a real Stripe account was not available for this environment.

The application preserves the required Checkout and webhook architecture while keeping external payment credentials out of the repository.

Conclusion

The Checkout flow is represented and connected to the subscription webhook flow without storing payment secrets.



 8. Checkout Webhook — Free to Pro

Requirement

A verified `checkout.session.completed` event must update the tenant's subscription.

 Test

A signed mock event was sent:

text
event type:
checkout.session.completed


Result:
json
{
  "received": true,
  "duplicate": false,
  "event_id": "evt_mock_checkout_001",
  "event_type": "checkout.session.completed"
}

Database state after processing:

text
tenant: tenant-test-001
plan:   pro
status: active
stripe subscription id: sub_mock