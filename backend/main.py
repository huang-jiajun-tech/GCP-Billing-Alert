from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

import models, schemas, crud, bigquery_client
from database import engine, get_db
from scheduler import start_scheduler, sync_billing_accounts, sync_usage_data
import auth

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Billing Alert System API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import threading
import logging
import sys

# Configure logging to output to both console and a file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def on_startup():
    start_scheduler()
    
    # Create default admin user if not exists
    db = next(get_db())
    admin = auth.get_user_by_username(db, "admin")
    if not admin:
        crud.create_user(db, schemas.UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin",
            role="admin"
        ))
        logger.info("Default admin user created.")

@app.get("/")
def read_root():
    return {"message": "Welcome to Billing Alert System API"}

# --- Auth & User Management APIs ---

@app.post("/api/auth/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    auth.log_audit(db, user.id, "LOGIN", "User logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.get("/api/users", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.post("/api/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    db_user = auth.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = crud.create_user(db=db, user=user)
    auth.log_audit(db, current_user.id, "CREATE_USER", f"Created user {new_user.username}")
    return new_user

@app.put("/api/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    updated_user = crud.update_user(db, user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    auth.log_audit(db, current_user.id, "UPDATE_USER", f"Updated user {updated_user.username}")
    return updated_user

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    deleted_user = crud.delete_user(db, user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    auth.log_audit(db, current_user.id, "DELETE_USER", f"Deleted user {deleted_user.username}")
    return {"message": "User deleted successfully"}

@app.get("/api/audit-logs", response_model=List[schemas.AuditLog])
def read_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    return crud.get_audit_logs(db, skip=skip, limit=limit)

# --- Sync Logs APIs ---

@app.get("/api/sync/logs", response_model=List[schemas.SyncLog])
def read_sync_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    return crud.get_sync_logs(db, skip=skip, limit=limit)

@app.post("/api/sync/usage")
def trigger_manual_sync(
    sync_req: schemas.SyncRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_admin_user)
):
    """
    Manually trigger usage data sync from BigQuery for a specific date range.
    """
    import threading
    
    # Create a sync log entry
    log_data = schemas.SyncLogCreate(
        sync_type="manual",
        target_start_date=sync_req.start_date,
        target_end_date=sync_req.end_date
    )
    sync_log = crud.create_sync_log(db, log_data)
    
    def run_sync(log_id: int, start_date: str, end_date: str):
        db_session = next(get_db())
        try:
            count = bigquery_client.fetch_and_store_usage_data(start_date, end_date)
            crud.update_sync_log(db_session, log_id, status="success", records_synced=count)
        except Exception as e:
            crud.update_sync_log(db_session, log_id, status="failed", error_message=str(e))
        finally:
            db_session.close()
            
    # Run in background
    threading.Thread(target=run_sync, args=(sync_log.id, sync_req.start_date, sync_req.end_date), daemon=True).start()
    
    auth.log_audit(db, current_user.id, "MANUAL_SYNC", f"Triggered manual sync for {sync_req.start_date} to {sync_req.end_date}")
    return {"message": "Manual sync started in the background", "log_id": sync_log.id}

# --- BigQuery Usage APIs ---

@app.get("/api/usage", response_model=List[dict])
def get_all_usage(
    start_date: str = None, 
    end_date: str = None, 
    project_id: str = None, 
    billing_account_id: str = None, 
    min_cost: float = 0,
    service_description: str = None,
    db: Session = Depends(get_db)
):
    """
    Get usage for projects with filters from PostgreSQL.
    """
    from datetime import datetime, timedelta
    
    if not end_date:
        end_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    if not start_date:
        start_date = end_date
        
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    usages = crud.get_daily_usage(db, start_dt, end_dt, project_id, billing_account_id, service_description)
    
    # Fetch billing accounts mapping
    accounts = crud.get_billing_accounts(db, limit=5000)
    billing_map = {acc.billing_account_id: acc.display_name for acc in accounts}
    
    # Fetch project info mapping
    project_infos = crud.get_all_project_infos(db)
    project_info_map = {pi.project_id: pi for pi in project_infos}
    
    # Aggregate data
    project_data = {}
    for u in usages:
        pid = u.project_id
        if pid not in project_data:
            b_id = u.billing_account_id
            p_info = project_info_map.get(pid)
            project_data[pid] = {
                "project_id": pid,
                "billing_account_id": b_id,
                "billing_name": billing_map.get(b_id, "Unknown"),
                "customer_name": p_info.customer_name if p_info else "Unknown",
                "sales_rep": p_info.sales_rep if p_info else "Unknown",
                "total_cost": 0.0,
                "currency": u.currency,
                "daily_costs": {}
            }
        date_str = u.usage_date.strftime('%Y-%m-%d')
        cost = round(u.cost, 2)
        # If multiple services match, sum them up for the day
        project_data[pid]["daily_costs"][date_str] = project_data[pid]["daily_costs"].get(date_str, 0) + cost
        project_data[pid]["total_cost"] += cost
        
    final_results = []
    for pid, data in project_data.items():
        data["total_cost"] = round(data["total_cost"], 2)
        data["cost"] = data["total_cost"]
        if any(c >= min_cost for c in data["daily_costs"].values()):
            final_results.append(data)
            
    return sorted(final_results, key=lambda x: x['total_cost'], reverse=True)

@app.get("/api/usage/trend", response_model=List[dict])
def get_usage_trend(
    start_date: str, 
    end_date: str, 
    project_id: str = None, 
    billing_account_id: str = None,
    min_cost: float = 0,
    service_description: str = None,
    db: Session = Depends(get_db)
):
    """
    Get daily usage trend over a time period from PostgreSQL.
    """
    from datetime import datetime
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    usages = crud.get_daily_usage(db, start_dt, end_dt, project_id, billing_account_id, service_description)
    
    trend_data = {}
    project_max_daily = {}
    
    for u in usages:
        date_str = u.usage_date.strftime('%Y-%m-%d')
        if date_str not in trend_data:
            trend_data[date_str] = {
                "date": date_str,
                "cost": 0.0,
                "currency": u.currency
            }
        
        pid = u.project_id
        cost = round(u.cost, 2)
        trend_data[date_str][pid] = trend_data[date_str].get(pid, 0) + cost
        
    # Calculate max daily cost per project
    for date_str, day_data in trend_data.items():
        for pid, cost in day_data.items():
            if pid not in ('date', 'cost', 'currency'):
                project_max_daily[pid] = max(project_max_daily.get(pid, 0), cost)
                
    valid_projects = {pid for pid, max_cost in project_max_daily.items() if max_cost >= min_cost}
    
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

@app.get("/api/usage/{project_id}", response_model=dict)
def get_project_usage(project_id: str, date: str = None):
    """
    Get daily usage for a specific project.
    """
    # This endpoint is currently not used by the frontend and was relying on the removed get_daily_usage function.
    # Returning a placeholder to avoid 500 errors if called.
    return {"message": "Endpoint deprecated. Please use /api/usage instead."}

# --- Alert Configuration APIs ---

def validate_alert_config(config):
    if config.dimension not in ["project", "billing"]:
        raise HTTPException(status_code=400, detail="dimension must be either 'project' or 'billing'")
        
    if config.alert_type not in ["absolute", "relative"]:
        raise HTTPException(status_code=400, detail="alert_type must be either 'absolute' or 'relative'")
    
    if config.alert_type == "relative":
        if not config.comparison_window:
            raise HTTPException(status_code=400, detail="comparison_window is required for relative alert type")
        if config.comparison_window not in ["week", "month"]:
            raise HTTPException(status_code=400, detail="comparison_window must be either 'week' or 'month'")
        if config.threshold_percentage is None:
            raise HTTPException(status_code=400, detail="threshold_percentage is required for relative alert type")
        if config.threshold_percentage <= 0:
            raise HTTPException(status_code=400, detail="threshold_percentage must be greater than 0")
    else:
        if config.threshold <= 0:
            raise HTTPException(status_code=400, detail="threshold must be greater than 0")

@app.get("/api/alerts", response_model=List[schemas.AlertConfig])
def read_alert_configs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    configs = crud.get_alert_configs(db, skip=skip, limit=limit)
    return configs

@app.get("/api/alerts/{config_id}", response_model=schemas.AlertConfig)
def read_alert_config(config_id: int, db: Session = Depends(get_db)):
    db_config = crud.get_alert_config(db, config_id=config_id)
    if db_config is None:
        raise HTTPException(status_code=404, detail="Alert configuration not found")
    return db_config

@app.post("/api/alerts", response_model=schemas.AlertConfig)
def create_alert_config(config: schemas.AlertConfigCreate, db: Session = Depends(get_db)):
    validate_alert_config(config)
    return crud.create_alert_config(db=db, config=config)

@app.put("/api/alerts/{config_id}", response_model=schemas.AlertConfig)
def update_alert_config(config_id: int, config: schemas.AlertConfigUpdate, db: Session = Depends(get_db)):
    validate_alert_config(config)
    db_config = crud.update_alert_config(db, config_id=config_id, config=config)
    if db_config is None:
        raise HTTPException(status_code=404, detail="Alert configuration not found")
    return db_config

@app.delete("/api/alerts/{config_id}")
def delete_alert_config(config_id: int, db: Session = Depends(get_db)):
    db_config = crud.delete_alert_config(db, config_id=config_id)
    if db_config is None:
        raise HTTPException(status_code=404, detail="Alert configuration not found")
    return {"message": "Alert configuration deleted successfully"}

@app.post("/api/alerts/test")
def test_alert_connection(test_req: schemas.AlertTestRequest):
    """
    Test the connectivity of the provided webhook URL or email.
    """
    from scheduler import send_webhook_alert, send_email_alert
    from datetime import datetime
    
    test_message = "🔔 这是一条来自 Billing Alert System 的测试告警消息，用于验证连通性。"
    test_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    results = []
    
    if test_req.webhook_url:
        try:
            send_webhook_alert(test_req.webhook_url, test_message, 0.0, test_date)
            results.append("Webhook test sent successfully.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook test failed: {str(e)}")
            
    if test_req.email:
        try:
            send_email_alert(test_req.email, test_message, 0.0, test_date)
            results.append("Email test sent successfully.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Email test failed: {str(e)}")
            
    if not results:
        raise HTTPException(status_code=400, detail="No webhook URL or email provided for testing.")
        
    return {"message": " ".join(results)}

@app.post("/api/alerts/trigger-check")
def trigger_alert_check(current_user: models.User = Depends(auth.get_current_user)):
    """
    Manually trigger the billing check and alert job.
    """
    from scheduler import check_billing_and_alert
    import threading
    
    # Run in background to avoid blocking the API response
    threading.Thread(target=check_billing_and_alert, daemon=True).start()
    
    return {"message": "Alert check job triggered successfully in the background."}

# --- Alert Incidents APIs ---

@app.get("/api/incidents", response_model=List[schemas.AlertIncident])
def read_alert_incidents(skip: int = 0, limit: int = 100, status: str = None, db: Session = Depends(get_db)):
    return crud.get_alert_incidents(db, skip=skip, limit=limit, status=status)

@app.post("/api/incidents/{incident_id}/handle", response_model=schemas.AlertIncident)
def handle_alert_incident(
    incident_id: int, 
    handle_data: schemas.AlertIncidentHandle, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    incident = crud.handle_alert_incident(db, incident_id, current_user.id, handle_data.handle_notes)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    auth.log_audit(db, current_user.id, "HANDLE_INCIDENT", f"Handled incident {incident_id} for project {incident.project_id}")
    return incident

@app.delete("/api/incidents")
def delete_alert_incidents(
    delete_req: schemas.AlertIncidentBatchDelete,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_admin_user)
):
    """
    Batch delete alert incidents. Only admins can perform this action.
    """
    if not delete_req.incident_ids:
        raise HTTPException(status_code=400, detail="No incident IDs provided")
        
    deleted_count = crud.delete_alert_incidents(db, delete_req.incident_ids)
    auth.log_audit(db, current_user.id, "DELETE_INCIDENTS", f"Deleted {deleted_count} alert incidents")
    return {"message": f"Successfully deleted {deleted_count} incidents", "deleted_count": deleted_count}

# --- Billing Accounts APIs ---

@app.get("/api/billing-accounts", response_model=List[schemas.BillingAccount])
def read_billing_accounts(skip: int = 0, limit: int = 5000, search: str = None, db: Session = Depends(get_db)):
    """
    Get all synced billing accounts.
    """
    return crud.get_billing_accounts(db, skip=skip, limit=limit, search=search)

@app.post("/api/billing-accounts/sync")
def trigger_billing_accounts_sync():
    """
    Manually trigger a sync of billing accounts from GCP.
    """
    threading.Thread(target=sync_billing_accounts, daemon=True).start()
    return {"message": "Sync triggered successfully in background"}
