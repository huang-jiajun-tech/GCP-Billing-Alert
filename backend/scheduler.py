import requests
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
import crud
import schemas
import bigquery_client
from datetime import datetime
from google.cloud import billing_v1
import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
import crud
import schemas
import bigquery_client
import requests
import google.auth
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

def get_access_token():
    """获取 Google Cloud API 的 Access Token"""
    scopes = ["https://www.googleapis.com/auth/cloud-billing.readonly"]
    # Do not force GOOGLE_APPLICATION_CREDENTIALS here if we want to use the default environment
    # like the original script did.
    credentials, project = google.auth.default(scopes=scopes)
    credentials.refresh(Request())
    return credentials.token

def sync_billing_accounts():
    """
    Job to sync billing accounts from GCP to local database using REST API
    """
    logger.info("Running billing accounts sync job via REST API...")
    
    try:
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        params = {
            "parent": "organizations/28496605279",
            "pageSize": 100
        }
        
        url = "https://cloudbilling.googleapis.com/v1/billingAccounts"
        page_count = 1
        count = 0
        
        db = SessionLocal()
        try:
            while True:
                logger.info(f"Fetching page {page_count} of billing accounts...")
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                accounts_in_page = data.get('billingAccounts', [])
                for account in accounts_in_page:
                    billing_id = account.get('name', '').replace('billingAccounts/', '')
                    billing_name = account.get('displayName', '')
                    
                    account_data = schemas.BillingAccountCreate(
                        billing_account_id=billing_id,
                        display_name=billing_name
                    )
                    crud.upsert_billing_account(db, account_data)
                    count += 1
                    
                page_token = data.get('nextPageToken')
                if not page_token or page_token == "":
                    break
                    
                params['pageToken'] = page_token
                page_count += 1
                
            logger.info(f"Successfully synced {count} billing accounts.")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error syncing billing accounts: {e}")

def send_webhook_alert(webhook_url: str, message_content: str, threshold: float, date: str, is_relative: bool = False):
    """
    Send alert to Webhook (e.g., WeChat Work / 企业微信)
    """
    if not webhook_url:
        return
        
    threshold_display = f"{threshold * 100:.1f}%" if is_relative else f"${threshold:.2f}"
    # Example payload for WeChat Work
    content = (
        f"## <font color=\"warning\">⚠️ GCP 费用超额告警</font>\n"
        f"**告警日期**：<font color=\"comment\">{date}</font>\n"
        f"**设定的告警阈值**：<font color=\"info\">{threshold_display}</font>\n\n"
        f"**告警详情**：\n"
        f"{message_content}"
    )
    
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Webhook sent: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send webhook: {e}")
        raise e

def send_email_alert(email: str, message_content: str, threshold: float, date: str, is_relative: bool = False):
    """
    Send alert to Email (Mock implementation for now)
    """
    if not email:
        return
    threshold_display = f"{threshold * 100:.1f}%" if is_relative else f"${threshold:.2f}"
    logger.info(f"Mock Email sent to {email}: {message_content} on {date} (Threshold: {threshold_display})")

