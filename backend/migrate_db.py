import psycopg2
import os

DB_HOST = os.getenv("DB_HOST", "34.81.147.109")
DB_PORT = os.getenv("DB_PORT", "15432")
DB_NAME = os.getenv("DB_NAME", "Billing")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "Baidao123..")

def migrate():
    print(f"Connecting to database {DB_NAME} on {DB_HOST}:{DB_PORT}...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    conn.autocommit = True
    cursor = conn.cursor()

    print("Adding new columns to alert_configs table if they do not exist...")
    
    # Add alert_type
    cursor.execute("""
        ALTER TABLE alert_configs 
        ADD COLUMN IF NOT EXISTS alert_type VARCHAR NOT NULL DEFAULT 'absolute';
    """)
    
    # Add comparison_window
    cursor.execute("""
        ALTER TABLE alert_configs 
        ADD COLUMN IF NOT EXISTS comparison_window VARCHAR;
    """)
    
    # Add threshold_percentage
    cursor.execute("""
        ALTER TABLE alert_configs 
        ADD COLUMN IF NOT EXISTS threshold_percentage DOUBLE PRECISION;
    """)

    print("Adding dimension and billing_account_ids columns to alert_configs table...")
    cursor.execute("""
        ALTER TABLE alert_configs 
        ADD COLUMN IF NOT EXISTS dimension VARCHAR NOT NULL DEFAULT 'project';
    """)
    cursor.execute("""
        ALTER TABLE alert_configs 
        ADD COLUMN IF NOT EXISTS billing_account_ids JSONB;
    """)

    print("Adding billing_account_id column and modifying project_id in alert_incidents table...")
    cursor.execute("""
        ALTER TABLE alert_incidents 
        ADD COLUMN IF NOT EXISTS billing_account_id VARCHAR;
    """)
    cursor.execute("""
        ALTER TABLE alert_incidents 
        ALTER COLUMN project_id DROP NOT NULL;
    """)

    print("Database migration completed successfully.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    migrate()
