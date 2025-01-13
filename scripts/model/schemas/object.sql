CREATE TABLE object (
    id STRING(36) NOT NULL,
    entity_type STRING(50),
    entity_id INT64,
    parent_id FLOAT64,
    name STRING(255),
    normalized_name STRING(255),
    permalink STRING(255),
    category_code STRING(50),
    status STRING(50),
    founded_at TIMESTAMP,
    closed_at TIMESTAMP,
    domain STRING(255),
    homepage_url STRING(512),
    twitter_username STRING(50),
    logo_url STRING(512),
    logo_width INT64,
    logo_height INT64,
    short_description STRING(MAX),
    description STRING(MAX),
    overview STRING(MAX),
    tag_list STRING(MAX),
    country_code STRING(2),
    state_code STRING(2),
    city STRING(100),
    region STRING(100),
    first_investment_at TIMESTAMP,
    last_investment_at TIMESTAMP,
    investment_rounds INT64,
    invested_companies INT64,
    first_funding_at TIMESTAMP,
    last_funding_at TIMESTAMP,
    funding_rounds INT64,
    funding_total_usd FLOAT64,
    first_milestone_at TIMESTAMP,
    last_milestone_at TIMESTAMP,
    milestones INT64,
    relationships INT64,
    created_by STRING(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) PRIMARY KEY(id)