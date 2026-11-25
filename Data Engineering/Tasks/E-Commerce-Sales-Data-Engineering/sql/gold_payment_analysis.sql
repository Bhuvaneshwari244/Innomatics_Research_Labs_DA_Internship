-- ============================================================
-- Gold layer table: workspace.ecommerce.gold_payment_analysis
-- DDL captured via SHOW CREATE TABLE from the live Unity Catalog.
-- Aggregates DELIVERED orders only.
-- ============================================================

CREATE TABLE workspace.ecommerce.gold_payment_analysis (
  payment_mode STRING COLLATE UTF8_BINARY,
  orders BIGINT,
  revenue BIGINT,
  avg_transaction_value DOUBLE,
  contribution_pct DECIMAL(27,2))
USING delta
CLUSTER BY AUTO
TBLPROPERTIES (
  'delta.checkpoint.writeStatsAsJson' = 'false',
  'delta.checkpoint.writeStatsAsStruct' = 'true',
  'delta.checkpointPolicy' = 'v2',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableInCommitTimestamps' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.inCommitTimestamp' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.feature.v2Checkpoint' = 'supported',
  'delta.parquet.compression.codec' = 'zstd',
  'delta.parquet.format.version' = '2.12.0',
  'delta.parquet.format.version.afe.internal' = '2.12.0')

