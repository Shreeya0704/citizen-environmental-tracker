import io
import json
import os
from minio import Minio


def _client():
    endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    region = os.getenv("S3_REGION")
    secure = endpoint.startswith("https://")
    host = endpoint.replace("http://", "").replace("https://", "")
    return Minio(
        host,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
        region=region,
    )

def put_json(bucket: str, key: str, payload: dict) -> None:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    client = _client()
    # bucket may already exist (created in STEP 4)
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except Exception:
        # If race or permission issues, continue; put_object will still raise if truly broken
        pass
    client.put_object(
        bucket_name=bucket,
        object_name=key,
        data=io.BytesIO(data),
        length=len(data),
        content_type="application/json",
    )
