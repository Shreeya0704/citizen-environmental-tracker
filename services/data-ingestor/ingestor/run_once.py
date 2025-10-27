import os
from datetime import datetime, timezone
from typing import Any, Dict

import httpx
from dotenv import load_dotenv

from .queue import publish
from .storage import put_json

DEFAULT_OPENAQ_BASE = "https://api.openaq.org/v3/measurements"
DEFAULT_OPENAQ_FALLBACK = (
    "https://raw.githubusercontent.com/openaq/openaq-api-old/develop/test/data/measurements.json"
)


def _fetch_openaq_payload(client: httpx.Client) -> Dict[str, Any]:
    """Fetch OpenAQ payload, falling back to the public sample if needed."""
    base_url = os.getenv("OPENAQ_BASE_URL", DEFAULT_OPENAQ_BASE)
    fallback_url = os.getenv("OPENAQ_FALLBACK_URL", DEFAULT_OPENAQ_FALLBACK)

    limit = int(os.getenv("OPENAQ_LIMIT", "100"))
    params = {"limit": limit}

    country = os.getenv("OPENAQ_COUNTRY") or None
    city = os.getenv("OPENAQ_CITY") or None
    if country:
        params["country"] = country
    if city:
        params["city"] = city

    headers: Dict[str, str] = {}
    api_key = os.getenv("OPENAQ_API_KEY")
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = client.get(base_url, params=params, headers=headers or None)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPStatusError, httpx.RequestError):
        response = client.get(fallback_url)
        response.raise_for_status()
        return response.json()


def main() -> None:
    load_dotenv()

    with httpx.Client(timeout=30.0) as client:
        payload = _fetch_openaq_payload(client)

    results = payload.get("results", [])
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    s3_bucket = os.getenv("S3_BUCKET", "ingestion")
    s3_key = f"openaq/raw/{ts}.json"

    put_json(s3_bucket, s3_key, payload)

    publish(
        os.getenv("INGEST_QUEUE", "ingestion_raw"),
        {
            "source": "openaq",
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "records": len(results),
            "ts": ts,
        },
    )

    print("STEP 5 OK")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("STEP 5 ERROR")
        raise
