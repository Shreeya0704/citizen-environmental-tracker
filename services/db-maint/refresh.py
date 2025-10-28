import os
import sys
import psycopg2

def main():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL missing", file=sys.stderr)
        sys.exit(1)
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute("REFRESH MATERIALIZED VIEW mv_city_param_latest;")
        cur.execute("REFRESH MATERIALIZED VIEW mv_param_daily_counts;")
        conn.commit()
    print("REFRESH OK", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"REFRESH ERROR: {e}", file=sys.stderr)
        sys.exit(1)
