CREATE TABLE users (
    id STRING(36) NOT NULL,
    name STRING(MAX),
    email STRING(MAX),
    created_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
    updated_at TIMESTAMP OPTIONS (allow_commit_timestamp=true)
) PRIMARY KEY (id)
