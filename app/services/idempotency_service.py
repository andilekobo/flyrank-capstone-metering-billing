processed_requests = {}


def get_processed_request(idempotency_key: str):
    return processed_requests.get(idempotency_key)


def save_processed_request(idempotency_key: str, response: dict):
    processed_requests[idempotency_key] = response