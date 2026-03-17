-- Create the application role (unprivileged, for RLS enforcement)
-- The owner role (mastercrm_owner) runs migrations; app_user runs the application
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user LOGIN PASSWORD 'appuserpassword';
    END IF;
END $$;

GRANT CONNECT ON DATABASE mastercrm TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
