import json
import os
import sys
from datetime import datetime

import pika
import psycopg2
from minio import Minio
from psycopg2.extras import execute_values


def s3_client() -> Minio:
    endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
    access = os.getenv("MINIO_ROOT_USER", "minioadmin")
    secret = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    secure = endpoint.startswith("https://")
    host = endpoint.replace("http://", "").replace("https://", "")
    return Minio(host, access_key=access, secret_key=secret, secure=secure)


def db_conn():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL missing")
    return psycopg2.connect(url)


def normalize(openaq_json, s3_key):
    rows = []
    for idx, item in enumerate(openaq_json.get("results", [])):
        coords = item.get("coordinates") or {}
        date_info = item.get("date") or {}
        utc_str = date_info.get("utc")
        ts = None
        if utc_str:
            try:
                ts = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            except Exception:
                ts = None
        rows.append(
            (
                "openaq",
                s3_key,
                idx,
                item.get("location"),
                item.get("city"),
                item.get("country"),
                item.get("parameter"),
                item.get("value"),
                item.get("unit"),
                coords.get("latitude"),
                coords.get("longitude"),
                ts,
            )
        )
    return rows


def handle_message(channel, method, properties, body):
    try:
        message = json.loads(body.decode("utf-8"))
        if message.get("source", "openaq") != "openaq":
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        bucket = message["s3_bucket"]
        s3_key = message["s3_key"]

        client = s3_client()
        response = client.get_object(bucket, s3_key)
        payload = json.loads(response.read().decode("utf-8"))
        try:
            response.close()
            response.release_conn()
        except Exception:
            pass

        rows = normalize(payload, s3_key)
        if rows:
            with db_conn() as conn, conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO measurements (
                        source, s3_key, row_index, location, city, country,
                        parameter, value, unit, latitude, longitude, time_utc
                    )
                    VALUES %s
                    ON CONFLICT (s3_key, row_index) DO NOTHING
                    """,
                    rows,
                )
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:  # noqa: BLE001
        print(f"worker_error: {exc}", file=sys.stderr)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    queue = os.getenv("INGEST_QUEUE", "ingestion_raw")

    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue, on_message_callback=handle_message)
    print("validation-worker: listening...", flush=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()
