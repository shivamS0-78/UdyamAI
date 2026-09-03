-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Ensure profiles table has all columns required by the SQLAlchemy model.
-- Columns are added conditionally so this is safe to run repeatedly.
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'profiles') THEN
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email TEXT;
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS phone TEXT;
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS business_name TEXT;
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS business_type TEXT;
    END IF;
END
$$;
