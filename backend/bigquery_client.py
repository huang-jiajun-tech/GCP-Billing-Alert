import os
from google.cloud import bigquery
from datetime import datetime, timedelta
import random
from database import SessionLocal
import crud

# Set credentials from the copied JSON file
cred_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
if os.path.exists(cred_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

# Initialize BigQuery client
try:
    client = bigquery.Client()
    USE_MOCK = False
except Exception as e:
    print(f"Warning: Could not initialize BigQuery client. Using mock data. Error: {e}")
    USE_MOCK = True

# The specific table ID provided
TABLE_ID = "billing-export-total.baidao_billing.gcp_billing_export_v1_016A40_628771_B28C06"

def fetch_and_store_usage_data(start_date: str, end_date: str):
    """
    Fetch usage data from BigQuery and store it in PostgreSQL.
    """
    if USE_MOCK:
        print("Using mock data, skipping BQ fetch.")
        return
        
    query_params = [
        bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", f"{start_date} 00:00:00 UTC"),
        bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", f"{end_date} 23:59:59 UTC"),
        bigquery.ScalarQueryParameter("start_date_str", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date_str", "DATE", end_date),
    ]
    
    query = f"""
        SELECT
            project.id as project_id,
            billing_account_id,
            service.description as service_description,
            DATE(DATETIME(usage_start_time, "America/Los_Angeles")) as usage_date,
            SUM(cost) as daily_cost,
            currency
        FROM
            `{TABLE_ID}`
        WHERE
            _PARTITIONTIME >= @start_date AND _PARTITIONTIME <= @end_date
            AND DATE(DATETIME(usage_start_time, "America/Los_Angeles")) BETWEEN @start_date_str AND @end_date_str
            AND project.id IS NOT NULL
        GROUP BY
            project.id, billing_account_id, service_description, usage_date, currency
    """
    
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        import schemas
        usages_to_insert = []
        for row in results:
            # Convert date to datetime for schema
            usage_date_dt = datetime.combine(row.usage_date, datetime.min.time())
            usages_to_insert.append(schemas.DailyUsageCreate(
                project_id=row.project_id,
                billing_account_id=row.billing_account_id,
                service_description=row.service_description,
                usage_date=usage_date_dt,
                cost=round(row.daily_cost, 2),
                currency=row.currency
            ))
            
        count = 0
        if usages_to_insert:
            db = SessionLocal()
            try:
                crud.upsert_daily_usage_batch(db, usages_to_insert)
                count = len(usages_to_insert)
                print(f"Successfully synced {count} usage records to DB.")
            finally:
                db.close()
        return count
                
    except Exception as e:
        print(f"Error fetching/storing BigQuery usage data: {e}")
        raise e

def get_all_projects_daily_usage(start_date: str = None, end_date: str = None, project_id: str = None, billing_account_id: str = None, min_cost: float = 0, service_description: str = None):
    """
    Fetch usage cost for projects with filters, including daily breakdown.
    """
    if not end_date:
        end_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    if not start_date:
        start_date = end_date
        
    if USE_MOCK:
        projects = ["project-alpha", "project-beta", "project-gamma", "data-warehouse-prod"]
        if project_id:
            projects = [project_id]
        
        results = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        delta = end - start
        
        for p in projects:
            daily_costs = {}
            total_cost = 0.0
            for i in range(delta.days + 1):
                day = start + timedelta(days=i)
                day_str = day.strftime('%Y-%m-%d')
                cost = round(random.uniform(10.0, 5000.0), 2)
                daily_costs[day_str] = cost
                total_cost += cost
                
            if any(c >= min_cost for c in daily_costs.values()):
                results.append({
                    "project_id": p,
                    "billing_account_id": billing_account_id or "012345-6789AB-CDEF01",
                    "billing_name": "Mock Billing Account",
                    "cost": round(total_cost, 2),
                    "total_cost": round(total_cost, 2),
                    "currency": "USD",
                    "daily_costs": daily_costs
                })
        return sorted(results, key=lambda x: x['total_cost'], reverse=True)
        
    query_params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ]
    
    filters = []
    if project_id:
        filters.append("AND project.id = @project_id")
        query_params.append(bigquery.ScalarQueryParameter("project_id", "STRING", project_id))
    else:
        filters.append("AND project.id IS NOT NULL")
        
    if billing_account_id:
        filters.append("AND billing_account_id = @billing_account_id")
        query_params.append(bigquery.ScalarQueryParameter("billing_account_id", "STRING", billing_account_id))
        
    if service_description:
        filters.append("AND service.description = @service_description")
        query_params.append(bigquery.ScalarQueryParameter("service_description", "STRING", service_description))
        
    filter_str = " ".join(filters)
    
    query = f"""
        SELECT
            project.id as project_id,
            billing_account_id,
            DATE(DATETIME(usage_start_time, "America/Los_Angeles")) as usage_date,
            SUM(cost) as daily_cost,
            currency
        FROM
            `{TABLE_ID}`
        WHERE
            DATE(billing_partition_time) BETWEEN @start_date AND DATE_ADD(@end_date, INTERVAL 5 DAY)
            AND DATE(DATETIME(usage_start_time, "America/Los_Angeles")) BETWEEN @start_date AND @end_date
            {filter_str}
        GROUP BY
            project.id, billing_account_id, usage_date, currency
    """
    
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        # Fetch billing accounts mapping from DB
        db = SessionLocal()
        billing_map = {}
        try:
            accounts = crud.get_billing_accounts(db, limit=1000)
            billing_map = {acc.billing_account_id: acc.display_name for acc in accounts}
        finally:
            db.close()
        
        project_data = {}
        for row in results:
            pid = row.project_id
            if pid not in project_data:
                b_id = row.billing_account_id
                project_data[pid] = {
                    "project_id": pid,
                    "billing_account_id": b_id,
                    "billing_name": billing_map.get(b_id, "Unknown"),
                    "total_cost": 0.0,
                    "currency": row.currency,
                    "daily_costs": {}
                }
            date_str = row.usage_date.strftime('%Y-%m-%d')
            cost = round(row.daily_cost, 2)
            project_data[pid]["daily_costs"][date_str] = cost
            project_data[pid]["total_cost"] += cost
            
        final_results = []
        for pid, data in project_data.items():
            data["total_cost"] = round(data["total_cost"], 2)
            data["cost"] = data["total_cost"]  # For backward compatibility
            if any(c >= min_cost for c in data["daily_costs"].values()):
                final_results.append(data)
                
        return sorted(final_results, key=lambda x: x['total_cost'], reverse=True)
    except Exception as e:
        print(f"Error querying BigQuery: {e}")
        return []

def get_usage_trend(start_date: str, end_date: str, project_id: str = None, billing_account_id: str = None, min_cost: float = 0, service_description: str = None):
    """
    Fetch daily usage trend over a time period, broken down by project.
    Only includes projects that have at least one day with cost >= min_cost.
    """
    if USE_MOCK:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        delta = end - start
        
        projects = ["project-alpha", "project-beta", "project-gamma"]
        if project_id:
            projects = [project_id]
            
        results = []
        for i in range(delta.days + 1):
            day = start + timedelta(days=i)
            day_data = {
                "date": day.strftime('%Y-%m-%d'),
                "cost": 0, # Total cost for the day
                "currency": "USD"
            }
            for p in projects:
                p_cost = round(random.uniform(100.0, 5000.0), 2)
                day_data[p] = p_cost
                day_data["cost"] += p_cost
            day_data["cost"] = round(day_data["cost"], 2)
            results.append(day_data)
        
        # Note: Mock data logic doesn't easily support min_cost filtering across days without regenerating.
        # Keeping it simple for mock.
        return results

    query_params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ]
    
    filters = []
    if project_id:
        filters.append("AND project.id = @project_id")
        query_params.append(bigquery.ScalarQueryParameter("project_id", "STRING", project_id))
    else:
        filters.append("AND project.id IS NOT NULL")
        
    if billing_account_id:
        filters.append("AND billing_account_id = @billing_account_id")
        query_params.append(bigquery.ScalarQueryParameter("billing_account_id", "STRING", billing_account_id))
        
    if service_description:
        filters.append("AND service.description = @service_description")
        query_params.append(bigquery.ScalarQueryParameter("service_description", "STRING", service_description))
        
    filter_str = " ".join(filters)
    
    query = f"""
        SELECT
            DATE(DATETIME(usage_start_time, "America/Los_Angeles")) as usage_date,
            project.id as project_id,
            SUM(cost) as daily_cost,
            currency
        FROM
            `{TABLE_ID}`
        WHERE
            DATE(billing_partition_time) BETWEEN @start_date AND DATE_ADD(@end_date, INTERVAL 5 DAY)
            AND DATE(DATETIME(usage_start_time, "America/Los_Angeles")) BETWEEN @start_date AND @end_date
            {filter_str}
        GROUP BY
            usage_date, project.id, currency
        ORDER BY
            usage_date ASC, daily_cost DESC
    """
    
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        # Aggregate data by date
        trend_data = {}
        project_max_daily = {}
        
        for row in results:
            date_str = row.usage_date.strftime('%Y-%m-%d')
            if date_str not in trend_data:
                trend_data[date_str] = {
                    "date": date_str,
                    "cost": 0.0,
                    "currency": row.currency
                }
            
            pid = row.project_id
            cost = round(row.daily_cost, 2)
            trend_data[date_str][pid] = cost
            # Track the max daily cost for this project
            project_max_daily[pid] = max(project_max_daily.get(pid, 0), cost)
            
        # Filter projects that don't meet min_cost threshold on any day
        valid_projects = {pid for pid, max_cost in project_max_daily.items() if max_cost >= min_cost}
            
        # Format final output, excluding invalid projects
        final_results = []
        for date_str in sorted(trend_data.keys()):
            day_data = trend_data[date_str]
            new_day_data = {
                "date": day_data["date"],
                "cost": 0.0,
                "currency": day_data["currency"]
            }
            
            for pid in valid_projects:
                if pid in day_data:
                    new_day_data[pid] = day_data[pid]
                    new_day_data["cost"] += day_data[pid]
                    
            new_day_data["cost"] = round(new_day_data["cost"], 2)
            final_results.append(new_day_data)
            
        return final_results
    except Exception as e:
        print(f"Error querying BigQuery trend: {e}")
        return []
