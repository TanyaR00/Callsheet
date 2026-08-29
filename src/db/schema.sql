-- illustrative schema for ClickHouse OLAP + Vector Search
CREATE TABLE IF NOT EXISTS scene_cost_history (
    scene_comp_id UUID DEFAULT generateUUIDv4(),
    int_ext LowCardinality(String),
    time_of_day LowCardinality(String),
    cast_count UInt16,
    vfx_density Float32,
    location_type String,
    actual_cost Float64,
    shoot_duration_hours Float32,
    feature_vector Array(Float32),
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (int_ext, time_of_day, cast_count);
