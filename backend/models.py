from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user") # "admin" or "user"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    details = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True, index=True)
    alert_name = Column(String, nullable=False, default="Default Alert")
    project_ids = Column(JSONB, nullable=True) # List of project IDs, null means all projects
    service_description = Column(String, nullable=True) # Filter by specific service
    time_range_days = Column(Integer, default=1) # Time range to check daily costs
    threshold = Column(Float, nullable=False)
    email = Column(String, nullable=True)
    webhook_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    alert_type = Column(String, nullable=False, default="absolute") # "absolute" or "relative"
    comparison_window = Column(String, nullable=True) # "week" or "month"
    threshold_percentage = Column(Float, nullable=True) # e.g., 0.5 for 50%

class AlertIncident(Base):
    __tablename__ = "alert_incidents"

    id = Column(Integer, primary_key=True, index=True)
    alert_config_id = Column(Integer, ForeignKey("alert_configs.id"), nullable=False)
    project_id = Column(String, index=True, nullable=False)
    cost = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    usage_date = Column(String, nullable=False)
    status = Column(String, default="pending") # "pending", "handled"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Handling details
    handled_at = Column(DateTime, nullable=True)
    handler_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    handle_notes = Column(String, nullable=True)

    config = relationship("AlertConfig")
    handler = relationship("User")

class BillingAccount(Base):
    __tablename__ = "billing_accounts"

    id = Column(Integer, primary_key=True, index=True)
    billing_account_id = Column(String, index=True, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProjectInfo(Base):
    __tablename__ = "project_info"

    project_id = Column(String, primary_key=True, index=True)
    customer_name = Column(String, nullable=True)
    sales_rep = Column(String, nullable=True)

class DailyUsage(Base):
    __tablename__ = "daily_usage"

    # For partitioned tables, the partition key must be part of the primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(String, index=True, nullable=False)
    billing_account_id = Column(String, index=True, nullable=True)
    service_description = Column(String, index=True, nullable=True)
    usage_date = Column(Date, primary_key=True, index=True, nullable=False)
    cost = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('project_id', 'billing_account_id', 'service_description', 'usage_date', name='uix_daily_usage'),
        {'postgresql_partition_by': 'RANGE (usage_date)'}
    )

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String, nullable=False) # "auto" or "manual"
    target_start_date = Column(Date, nullable=False)
    target_end_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="running") # "running", "success", "failed"
    records_synced = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
