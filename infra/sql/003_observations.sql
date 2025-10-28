CREATE TABLE IF NOT EXISTS observations (
  id             BIGSERIAL PRIMARY KEY,
  source         TEXT NOT NULL,
  s3_key         TEXT NOT NULL,
  row_index      INTEGER NOT NULL,
  taxon_id       BIGINT,
  scientific_name TEXT,
  common_name     TEXT,
  latitude       DOUBLE PRECISION,
  longitude      DOUBLE PRECISION,
  observed_at    TIMESTAMPTZ,
  place_city     TEXT,
  place_country  TEXT,
  quality_grade  TEXT
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'uq_observations_file_row'
  ) THEN
    ALTER TABLE observations ADD CONSTRAINT uq_observations_file_row UNIQUE (s3_key, row_index);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_observations_time ON observations (observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_observations_taxon ON observations (taxon_id);
