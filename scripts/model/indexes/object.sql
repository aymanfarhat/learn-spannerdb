-- Index for entity lookups
CREATE INDEX object_by_entity 
ON object(entity_type, entity_id);

-- Index for hierarchical queries
CREATE INDEX object_by_parent 
ON object(parent_id);

-- Index for name searches
CREATE INDEX object_by_name 
ON object(normalized_name);

-- Index for status queries
CREATE INDEX object_by_status 
ON object(status);

-- Index for regional queries
CREATE INDEX object_by_location 
ON object(country_code, state_code, city);

-- Index for funding queries
CREATE INDEX object_by_funding 
ON object(funding_total_usd DESC);
