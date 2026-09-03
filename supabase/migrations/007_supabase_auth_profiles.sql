-- ============================================================
-- Supabase Auth <-> profiles integration
--
-- 1. Add columns used by the app (email/phone/business info) that
--    older migrations did not create on `profiles`.
-- 2. Auto-create a `profiles` row whenever an auth user signs up and
--    keep email/phone in sync when the auth user record changes.
-- 3. Backfill profiles for auth users that existed before this migration.
-- ============================================================

-- 1. Missing profile columns (safe to re-run)
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS business_name TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS business_type TEXT;

-- 2. Auto-create / sync profile rows from auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (auth_user_id, name, email, phone, preferred_language)
    VALUES (
        NEW.id,
        COALESCE(
            NEW.raw_user_meta_data ->> 'name',
            NEW.raw_user_meta_data ->> 'full_name',
            NULLIF(TRIM(COALESCE(NEW.raw_user_meta_data ->> 'first_name', '') || ' ' ||
                        COALESCE(NEW.raw_user_meta_data ->> 'last_name', '')), '')
        ),
        NEW.email,
        NEW.phone,
        COALESCE(NEW.raw_user_meta_data ->> 'preferred_language', 'en')
    )
    ON CONFLICT (auth_user_id) DO NOTHING;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.sync_user_profile()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    UPDATE public.profiles
    SET email = NEW.email,
        phone = NEW.phone,
        updated_at = now()
    WHERE auth_user_id = NEW.id
      AND (profiles.email IS DISTINCT FROM NEW.email
           OR profiles.phone IS DISTINCT FROM NEW.phone);
    RETURN NEW;
END;
$$;

-- Re-create triggers idempotently
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

DROP TRIGGER IF EXISTS on_auth_user_updated ON auth.users;
CREATE TRIGGER on_auth_user_updated
    AFTER UPDATE OF email, phone, raw_user_meta_data ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.sync_user_profile();

-- Keep updated_at current on profile edits made through the app
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_profiles_updated_at ON profiles;
CREATE TRIGGER set_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- 3. Backfill profiles for auth users that existed before this migration.
--    (Keeps `name` empty so the app's onboarding screen can collect it.)
INSERT INTO public.profiles (auth_user_id, email, phone)
SELECT u.id, u.email, u.phone
FROM auth.users u
ON CONFLICT (auth_user_id) DO NOTHING;
