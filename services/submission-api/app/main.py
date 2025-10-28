import json
import os
import time
from datetime import datetime
from typing import List, Optional

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Query, Request, Response
from minio import Minio
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQ_COUNT = Counter(
    "submission_api_requests_total",
    "Total HTTP requests",
    ["endpoint", "method", "status"],
)
REQ_LATENCY = Histogram(
    "submission_api_request_seconds", "Request latency seconds", ["endpoint", "method"]
)

BUCKET = os.getenv("S3_BUCKET", "ingestion")
PREFIX = os.getenv("INGEST_PREFIX", "openaq/raw/")
ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cstracker:cstracker@cstr_postgres:5432/cstracker",
)


def _s3() -> Minio:
    secure = ENDPOINT.startswith("https://")
    host = ENDPOINT.replace("http://", "").replace("https://", "")
    return Minio(host, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=secure)


def _db():
    return psycopg2.connect(DB_URL)


app = FastAPI(title="Submission API", version="0.5.0")


@app.middleware("http")
async def _metrics_middleware(request: Request, call_next):
    start = time.time()
    endpoint = request.url.path
    method = request.method
    status = "500"
    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    finally:
        duration = time.time() - start
        REQ_LATENCY.labels(endpoint=endpoint, method=method).observe(duration)
        REQ_COUNT.labels(endpoint=endpoint, method=method, status=status).inc()


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def healthz():
    try:
        next(_s3().list_objects(BUCKET, prefix=PREFIX, recursive=True), None)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"minio_unreachable: {exc}") from exc

    try:
        with _db() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"db_unreachable: {exc}") from exc

    return {"status": "ok"}


@app.get("/ingestions/latest")
def latest(n: int = Query(5, ge=1, le=50)):
    client = _s3()
    try:
        objects = list(client.list_objects(BUCKET, prefix=PREFIX, recursive=True))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"list_failed: {exc}") from exc

    objects.sort(key=lambda obj: obj.last_modified, reverse=True)
    items = []
    for obj in objects[:n]:
        count = None
        try:
            resp = client.get_object(BUCKET, obj.object_name)
            data = json.loads(resp.read().decode("utf-8"))
            count = len(data.get("results", []))
        except Exception:
            pass
        finally:
            try:
                resp.close()
                resp.release_conn()
            except Exception:
                pass
        items.append(
            {
                "key": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified.isoformat(),
                "records": count,
            }
        )
    return {"items": items}


@app.get("/measurements")
def measurements(
    city: Optional[str] = None,
    parameter: Optional[str] = None,
    start: Optional[str] = Query(
        None, description="ISO 8601 UTC, e.g., 2025-10-26T00:00:00Z"
    ),
    end: Optional[str] = Query(None, description="ISO 8601 UTC"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    clauses: List[str] = []
    args: List[object] = []

    if city:
        clauses.append("city = %s")
        args.append(city)
    if parameter:
        clauses.append("parameter = %s")
        args.append(parameter)
    if start:
        try:
            datetime.fromisoformat(start.replace("Z", "+00:00"))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, "invalid start datetime") from exc
        clauses.append("time_utc >= %s")
        args.append(start)
    if end:
        try:
            datetime.fromisoformat(end.replace("Z", "+00:00"))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, "invalid end datetime") from exc
        clauses.append("time_utc <= %s")
        args.append(end)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT id, source, city, country, parameter, value, unit, latitude, longitude, time_utc
        FROM measurements
        {where}
        ORDER BY time_utc DESC NULLS LAST
        LIMIT %s OFFSET %s
    """
    args.extend([limit, offset])

    with _db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, args)
        rows = cur.fetchall()
        return {"items": rows, "count": len(rows)}


@app.get("/observations")
def observations(
    taxon_id: Optional[int] = None,
    country: Optional[str] = None,
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    clauses = ["observed_at >= (now() AT TIME ZONE 'UTC') - (INTERVAL '1 day' * %s)"]
    args: List[object] = [days]
    if taxon_id is not None:
        clauses.append("taxon_id = %s")
        args.append(taxon_id)
    if country:
        clauses.append("place_country = %s")
        args.append(country)
    where = "WHERE " + " AND ".join(clauses)
    sql = f"""
        SELECT id, taxon_id, scientific_name, common_name, latitude, longitude,
               place_city, place_country, quality_grade, observed_at
        FROM observations
        {where}
        ORDER BY observed_at DESC NULLS LAST
        LIMIT %s OFFSET %s
    """
    args.extend([limit, offset])

    with _db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, args)
        rows = cur.fetchall()
        return {"items": rows, "count": len(rows)}