def check_billing_and_alert():
    """
    Job to check billing and trigger alerts
    """
    logger.info("Running billing check job...")
    db = SessionLocal()
    try:
        # Get all active alert configs
        configs = crud.get_alert_configs(db)
        active_configs = [c for c in configs if c.is_active]
        
        if not active_configs:
            logger.info("No active alert configurations found.")
            return
            
        from datetime import datetime as dt
        
        for config in active_configs:
            days_to_check = config.time_range_days or 1
            
            # Calculate date range for this config
            # Billing data usually has 1 day delay, so end_date is yesterday
            end_dt = (datetime.utcnow() - timedelta(days=1)).date()
            start_dt = (datetime.utcnow() - timedelta(days=days_to_check)).date()
            
            # Determine query start date based on alert type
            query_start_dt = start_dt
            if config.alert_type == "relative":
                if config.comparison_window == "week":
                    query_start_dt = start_dt - timedelta(days=7)
                elif config.comparison_window == "month":
                    query_start_dt = start_dt - timedelta(days=30)
            
            # Fetch usages with optional service_description filter
            usages = crud.get_daily_usage(db, query_start_dt, end_dt, service_description=config.service_description)
            
            # Aggregate by project AND date to check daily threshold
            # Structure: { project_id: { date_str: daily_cost } }
            project_daily_costs = {}
            for u in usages:
                pid = u.project_id
                date_str = u.usage_date.strftime('%Y-%m-%d')
                if pid not in project_daily_costs:
                    project_daily_costs[pid] = {}
                project_daily_costs[pid][date_str] = project_daily_costs[pid].get(date_str, 0) + u.cost
                
            # Determine which projects to check for this config
            projects_to_check = config.project_ids if config.project_ids else list(project_daily_costs.keys())
            
            exceeded_projects = []
            for pid in projects_to_check:
                daily_costs = project_daily_costs.get(pid, {})
                
                exceeding_days = []
                
                # Check each day in the current check range
                current_date = start_dt
                while current_date <= end_dt:
                    date_str = current_date.strftime('%Y-%m-%d')
                    cost = daily_costs.get(date_str, 0.0)
                    
                    if config.alert_type == "relative":
                        # Calculate history date
                        if config.comparison_window == "week":
                            history_date = current_date - timedelta(days=7)
                        elif config.comparison_window == "month":
                            history_date = current_date - timedelta(days=30)
                        else:
                            history_date = None
                            
                        if history_date:
                            history_date_str = history_date.strftime('%Y-%m-%d')
                            history_cost = daily_costs.get(history_date_str, 0.0)
                            
                            # Handle missing or zero history data to avoid division by zero or false alerts
                            if history_cost > 0:
                                change_ratio = (cost - history_cost) / history_cost
                                if change_ratio > config.threshold_percentage:
                                    exceeding_days.append({
                                        "date": date_str,
                                        "cost": cost,
                                        "history_date": history_date_str,
                                        "history_cost": history_cost,
                                        "change_ratio": change_ratio
                                    })
                    else:
                        # Absolute threshold check
                        if cost > config.threshold:
                            exceeding_days.append({
                                "date": date_str,
                                "cost": cost
                            })
                            
                    current_date += timedelta(days=1)
                
                if exceeding_days:
                    # Check if there's a recently handled incident for this project to suppress alert
                    recent_handled = crud.get_recent_handled_incidents(db, pid, days=3)
                    if recent_handled:
                        logger.info(f"Alert suppressed for project {pid} due to recent handling.")
                        continue
                        
                    # Check if there's already a pending incident in the last 24 hours to avoid hourly spam
                    import models
                    recent_pending = db.query(models.AlertIncident).filter(
                        models.AlertIncident.project_id == pid,
                        models.AlertIncident.alert_config_id == config.id,
                        models.AlertIncident.status == "pending",
                        models.AlertIncident.created_at >= datetime.utcnow() - timedelta(hours=24)
                    ).first()
                    if recent_pending:
                        continue
                        
                    # Sort exceeding days by date descending to show the latest one
                    exceeding_days.sort(key=lambda x: x['date'], reverse=True)
                    latest_exceeding = exceeding_days[0]
                    
                    exceeded_project_info = {
                        "id": pid, 
                        "cost": latest_exceeding["cost"],
                        "date": latest_exceeding["date"]
                    }
                    if config.alert_type == "relative":
                        exceeded_project_info.update({
                            "history_date": latest_exceeding["history_date"],
                            "history_cost": latest_exceeding["history_cost"],
                            "change_ratio": latest_exceeding["change_ratio"]
                        })
                    exceeded_projects.append(exceeded_project_info)
                    
                    # Record the incident in DB
                    incident_data = schemas.AlertIncidentCreate(
                        alert_config_id=config.id,
                        project_id=pid,
                        cost=latest_exceeding["cost"],
                        threshold=config.threshold_percentage if config.alert_type == "relative" else config.threshold,
                        usage_date=latest_exceeding["date"]
                    )
                    crud.create_alert_incident(db, incident_data)
                    
            if exceeded_projects:
                logger.warning(f"ALERT: Config '{config.alert_name}' triggered for {len(exceeded_projects)} projects.")
                
                service_info = f" (服务: {config.service_description})" if config.service_description else ""
                
                if config.alert_type == "relative":
                    window_name = "同比上周" if config.comparison_window == "week" else "同比上月"
                    project_details = []
                    for p in exceeded_projects:
                        ratio_pct = p['change_ratio'] * 100
                        detail = (
                            f"> - {p['id']}: 当前费用 ${p['cost']:.2f} (日期: {p['date']}), "
                            f"历史费用 ${p['history_cost']:.2f} (日期: {p['history_date']}), "
                            f"涨幅: {ratio_pct:+.2f}%"
                        )
                        project_details.append(detail)
                    project_details_str = "\n".join(project_details)
                    
                    message_content = (
                        f"> 告警名称: {config.alert_name}{service_info}\n"
                        f"> 告警类型: 环比告警 ({window_name})\n"
                        f"> 设定阈值比例: {config.threshold_percentage * 100:.1f}%\n"
                        f"> 检查范围: 过去 {days_to_check} 天\n"
                        f"> 环比超标项目详情:\n{project_details_str}"
                    )
                    threshold_val = config.threshold_percentage
                else:
                    project_details = "\n".join([f"> - {p['id']}: ${p['cost']:.2f} (日期: {p['date']})" for p in exceeded_projects])
                    message_content = f"> 告警名称: {config.alert_name}{service_info}\n> 检查范围: 过去 {days_to_check} 天\n> 超标项目及日费用:\n{project_details}"
                    threshold_val = config.threshold
                
                if config.webhook_url:
                    send_webhook_alert(
                        config.webhook_url, 
                        message_content,
                        threshold_val, 
                        f"{start_dt} to {end_dt}",
                        is_relative=(config.alert_type == "relative")
                    )
                    
                if config.email:
                    send_email_alert(
                        config.email,
                        message_content,
                        threshold_val,
                        f"{start_dt} to {end_dt}",
                        is_relative=(config.alert_type == "relative")
                    )
    finally:
        db.close()

