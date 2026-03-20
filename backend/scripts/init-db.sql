-- Pre-create alembic_version with wider column (default varchar(32) is too short for our descriptive revision IDs)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(128) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Create the application role (unprivileged, for RLS enforcement)
-- The owner role (mastercrm_owner) runs migrations; app_user runs the application
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user LOGIN PASSWORD 'appuserpassword';
    END IF;
END $$;

GRANT CONNECT ON DATABASE mastercrm TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
