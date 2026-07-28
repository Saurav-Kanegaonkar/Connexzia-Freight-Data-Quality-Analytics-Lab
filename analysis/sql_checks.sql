-- 1. Shipment primary-key control
SELECT shipment_id, COUNT(*) AS duplicate_count FROM shipments GROUP BY shipment_id HAVING COUNT(*) > 1;

-- 2. Event referential-integrity control
SELECT e.event_id FROM shipment_events e LEFT JOIN shipments s ON e.shipment_id = s.shipment_id WHERE s.shipment_id IS NULL;

-- 3. Required-field completeness control
SELECT shipment_id FROM shipments WHERE eta_missing_flag = 1 OR pod_missing_flag = 1;

-- 4. Reporting refresh SLA control (dialect-specific timestamp arithmetic may vary)
SELECT run_id FROM report_runs WHERE status <> 'success' OR completed_at > scheduled_at + INTERVAL '60 minutes';
