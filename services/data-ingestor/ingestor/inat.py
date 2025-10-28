import os
from datetime import datetime, timezone
import httpx

BASE = "https://api.inaturalist.org/v1/observations"

def fetch_inat():
    if str(os.getenv("INAT_ENABLED", "false")).lower() != "true":
        return None
    per_page = int(os.getenv("INAT_PER_PAGE", "50"))
    taxon_id = os.getenv("INAT_TAXON_ID") or None
    place_id = os.getenv("INAT_PLACE_ID") or None

    params = {
        "order": "desc",
        "order_by": "created_at",
        "per_page": per_page,
    }
    if taxon_id:
        params["taxon_id"] = taxon_id
    if place_id:
        params["place_id"] = place_id

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(BASE, params=params)
        resp.raise_for_status()
        payload = resp.json()

    results = payload.get("results", [])
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    s3_key = f"inat/raw/{ts}.json"
    return payload, results, s3_key
