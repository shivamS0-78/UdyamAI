-- Backfill PostGIS geography columns from latitude/longitude.
--
-- Why: `find_within_radius` (backend/app/geo/radius.py) filters on the geography
-- column alone — `ST_DWithin(geom, point, radius)` — so PostgreSQL can use the GiST
-- indexes created in 006_rls_and_indexes.sql. It previously wrapped the column in
-- `COALESCE(geom, make_point(longitude, latitude))`, which made every radius query a
-- sequential scan.
--
-- The locations importer used to write latitude/longitude onto a village without
-- touching `geom`, so rows can exist that carry valid coordinates but no geography
-- point. Those rows would silently drop out of every nearby-* lookup, so the
-- geography column has to be derived once from the coordinates that are already there.
--
-- Safe to re-run: it only touches rows where the geography column is NULL.

UPDATE villages
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
WHERE geom IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;

UPDATE businesses
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
WHERE geom IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;

UPDATE markets
SET geog = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
WHERE geog IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;

UPDATE infrastructure
SET geog = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
WHERE geog IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;


-- Verify the spatial indexes 006 relies on actually exist. Missing ones turn every
-- radius query into a sequential scan on the whole table.
CREATE INDEX IF NOT EXISTS idx_villages_geom ON villages USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_businesses_geom ON businesses USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_markets_geog ON markets USING GIST (geog);
CREATE INDEX IF NOT EXISTS idx_infrastructure_geog ON infrastructure USING GIST (geog);


-- RAG retrieval now ranks with the pgvector `<=>` operator, which this HNSW index
-- serves. Wrapped so a Postgres/pgvector version without HNSW support only warns
-- instead of aborting the script; retrieval stays correct either way (it degrades to
-- a sequential scan over document_chunks).
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;

    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public' AND indexname = 'idx_document_chunks_embedding_hnsw'
    ) THEN
        RAISE NOTICE 'HNSW index already present, skipping';
    ELSE
        CREATE INDEX idx_document_chunks_embedding_hnsw
        ON document_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        RAISE NOTICE 'Created HNSW index on document_chunks.embedding';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Could not create HNSW index (pgvector <0.5 or missing extension): %', SQLERRM;
        RAISE NOTICE 'Retrieval still works, but scans every chunk instead of using an index.';
END $$;


-- Confirm the plan: this should report an "Index Scan"/"Bitmap Index Scan", never a
-- "Seq Scan" on villages. Run it manually after applying this file:
--
--   EXPLAIN SELECT id FROM villages
--   WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(73.8567, 18.5204), 4326), 25000);
