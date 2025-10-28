import os
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

from .storage import put_json
from .queue import publish
from .inat import fetch_inat

OPENAQ_BASE = "https://api.openaq.org/v2/measurements"


def ingest_openaq():
    if str(os.getenv("OPENAQ_ENABLED", "true")).lower() != "true":
        return 0
    limit = int(os.getenv("OPENAQ_LIMIT", "100"))
    params = {"limit": limit, "sort": "desc", "order_by": "datetime"}

    country = os.getenv("OPENAQ_COUNTRY") or None
    city = os.getenv("OPENAQ_CITY") or None
    if country:
        params["country"] = country
    if city:
        params["city"] = city

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(OPENAQ_BASE, params=params)
        resp.raise_for_status()
        payload = resp.json()

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
    return len(results)


def ingest_inaturalist():
    data = fetch_inat()
    if not data:
        return 0
    payload, results, s3_key = data
    s3_bucket = os.getenv("S3_BUCKET", "ingestion")
    put_json(s3_bucket, s3_key, payload)
    publish(
        os.getenv("INGEST_QUEUE", "ingestion_raw"),
        {
            "source": "inaturalist",
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "records": len(results),
            "ts": s3_key.split("/")[-1].replace(".json", ""),
        },
    )
    return len(results)


def main() -> None:
    load_dotenv()
    ingest_openaq()
    ingest_inaturalist()
    print("STEP 5 OK")


if __name__ == "__main__":
    main()
