-- Index for funding round lookups
CREATE INDEX investments_by_funding_round 
ON investments(funding_round_id);

-- Index for funded object queries
CREATE INDEX investments_by_funded_object 
ON investments(funded_object_id);

-- Index for investor queries
CREATE INDEX investments_by_investor 
ON investments(investor_object_id);

-- Index for temporal queries
CREATE INDEX investments_by_created_at 
ON investments(created_at DESC);

-- Composite index for investor timeline
CREATE INDEX investments_by_investor_timeline 
ON investments(investor_object_id, created_at DESC);
