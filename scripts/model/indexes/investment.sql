-- Index for funding round lookups
CREATE INDEX investment_by_funding_round 
ON investment(funding_round_id);

-- Index for funded object queries
CREATE INDEX investment_by_funded_object 
ON investment(funded_object_id);

-- Index for investor queries
CREATE INDEX investment_by_investor 
ON investment(investor_object_id);

-- Index for temporal queries
CREATE INDEX investment_by_created_at 
ON investment(created_at DESC);

-- Composite index for investor timeline
CREATE INDEX investment_by_investor_timeline 
ON investment(investor_object_id, created_at DESC);
