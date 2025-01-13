CREATE TABLE investment (
    id INT64 NOT NULL,
    funding_round_id INT64 NOT NULL,
    funded_object_id STRING(36) NOT NULL,
    investor_object_id STRING(36) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
) PRIMARY KEY(id)
