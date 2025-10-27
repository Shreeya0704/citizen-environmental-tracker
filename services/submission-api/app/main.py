import os, json
from typing import List
from fastapi import FastAPI, HTTPException, Query
from minio import Minio

BUCKET = os.getenv("S3_BUCKET", "ingestion")
PREFIX = os.getenv("INGEST_PREFIX", "openaq/raw/")
ENDPOINT = os.getenv("S3_ENDPOINT", "http://cstr_minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

def _client() -> Minio:
    secure = ENDPOINT.startswith("https://")
    host = ENDPOINT.replace("http://", "").replace("https://", "")
    return Minio(host, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=secure)

app = FastAPI(title="Submission API", version="0.1.0")

@app.get("/healthz")
def healthz():
    try:
        c = _client()
        next(c.list_objects(BUCKET, prefix=PREFIX, recursive=True), None)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, f"minio_unreachable: {e}")

@app.get("/ingestions/latest")
def latest(n: int = Query(5, ge=1, le=50)):
    c = _client()
    try:
        objs = list(c.list_objects(BUCKET, prefix=PREFIX, recursive=True))
    except Exception as e:
        raise HTTPException(500, f"list_failed: {e}")

    objs.sort(key=lambda o: o.last_modified, reverse=True)
    items = []
    for o in objs[:n]:
        count = None
        try:
            resp = c.get_object(BUCKET, o.object_name)
            data = json.loads(resp.read().decode("utf-8"))
            count = len(data.get("results", []))
        except Exception:
            pass
        finally:
            try:
                resp.close(); resp.release_conn()
            except Exception:
                pass
        items.append({
            "key": o.object_name,
            "size": o.size,
            "last_modified": o.last_modified.isoformat(),
            "records": count
        })
    return {"items": items}
