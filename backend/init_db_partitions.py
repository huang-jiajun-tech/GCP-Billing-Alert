import psycopg2
from datetime import datetime
from dateutil.relativedelta import relativedelta

DB_HOST = "192.168.200.124"
DB_PORT = "5432"
DB_NAME = "Billing"
DB_USER = "postgres"
DB_PASS = "Baidao123.."

def init_partitions():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # 1. Drop existing table
    print("Dropping existing daily_usage table...")
    cursor.execute("DROP TABLE IF EXISTS daily_usage CASCADE;")

    # 2. Create partitioned table
    print("Creating partitioned daily_usage table...")
    create_table_sql = """
    CREATE TABLE daily_usage (
        id SERIAL,
        project_id VARCHAR NOT NULL,
        billing_account_id VARCHAR,
        service_description VARCHAR,
        usage_date DATE NOT NULL,
        cost DOUBLE PRECISION NOT NULL,
        currency VARCHAR NOT NULL DEFAULT 'USD',
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id, usage_date),
        CONSTRAINT uix_daily_usage UNIQUE (project_id, billing_account_id, service_description, usage_date)
    ) PARTITION BY RANGE (usage_date);
    """
    cursor.execute(create_table_sql)

    # 3. Create partitions for 2024 to 2027
    print("Creating monthly partitions...")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2028, 1, 1)
    
    current_date = start_date
    while current_date < end_date:
        next_date = current_date + relativedelta(months=1)
        partition_name = f"daily_usage_{current_date.strftime('%Y_%m')}"
        
        create_partition_sql = f"""
        CREATE TABLE IF NOT EXISTS {partition_name} 
        PARTITION OF daily_usage 
        FOR VALUES FROM ('{current_date.strftime('%Y-%m-%d')}') TO ('{next_date.strftime('%Y-%m-%d')}');
        """
        cursor.execute(create_partition_sql)
        print(f"Created partition: {partition_name}")
        
        current_date = next_date

    print("Database partitioning completed successfully.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_partitions()
