-- Latest reading per (city, parameter), keeping value/unit/time
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_city_param_latest AS
SELECT DISTINCT ON (city, parameter)
  city, country, parameter, unit, value, time_utc
FROM measurements
WHERE city IS NOT NULL AND parameter IS NOT NULL
ORDER BY city, parameter, time_utc DESC;

CREATE INDEX IF NOT EXISTS idx_mv_cpl_param_city ON mv_city_param_latest (parameter, city);
CREATE INDEX IF NOT EXISTS idx_mv_cpl_value_desc ON mv_city_param_latest (parameter, value DESC NULLS LAST);

-- Daily counts by parameter (for simple trends)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_param_daily_counts AS
SELECT date_trunc('day', time_utc) AS day, parameter, COUNT(*)::bigint AS count
FROM measurements
WHERE time_utc IS NOT NULL
GROUP BY 1, 2;

CREATE INDEX IF NOT EXISTS idx_mv_pdc_param_day ON mv_param_daily_counts (parameter, day DESC);
