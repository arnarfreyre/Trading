
-- See all unique sectors
select distinct t.industry
from tickers t;






-- Query to DROP ALL TABLES (BE CAREFUL!)
-- This will delete all tables and their data permanently
DROP TABLE IF EXISTS calendar_events;
DROP TABLE IF EXISTS upgrades_downgrades;
DROP TABLE IF EXISTS growth_estimates;
DROP TABLE IF EXISTS eps_trends;
DROP TABLE IF EXISTS revenue_estimates;
DROP TABLE IF EXISTS earnings_estimates;
DROP TABLE IF EXISTS analyst_recommendations;
DROP TABLE IF EXISTS forward_estimates;
DROP TABLE IF EXISTS tickers;



