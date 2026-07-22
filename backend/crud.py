from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import models, schemas
from datetime import date
from auth import get_password_hash

# --- User Management ---

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100):
    logs = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for log in logs:
        log_dict = log.__dict__.copy()
        log_dict['username'] = log.user.username if log.user else "System"
        result.append(log_dict)
    return result

# --- Alert Config ---

def get_alert_config(db: Session, config_id: int):
    return db.query(models.AlertConfig).filter(models.AlertConfig.id == config_id).first()

def get_alert_configs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AlertConfig).offset(skip).limit(limit).all()

def create_alert_config(db: Session, config: schemas.AlertConfigCreate):
    db_config = models.AlertConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def update_alert_config(db: Session, config_id: int, config: schemas.AlertConfigUpdate):
    db_config = get_alert_config(db, config_id)
    if db_config:
        for key, value in config.model_dump().items():
            setattr(db_config, key, value)
        db.commit()
        db.refresh(db_config)
    return db_config

def delete_alert_config(db: Session, config_id: int):
    # Delete associated alert incidents first to prevent ForeignKeyViolation
    db.query(models.AlertIncident).filter(models.AlertIncident.alert_config_id == config_id).delete()
    db_config = get_alert_config(db, config_id)
    if db_config:
        db.delete(db_config)
        db.commit()
    return db_config

# --- Alert Incidents ---

def get_alert_incidents(db: Session, skip: int = 0, limit: int = 100, status: str = None):
    query = db.query(models.AlertIncident)
    if status:
        query = query.filter(models.AlertIncident.status == status)
    return query.order_by(models.AlertIncident.created_at.desc()).offset(skip).limit(limit).all()

def get_alert_incident(db: Session, incident_id: int):
    return db.query(models.AlertIncident).filter(models.AlertIncident.id == incident_id).first()

def create_alert_incident(db: Session, incident: schemas.AlertIncidentCreate):
    db_incident = models.AlertIncident(**incident.model_dump())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

def handle_alert_incident(db: Session, incident_id: int, handler_id: int, handle_notes: str):
    from datetime import datetime
    db_incident = get_alert_incident(db, incident_id)
    if db_incident:
        db_incident.status = "handled"
        db_incident.handler_id = handler_id
        db_incident.handle_notes = handle_notes
        db_incident.handled_at = datetime.utcnow()
        db.commit()
        db.refresh(db_incident)
    return db_incident

def delete_alert_incidents(db: Session, incident_ids: list[int]):
    deleted_count = db.query(models.AlertIncident).filter(models.AlertIncident.id.in_(incident_ids)).delete(synchronize_session=False)
    db.commit()
    return deleted_count

def get_recent_handled_incidents(db: Session, project_id: str, days: int = 3):
    from datetime import datetime, timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return db.query(models.AlertIncident).filter(
        models.AlertIncident.project_id == project_id,
        models.AlertIncident.status == "handled",
        models.AlertIncident.handled_at >= cutoff_date
    ).all()

def get_billing_accounts(db: Session, skip: int = 0, limit: int = 5000, search: str = None):
    query = db.query(models.BillingAccount)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.BillingAccount.billing_account_id.ilike(search_term)) |
            (models.BillingAccount.display_name.ilike(search_term))
        )
    return query.offset(skip).limit(limit).all()

def get_billing_account(db: Session, billing_account_id: str):
    return db.query(models.BillingAccount).filter(models.BillingAccount.billing_account_id == billing_account_id).first()

def upsert_billing_account(db: Session, account: schemas.BillingAccountCreate):
    stmt = insert(models.BillingAccount).values(**account.model_dump())
    stmt = stmt.on_conflict_do_update(
        index_elements=['billing_account_id'],
        set_={'display_name': stmt.excluded.display_name}
    )
    db.execute(stmt)
    db.commit()
    return get_billing_account(db, account.billing_account_id)

# --- Project Info ---

def get_project_info(db: Session, project_id: str):
    return db.query(models.ProjectInfo).filter(models.ProjectInfo.project_id == project_id).first()

def get_all_project_infos(db: Session):
    return db.query(models.ProjectInfo).all()

# --- Daily Usage ---

def upsert_daily_usage_batch(db: Session, usages: list[schemas.DailyUsageCreate]):
    if not usages:
        return
    
    values = [usage.model_dump() for usage in usages]
    stmt = insert(models.DailyUsage).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=['project_id', 'billing_account_id', 'service_description', 'usage_date'],
        set_={
            'cost': stmt.excluded.cost,
            'currency': stmt.excluded.currency
        }
    )
    db.execute(stmt)
    db.commit()

def get_daily_usage(
    db: Session, 
    start_date: date, 
    end_date: date, 
    project_id: str = None, 
    billing_account_id: str = None, 
    service_description: str = None
):
    query = db.query(models.DailyUsage).filter(
        models.DailyUsage.usage_date >= start_date,
        models.DailyUsage.usage_date <= end_date
    )
    
    if project_id:
        query = query.filter(models.DailyUsage.project_id == project_id)
    if billing_account_id:
        query = query.filter(models.DailyUsage.billing_account_id == billing_account_id)
    if service_description:
        query = query.filter(models.DailyUsage.service_description == service_description)
        
    return query.all()

# --- Sync Logs ---

def create_sync_log(db: Session, sync_log: schemas.SyncLogCreate):
    from datetime import datetime
    db_log = models.SyncLog(
        sync_type=sync_log.sync_type,
        target_start_date=datetime.strptime(sync_log.target_start_date, '%Y-%m-%d').date(),
        target_end_date=datetime.strptime(sync_log.target_end_date, '%Y-%m-%d').date(),
        status="running"
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def update_sync_log(db: Session, log_id: int, status: str, records_synced: int = 0, error_message: str = None):
    from datetime import datetime
    db_log = db.query(models.SyncLog).filter(models.SyncLog.id == log_id).first()
    if db_log:
        db_log.status = status
        db_log.records_synced = records_synced
        db_log.error_message = error_message
        db_log.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_log)
    return db_log

def get_sync_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SyncLog).order_by(models.SyncLog.created_at.desc()).offset(skip).limit(limit).all()
