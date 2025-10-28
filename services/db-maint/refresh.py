import os
import sys
import psycopg2
from psycopg2 import sql


def retention(conn: psycopg2.extensions.connection) -> None:
    keep_meas = int(os.getenv("RETAIN_MEASUREMENTS_DAYS", "90"))
    keep_obs = int(os.getenv("RETAIN_OBSERVATIONS_DAYS", "365"))

    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM measurements "
            "WHERE time_utc < (now() AT TIME ZONE 'UTC') - (INTERVAL '1 day' * %s);",
            (keep_meas,),
        )
        cur.execute(
            "DELETE FROM observations "
            "WHERE observed_at < (now() AT TIME ZONE 'UTC') - (INTERVAL '1 day' * %s);",
            (keep_obs,),
        )
    conn.commit()

    vac_url = os.getenv("DATABASE_URL")
    if not vac_url:
        raise RuntimeError("DATABASE_URL missing for VACUUM")

    vac_conn = psycopg2.connect(vac_url, options="-c statement_timeout=0")
    try:
        vac_conn.autocommit = True
        with vac_conn.cursor() as cur:
            cur.execute("VACUUM (ANALYZE) measurements;")
            cur.execute("VACUUM (ANALYZE) observations;")
    finally:
        vac_conn.close()

    print("RETENTION OK", flush=True)


def refresh_matviews(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        for name in ("mv_city_param_latest", "mv_param_daily_counts"):
            cur.execute("SELECT to_regclass(%s);", (name,))
            exists = cur.fetchone()[0]
            if exists:
                cur.execute(sql.SQL("REFRESH MATERIALIZED VIEW {}").format(sql.Identifier(name)))
    conn.commit()
    print("REFRESH OK", flush=True)


def main() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL missing", file=sys.stderr)
        sys.exit(1)

    with psycopg2.connect(url) as conn:
        retention(conn)
        refresh_matviews(conn)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"DB-MAINT ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
