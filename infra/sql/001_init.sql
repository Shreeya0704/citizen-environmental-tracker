CREATE TABLE IF NOT EXISTS measurements (
  id            BIGSERIAL PRIMARY KEY,
  source        TEXT NOT NULL,
  s3_key        TEXT NOT NULL,
  row_index     INTEGER NOT NULL,
  location      TEXT,
  city          TEXT,
  country       TEXT,
  parameter     TEXT,
  value         DOUBLE PRECISION,
  unit          TEXT,
  latitude      DOUBLE PRECISION,
  longitude     DOUBLE PRECISION,
  time_utc      TIMESTAMPTZ
);
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_measurements_file_row'
  ) THEN
    ALTER TABLE measurements
    ADD CONSTRAINT uq_measurements_file_row UNIQUE (s3_key, row_index);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_measurements_time ON measurements (time_utc DESC);
CREATE INDEX IF NOT EXISTS idx_measurements_city_param ON measurements (city, parameter);
