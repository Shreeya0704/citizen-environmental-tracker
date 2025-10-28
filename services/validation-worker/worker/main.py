import json
import os
import sys
from datetime import datetime

import pika
import psycopg2
from minio import Minio
from psycopg2.extras import execute_values


def s3_client():
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


def normalize_openaq(payload, s3_key):
    rows = []
    for idx, item in enumerate(payload.get("results", [])):
        location = item.get("location")
        city = item.get("city")
        country = item.get("country")
        parameter = item.get("parameter")
        value = item.get("value")
        unit = item.get("unit")
        coords = item.get("coordinates") or {}
        lat = coords.get("latitude")
        lon = coords.get("longitude")
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
                location,
                city,
                country,
                parameter,
                value,
                unit,
                lat,
                lon,
                ts,
            )
        )
    return rows


def normalize_inat(payload, s3_key):
    rows = []
    for idx, item in enumerate(payload.get("results", [])):
        taxon = item.get("taxon") or {}
        taxon_id = taxon.get("id")
        scientific_name = taxon.get("name")
        common_name = taxon.get("preferred_common_name") or item.get("species_guess")

        lat = lon = None
        geojson = item.get("geojson")
        if isinstance(geojson, dict):
            coords = geojson.get("coordinates")
            if isinstance(coords, (list, tuple)) and len(coords) == 2:
                lon, lat = coords[0], coords[1]
        if lat is None or lon is None:
            loc = item.get("location") or ""
            if "," in loc:
                try:
                    lat, lon = [float(x.strip()) for x in loc.split(",", 1)]
                except Exception:
                    lat = lon = None

        observed = item.get("time_observed_at") or item.get("observed_on") or item.get("created_at")
        ts = None
        if observed:
            try:
                ts = datetime.fromisoformat(observed.replace("Z", "+00:00"))
            except Exception:
                ts = None

        place_city = item.get("place_guess")
        place_country = item.get("place_country_name")
        quality = item.get("quality_grade")

        rows.append(
            (
                "inaturalist",
                s3_key,
                idx,
                taxon_id,
                scientific_name,
                common_name,
                lat,
                lon,
                ts,
                place_city,
                place_country,
                quality,
            )
        )
    return rows


def handle_message(ch, method, props, body):
    try:
        message = json.loads(body.decode("utf-8"))
        bucket = message["s3_bucket"]
        s3_key = message["s3_key"]
        source = message.get("source", "openaq")

        client = s3_client()
        response = client.get_object(bucket, s3_key)
        payload = json.loads(response.read().decode("utf-8"))
        try:
            response.close()
            response.release_conn()
        except Exception:
            pass

        with db_conn() as conn, conn.cursor() as cur:
            if source == "openaq":
                rows = normalize_openaq(payload, s3_key)
                if rows:
                    execute_values(
                        cur,
                        """
                        INSERT INTO measurements
                            (source, s3_key, row_index, location, city, country, parameter, value, unit, latitude, longitude, time_utc)
                        VALUES %s
                        ON CONFLICT (s3_key, row_index) DO NOTHING
                        """,
                        rows,
                    )
            elif source == "inaturalist":
                rows = normalize_inat(payload, s3_key)
                if rows:
                    execute_values(
                        cur,
                        """
                        INSERT INTO observations
                            (source, s3_key, row_index, taxon_id, scientific_name, common_name, latitude, longitude, observed_at, place_city, place_country, quality_grade)
                        VALUES %s
                        ON CONFLICT (s3_key, row_index) DO NOTHING
                        """,
                        rows,
                    )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:  # noqa: BLE001
        print(f"worker_error: {exc}", file=sys.stderr)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@cstr_rabbitmq:5672/")
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
