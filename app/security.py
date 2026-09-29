import hmac


def valid_demo_api_secret(expected: str, supplied: str) -> bool:
    return bool(expected and supplied) and hmac.compare_digest(expected, supplied)