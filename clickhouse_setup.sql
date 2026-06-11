CREATE TABLE IF NOT EXISTS crm_clients_kafka (
                                                 before String,
                                                 after String,
                                                 op String
) ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'crm.public.clients',
    kafka_group_name = 'clickhouse_consumer',
    kafka_format = 'JSONEachRow';

CREATE TABLE IF NOT EXISTS crm_clients (
                                           id Int32,
                                           email String,
                                           full_name String,
                                           version UInt64,
                                           deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(version)
ORDER BY id;

CREATE MATERIALIZED VIEW IF NOT EXISTS crm_clients_mv TO crm_clients AS
SELECT
    JSONExtractInt(after, 'id') as id,
    JSONExtractString(after, 'email') as email,
    JSONExtractString(after, 'full_name') as full_name,
    JSONExtractUInt(after, 'updated_at') as version,
    if(op = 'd', 1, 0) as deleted
FROM crm_clients_kafka
WHERE after != '';

CREATE TABLE IF NOT EXISTS crm_telemetry_kafka (
                                                   before String,
                                                   after String,
                                                   op String
) ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'crm.public.telemetry',
    kafka_group_name = 'clickhouse_consumer',
    kafka_format = 'JSONEachRow';

CREATE TABLE IF NOT EXISTS crm_telemetry (
                                             id Int32,
                                             client_id Int32,
                                             session_date Date,
                                             gestures_count Int32,
                                             avg_confidence Float32,
                                             avg_battery Float32,
                                             version UInt64,
                                             deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(version)
ORDER BY id;

CREATE MATERIALIZED VIEW IF NOT EXISTS crm_telemetry_mv TO crm_telemetry AS
SELECT
    JSONExtractInt(after, 'id') as id,
    JSONExtractInt(after, 'client_id') as client_id,
    JSONExtractString(after, 'session_date') as session_date,
    JSONExtractInt(after, 'gestures_count') as gestures_count,
    JSONExtractFloat(after, 'avg_confidence') as avg_confidence,
    JSONExtractFloat(after, 'avg_battery') as avg_battery,
    JSONExtractUInt(after, 'updated_at') as version,
    if(op = 'd', 1, 0) as deleted
FROM crm_telemetry_kafka
WHERE after != '';