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

def get_comparison_days(window: str) -> int:
    if window == "week":
        return 7
    elif window == "month":
        return 30
    try:
        return int(window)
    except (ValueError, TypeError):
        return 7 # default fallback

def get_window_display_name(window: str) -> str:
    if window == "week":
        return "同比上周"
    elif window == "month":
        return "同比上月"
    try:
        days = int(window)
        return f"环比前 {days} 天"
    except (ValueError, TypeError):
        return "环比"

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
        
    if message_content.startswith("# 🔴") or message_content.startswith("### 🔴"):
        # 已经是完整美化格式的卡片消息
        content = message_content
    elif message_content.startswith("🔔"):
        # 系统测试通知
        content = (
            f"# 🔴 GCP 费用超标告警\n\n"
            f"> 系统连接测试\n\n"
            f"**测试日期**\n"
            f"{date}\n\n"
            f"**测试内容**\n"
            f"{message_content}"
        )
    else:
        # 兼容性回退
        threshold_display = f"{threshold * 100:.1f}%" if is_relative else f"${threshold:.2f}"
        content = (
            f"# 🔴 GCP 费用超标告警\n\n"
            f"> 告警通知\n\n"
            f"**告警阈值**\n"
            f"🟠 {threshold_display}\n\n"
            f"**告警日期**\n"
            f"{date}\n\n"
            f"**详细内容**\n"
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
    logger.info("Running billing check job...")
    db = SessionLocal()
    try:
        # 获取基础数据字典用于补全通知信息
        billing_accounts = crud.get_billing_accounts(db, limit=5000)
        billing_name_map = {acc.billing_account_id: acc.display_name for acc in billing_accounts}
        
        project_infos = crud.get_all_project_infos(db)
        project_customer_map = {pi.project_id: pi.customer_name for pi in project_infos}

        configs = crud.get_alert_configs(db)
        active_configs = [c for c in configs if c.is_active]
        
        if not active_configs:
            logger.info("No active alert configurations found.")
            return
            
        for config in active_configs:
            days_to_check = config.time_range_days or 1
            end_dt = (datetime.utcnow() - timedelta(days=1)).date()
            start_dt = (datetime.utcnow() - timedelta(days=days_to_check)).date()
            
            query_start_dt = start_dt
            if config.alert_type == "relative":
                comp_days = get_comparison_days(config.comparison_window)
                query_start_dt = start_dt - timedelta(days=comp_days)
            
            # 1. 抓取该时段的每日花费记录
            usages = crud.get_daily_usage(db, query_start_dt, end_dt, service_description=config.service_description)
            
            if config.dimension == "billing":
                # ==========================================
                # Billing 维度告警判定
                # ==========================================
                billing_daily_costs = {}
                billing_project_costs = {} # 记录项目占比用

                for u in usages:
                    bid = u.billing_account_id
                    if not bid:
                        continue
                    date_str = u.usage_date.strftime('%Y-%m-%d')
                    
                    if bid not in billing_daily_costs:
                        billing_daily_costs[bid] = {}
                    billing_daily_costs[bid][date_str] = billing_daily_costs[bid].get(date_str, 0.0) + u.cost

                    # 记录同一 Billing 下项目的花费
                    if bid not in billing_project_costs:
                        billing_project_costs[bid] = {}
                    if date_str not in billing_project_costs[bid]:
                        billing_project_costs[bid][date_str] = {}
                    billing_project_costs[bid][date_str][u.project_id] = billing_project_costs[bid][date_str].get(u.project_id, 0.0) + u.cost

                billings_to_check = config.billing_account_ids if config.billing_account_ids else list(billing_daily_costs.keys())
                exceeded_billings = []

                for bid in billings_to_check:
                    daily_costs = billing_daily_costs.get(bid, {})
                    exceeding_days = []
                    current_date = start_dt
                    
                    while current_date <= end_dt:
                        date_str = current_date.strftime('%Y-%m-%d')
                        cost = daily_costs.get(date_str, 0.0)
                        
                        if config.alert_type == "relative":
                            comp_days = get_comparison_days(config.comparison_window)
                            history_date = current_date - timedelta(days=comp_days)
                            history_date_str = history_date.strftime('%Y-%m-%d')
                            history_cost = daily_costs.get(history_date_str, 0.0)
                            
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
                            if cost > config.threshold:
                                exceeding_days.append({
                                    "date": date_str,
                                    "cost": cost
                                })
                        current_date += timedelta(days=1)

                    if exceeding_days:
                        # 抑制 24 小时内的重复未处理 pending 告警
                        import models
                        recent_pending = db.query(models.AlertIncident).filter(
                            models.AlertIncident.billing_account_id == bid,
                            models.AlertIncident.alert_config_id == config.id,
                            models.AlertIncident.status == "pending",
                            models.AlertIncident.created_at >= datetime.utcnow() - timedelta(hours=24)
                        ).first()
                        if recent_pending:
                            continue

                        exceeding_days.sort(key=lambda x: x['date'], reverse=True)
                        latest_exceeding = exceeding_days[0]
                        latest_date_str = latest_exceeding["date"]

                        # 统计提取当日 Top 3 消费项目
                        proj_costs = billing_project_costs.get(bid, {}).get(latest_date_str, {})
                        sorted_projs = sorted(proj_costs.items(), key=lambda x: x[1], reverse=True)
                        top_projects = []
                        for pid, pcost in sorted_projs[:3]:
                            top_projects.append({
                                "project_id": pid,
                                "cost": pcost,
                                "percentage": (pcost / latest_exceeding["cost"] * 100) if latest_exceeding["cost"] > 0 else 0
                            })

                        exceeded_billing_info = {
                            "id": bid,
                            "cost": latest_exceeding["cost"],
                            "date": latest_date_str,
                            "top_projects": top_projects
                        }
                        if config.alert_type == "relative":
                            exceeded_billing_info.update({
                                "history_date": latest_exceeding["history_date"],
                                "history_cost": latest_exceeding["history_cost"],
                                "change_ratio": latest_exceeding["change_ratio"]
                            })
                        exceeded_billings.append(exceeded_billing_info)

                        # 创建 Incident 记录
                        incident_data = schemas.AlertIncidentCreate(
                            alert_config_id=config.id,
                            project_id=None,
                            billing_account_id=bid,
                            cost=latest_exceeding["cost"],
                            threshold=config.threshold_percentage if config.alert_type == "relative" else config.threshold,
                            usage_date=latest_date_str
                        )
                        crud.create_alert_incident(db, incident_data)

                if exceeded_billings:
                    logger.warning(f"ALERT: Billing Config '{config.alert_name}' triggered for {len(exceeded_billings)} accounts.")
                    service_info = f" (服务: {config.service_description})" if config.service_description else ""
                    threshold_val = config.threshold_percentage if config.alert_type == "relative" else config.threshold

                    billing_account_names = billing_name_map
                    billing_details_list = []
                    for b in exceeded_billings:
                        bname = billing_account_names.get(b['id'], "未知 Billing 账号")
                        if config.alert_type == "relative":
                            ratio_pct = b['change_ratio'] * 100
                            card_item = (
                                f"## 💳 `{b['id']}` ({bname})\n"
                                f"> 💰 单日费用：<font color=\"warning\">${b['cost']:.2f}</font>\n"
                                f"> 📈 费用涨幅：<font color=\"warning\">{ratio_pct:+.2f}%</font>\n"
                                f"> 📜 历史费用：${b['history_cost']:.2f}\n"
                                f"> 📅 费用日期：{b['date']}"
                            )
                        else:
                            card_item = (
                                f"## 💳 `{b['id']}` ({bname})\n"
                                f"> 💰 单日费用：<font color=\"warning\">${b['cost']:.2f}</font>\n"
                                f"> 📅 费用日期：{b['date']}"
                            )
                        
                        top_projs_str_list = []
                        for idx, p in enumerate(b['top_projects']):
                            top_projs_str_list.append(f"> {idx+1}. `{p['project_id']}` : **${p['cost']:.2f}** ({p['percentage']:.1f}%)")
                        
                        if top_projs_str_list:
                            card_item += "\n> 🔝 Top 消费项目：\n" + "\n".join(top_projs_str_list)
                        else:
                            card_item += "\n> 🔝 Top 消费项目：无"
                            
                        billing_details_list.append(card_item)
                    
                    billing_details_all = "\n\n".join(billing_details_list)
                    
                    threshold_display = f"{config.threshold_percentage * 100:.1f}%" if config.alert_type == "relative" else f"${config.threshold:.2f}"
                    desc_text = config.service_description if config.service_description else config.alert_name
                    message_content = (
                        f"# 🔴 GCP 费用超标告警\n\n"
                        f"> {desc_text}\n\n"
                        f"**告警阈值**\n"
                        f"🟠 {threshold_display}\n\n"
                        f"**告警日期**\n"
                        f"{start_dt} ~ {end_dt}\n\n"
                        f"**超标 Billing 数**\n"
                        f"{len(exceeded_billings)}\n\n"
                        f"{billing_details_all}"
                    )
                    
                    if config.webhook_url:
                        send_webhook_alert(config.webhook_url, message_content, threshold_val, f"{start_dt} to {end_dt}", is_relative=(config.alert_type == "relative"))
                    if config.email:
                        send_email_alert(config.email, message_content, threshold_val, f"{start_dt} to {end_dt}", is_relative=(config.alert_type == "relative"))

            else:
                # ==========================================
                # 项目维度告警判定
                # ==========================================
                project_daily_costs = {}
                project_billing_ids = {} # 统计项目对应的 Billing 账号

                for u in usages:
                    pid = u.project_id
                    date_str = u.usage_date.strftime('%Y-%m-%d')
                    if pid not in project_daily_costs:
                        project_daily_costs[pid] = {}
                    project_daily_costs[pid][date_str] = project_daily_costs[pid].get(date_str, 0.0) + u.cost
                    if u.billing_account_id and isinstance(u.billing_account_id, str):
                        project_billing_ids[pid] = u.billing_account_id

                projects_to_check = config.project_ids if config.project_ids else list(project_daily_costs.keys())
                exceeded_projects = []

                for pid in projects_to_check:
                    daily_costs = project_daily_costs.get(pid, {})
                    exceeding_days = []
                    current_date = start_dt
                    
                    while current_date <= end_dt:
                        date_str = current_date.strftime('%Y-%m-%d')
                        cost = daily_costs.get(date_str, 0.0)
                        
                        if config.alert_type == "relative":
                            comp_days = get_comparison_days(config.comparison_window)
                            history_date = current_date - timedelta(days=comp_days)
                            history_date_str = history_date.strftime('%Y-%m-%d')
                            history_cost = daily_costs.get(history_date_str, 0.0)
                            
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
                            if cost > config.threshold:
                                exceeding_days.append({
                                    "date": date_str,
                                    "cost": cost
                                })
                        current_date += timedelta(days=1)

                    if exceeding_days:
                        # 抑制 3 天内已处理的告警
                        recent_handled = crud.get_recent_handled_incidents(db, pid, days=3)
                        if recent_handled:
                            continue
                            
                        # 24 小时内 pendings 去重
                        import models
                        recent_pending = db.query(models.AlertIncident).filter(
                            models.AlertIncident.project_id == pid,
                            models.AlertIncident.alert_config_id == config.id,
                            models.AlertIncident.status == "pending",
                            models.AlertIncident.created_at >= datetime.utcnow() - timedelta(hours=24)
                        ).first()
                        if recent_pending:
                            continue

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
                        
                        # 写入 Incident
                        incident_data = schemas.AlertIncidentCreate(
                            alert_config_id=config.id,
                            project_id=pid,
                            billing_account_id=project_billing_ids.get(pid),
                            cost=latest_exceeding["cost"],
                            threshold=config.threshold_percentage if config.alert_type == "relative" else config.threshold,
                            usage_date=latest_exceeding["date"]
                        )
                        crud.create_alert_incident(db, incident_data)

                if exceeded_projects:
                    logger.warning(f"ALERT: Project Config '{config.alert_name}' triggered for {len(exceeded_projects)} projects.")
                    service_info = f" (服务: {config.service_description})" if config.service_description else ""
                    threshold_val = config.threshold_percentage if config.alert_type == "relative" else config.threshold
                    
                    project_cards = []
                    for idx, p in enumerate(exceeded_projects):
                        cust_name = project_customer_map.get(p['id'], "未知客户")
                        billing_id = project_billing_ids.get(p['id'], "未知 Billing")
                        b_display = f"{billing_id} ({billing_name_map.get(billing_id, '未知')})" if billing_id != "未知 Billing" else "未知 Billing"
                        
                        if config.alert_type == "relative":
                            ratio_pct = p['change_ratio'] * 100
                            card_item = (
                                f"## 📦 `{p['id']}`\n"
                                f"> 💰 单日费用：<font color=\"warning\">${p['cost']:.2f}</font>\n"
                                f"> 📈 费用涨幅：<font color=\"warning\">{ratio_pct:+.2f}%</font>\n"
                                f"> 📜 历史费用：${p['history_cost']:.2f}\n"
                                f"> 📅 费用日期：{p['date']}\n"
                                f"> 🏢 所属 Billing：`{b_display}`\n"
                                f"> 👤 所属客户：{cust_name}"
                            )
                        else:
                            card_item = (
                                f"## 📦 `{p['id']}`\n"
                                f"> 💰 单日费用：<font color=\"warning\">${p['cost']:.2f}</font>\n"
                                f"> 📅 费用日期：{p['date']}\n"
                                f"> 🏢 所属 Billing：`{b_display}`\n"
                                f"> 👤 所属客户：{cust_name}"
                            )
                        project_cards.append(card_item)

                    project_details_all = "\n\n".join(project_cards)
                    
                    threshold_display = f"{config.threshold_percentage * 100:.1f}%" if config.alert_type == "relative" else f"${config.threshold:.2f}"
                    desc_text = config.service_description if config.service_description else config.alert_name
                    message_content = (
                        f"# 🔴 GCP 费用超标告警\n\n"
                        f"> {desc_text}\n\n"
                        f"**告警阈值**\n"
                        f"🟠 {threshold_display}\n\n"
                        f"**告警日期**\n"
                        f"{start_dt} ~ {end_dt}\n\n"
                        f"**超标项目数**\n"
                        f"{len(exceeded_projects)}\n\n"
                        f"{project_details_all}"
                    )

                    if config.webhook_url:
                        send_webhook_alert(config.webhook_url, message_content, threshold_val, f"{start_dt} to {end_dt}", is_relative=(config.alert_type == "relative"))
                    if config.email:
                        send_email_alert(config.email, message_content, threshold_val, f"{start_dt} to {end_dt}", is_relative=(config.alert_type == "relative"))

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
