-- V2: Add environment column to system_metrics
ALTER TABLE system_metrics
  ADD COLUMN IF NOT EXISTS environment VARCHAR(50);

-- Backfill environment from api_logs where possible
UPDATE system_metrics sm
SET environment = al.environment
FROM api_logs al
WHERE sm.api_log_id = al.id
  AND sm.environment IS NULL
  AND al.environment IS NOT NULL;

-- Set default for any remaining NULLs
UPDATE system_metrics
SET environment = 'production'
WHERE environment IS NULL;
