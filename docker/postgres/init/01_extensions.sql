-- =========================================================
-- Glovo UZ — Postgres bootstrap
-- Runs once, automatically, on first container start (empty data volume),
-- via the official postgres image's /docker-entrypoint-initdb.d mechanism.
-- =========================================================

-- UUID generation for external-facing resource primary keys (Section 12)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Trigram index support for merchant/product search (Section 22.3 /search/)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- btree_gist enables combining equality + range/exclusion constraints,
-- useful for service-zone / working-hours overlap checks (Section 12.2/12.3)
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- unaccent helps Uzbek/Russian search be diacritic-insensitive (Section 6)
CREATE EXTENSION IF NOT EXISTS "unaccent";
