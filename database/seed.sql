-- CASHNET Database Seed Data (Reference Metadata)
-- Synthetic Indian Geographic Clusters and Metadata Configuration

-- Reference metadata for synthetic location clusters across Indian Major Metros
INSERT INTO locations (location_id, location_name, location_type, city, region, latitude, longitude, area_cluster_id, synthetic_location_group, is_active, created_at)
VALUES
    ('SYNTH_LOC_MUM_001', 'SYNTH_ATM_MUM_BKC_01', 'atm', 'Mumbai', 'Maharashtra', 19.067430, 72.868730, 'CLUSTER_MUM_BKC', 'WEST_ZONE_METRO', TRUE, '2026-06-01T00:00:00Z'),
    ('SYNTH_LOC_MUM_002', 'SYNTH_ATM_MUM_ANDHERI_01', 'atm', 'Mumbai', 'Maharashtra', 19.119700, 72.846400, 'CLUSTER_MUM_SUBURB', 'WEST_ZONE_METRO', TRUE, '2026-06-01T00:00:00Z'),
    ('SYNTH_LOC_DEL_001', 'SYNTH_ATM_DEL_CP_01', 'atm', 'New Delhi', 'Delhi NCR', 28.631500, 77.216700, 'CLUSTER_DEL_CENTRAL', 'NORTH_ZONE_METRO', TRUE, '2026-06-01T00:00:00Z'),
    ('SYNTH_LOC_BLR_001', 'SYNTH_ATM_BLR_KORAMANGALA_01', 'atm', 'Bengaluru', 'Karnataka', 12.935200, 77.624500, 'CLUSTER_BLR_SOUTH', 'SOUTH_ZONE_METRO', TRUE, '2026-06-01T00:00:00Z')
ON CONFLICT (location_id) DO NOTHING;
