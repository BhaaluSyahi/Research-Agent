-- Seed: search_strategy
-- Run after migration 002. Safe to re-run (INSERT ... ON CONFLICT DO NOTHING).

INSERT INTO search_strategy (topic, display_name, search_queries, crawl_frequency_hours)
VALUES
('floods',            'Flood Relief',       '[{"query":"NGO flood relief India","weight":1.0},{"query":"community flood rescue India","weight":0.8}]', 6),
('drought',           'Drought Response',   '[{"query":"drought relief NGO India","weight":1.0},{"query":"water scarcity village India","weight":0.8}]', 12),
('healthcare',        'Rural Healthcare',   '[{"query":"mobile health NGO rural India","weight":1.0}]', 24),
('disaster',          'Disaster Relief',    '[{"query":"disaster response NGO India","weight":1.0}]', 6),
('welfare',           'Social Welfare',     '[{"query":"community welfare NGO India","weight":1.0}]', 24),
('education',         'Education Access',   '[{"query":"education NGO tribal India","weight":1.0}]', 48),
('livelihood',        'Livelihood Support', '[{"query":"livelihood NGO farmer India","weight":1.0}]', 48),
('environment',       'Environment',        '[{"query":"environment conservation NGO India","weight":1.0}]', 48),
('regional_south',    'South India',        '[{"query":"NGO volunteer help Kerala Karnataka Tamil Nadu","weight":1.0}]', 12),
('regional_northeast','Northeast India',    '[{"query":"NGO volunteer help Assam Meghalaya Manipur","weight":1.0}]', 12)
ON CONFLICT (topic) DO NOTHING;