def sync_usage_data():
    """
    Job to sync usage data from BigQuery to local database
    Fetches the last 3 days of data.
    """
    logger.info("Running usage data sync job...")
    end_date = datetime.utcnow().strftime('%Y-%m-%d')
    start_date = (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%d')
    
    db = SessionLocal()
    try:
        # Create a sync log entry
        log_data = schemas.SyncLogCreate(
            sync_type="auto",
            target_start_date=start_date,
            target_end_date=end_date
        )
        sync_log = crud.create_sync_log(db, log_data)
        
        try:
            count = bigquery_client.fetch_and_store_usage_data(start_date, end_date)
            crud.update_sync_log(db, sync_log.id, status="success", records_synced=count)
        except Exception as e:
            crud.update_sync_log(db, sync_log.id, status="failed", error_message=str(e))
            
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Run billing check every hour on the hour (e.g., 7:00, 8:00)
    scheduler.add_job(check_billing_and_alert, 'cron', minute=0)
    
    # Run billing accounts sync every day at 16:00 UTC (which is 00:00 Beijing Time)
    scheduler.add_job(sync_billing_accounts, 'cron', hour=16, minute=0)
    
    # Run usage data sync every 6 hours on the hour (e.g., 0:00, 6:00, 12:00, 18:00)
    scheduler.add_job(sync_usage_data, 'cron', hour='*/6', minute=0)
    
    scheduler.start()
    logger.info("Scheduler started.")
