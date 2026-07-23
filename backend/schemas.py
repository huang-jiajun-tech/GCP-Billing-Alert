from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "user"
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class AuditLog(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    details: Optional[str]
    created_at: datetime
    username: Optional[str] = None # For display

    class Config:
        from_attributes = True

class AlertConfigBase(BaseModel):
    alert_name: str
    project_ids: Optional[List[str]] = None
    service_description: Optional[str] = None
    time_range_days: int = 1
    threshold: float = 0.0
    email: Optional[str] = None
    webhook_url: Optional[str] = None
    is_active: bool = True
    alert_type: str = "absolute" # "absolute" or "relative"
    comparison_window: Optional[str] = None # "week" or "month"
    threshold_percentage: Optional[float] = None # e.g., 0.5 for 50%
    dimension: str = "project" # "project" or "billing"
    billing_account_ids: Optional[List[str]] = None

class AlertConfigCreate(AlertConfigBase):
    pass

class AlertConfigUpdate(AlertConfigBase):
    pass

class AlertConfig(AlertConfigBase):
    id: int

    class Config:
        from_attributes = True

class AlertTestRequest(BaseModel):
    webhook_url: Optional[str] = None
    email: Optional[str] = None

class AlertIncidentBase(BaseModel):
    alert_config_id: int
    project_id: Optional[str] = None # 改为 Optional
    billing_account_id: Optional[str] = None # 新增
    cost: float
    threshold: float
    usage_date: str
    status: str = "pending"

class AlertIncidentCreate(AlertIncidentBase):
    pass

class AlertIncidentHandle(BaseModel):
    handle_notes: str

class AlertIncidentBatchDelete(BaseModel):
    incident_ids: List[int]

class AlertIncident(AlertIncidentBase):
    id: int
    created_at: datetime
    handled_at: Optional[datetime] = None
    handler_id: Optional[int] = None
    handle_notes: Optional[str] = None
    
    config: Optional[AlertConfig] = None
    handler: Optional[User] = None

    class Config:
        from_attributes = True

class BillingAccountBase(BaseModel):
    billing_account_id: str
    display_name: str

class BillingAccountCreate(BillingAccountBase):
    pass

class BillingAccount(BillingAccountBase):
    id: int
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectInfoBase(BaseModel):
    project_id: str
    customer_name: Optional[str] = None
    sales_rep: Optional[str] = None

class ProjectInfo(ProjectInfoBase):
    class Config:
        from_attributes = True

class DailyUsageBase(BaseModel):
    project_id: str
    billing_account_id: Optional[str] = None
    service_description: Optional[str] = None
    usage_date: datetime
    cost: float
    currency: str = "USD"

class DailyUsageCreate(DailyUsageBase):
    pass

class DailyUsage(DailyUsageBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True

class SyncLogBase(BaseModel):
    sync_type: str
    target_start_date: date
    target_end_date: date

class SyncLogCreate(BaseModel):
    sync_type: str
    target_start_date: str
    target_end_date: str

class SyncLog(SyncLogBase):
    id: int
    status: str
    records_synced: Optional[int] = 0
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SyncRequest(BaseModel):
    start_date: str
    end_date: str
