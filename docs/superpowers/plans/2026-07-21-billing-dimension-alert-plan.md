# GCP Billing 维度告警与 Webhook 富文本增强实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 GCP 账单告警系统中增加 Billing 账号级别的日费用及环比告警监控，并在 Webhook Markdown 通知中为项目级告警补充客户及 Billing 归属信息，为 Billing 级告警展示 Top 3 飙升消耗项目。

**Architecture:** 本方案在 `AlertConfig` 增加维度选择字段 `dimension` 及 `billing_account_ids` 以声明监控的目标；对 `AlertIncident` 的 `project_id` 设为可空并新增 `billing_account_id` 字段以支持记录 Billing 账号的告警。在 `scheduler.py` 中，根据配置的维度（项目或 Billing 账号）分流计算日总消费，并注入客户和账单关联信息，利用富文本 Markdown 进行精美展示与消息排版。

**Tech Stack:** Python 3.9, FastAPI, SQLAlchemy 2.0, PostgreSQL 15, React, Vite, Ant Design (Antd)

## Global Constraints

* 数据库迁移需保留原有数据，采用 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 实现向前兼容。
* `AlertIncident` 针对 `project_id` 改为可空，并针对 Billing 维度告警存储 `billing_account_id`。
* 编写测试需在 `backend` 目录下通过已存在的虚拟环境 `venv/bin/python -m unittest test_alert.py` 执行，在 `BypassSandbox: true` 模式下执行以防 Anaconda 系统库沙箱权限报错。

---

### Task 1: 数据库与 ORM 模型变更

**Files:**
* Modify: `backend/models.py`
* Modify: `backend/migrate_db.py`

**Interfaces:**
* Produces: 新增 `AlertConfig.dimension`, `AlertConfig.billing_account_ids` 字段及 `AlertIncident.billing_account_id` 字段，且 `AlertIncident.project_id` 变为可空。

- [ ] **Step 1: 修改数据库模型**

在 `backend/models.py` 中修改 `AlertConfig` 和 `AlertIncident`：

```python
# 修改 models.py 中的 AlertConfig 类 (约第 29 行)
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
    # --- 新增字段 ---
    dimension = Column(String, nullable=False, default="project") # "project" or "billing"
    billing_account_ids = Column(JSONB, nullable=True) # List of billing account IDs, null means all

# 修改 models.py 中的 AlertIncident 类 (约第 45 行)
class AlertIncident(Base):
    __tablename__ = "alert_incidents"

    id = Column(Integer, primary_key=True, index=True)
    alert_config_id = Column(Integer, ForeignKey("alert_configs.id"), nullable=False)
    project_id = Column(String, index=True, nullable=True) # 改为 nullable=True
    billing_account_id = Column(String, index=True, nullable=True) # 新增字段
    cost = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    usage_date = Column(String, nullable=False)
    status = Column(String, default="pending") # "pending", "handled"
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 2: 修改迁移脚本**

在 `backend/migrate_db.py` 中，在 `migrate` 函数中追加执行新字段迁移 SQL：

```python
# 在 backend/migrate_db.py 的 migrate() 函数中，约第 41 行后追加：
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
```

- [ ] **Step 3: 运行迁移并验证**

在 `BypassSandbox: true` 模式下执行迁移脚本：
运行：`venv/bin/python migrate_db.py`
预期输出：`Database migration completed successfully.` 且不发生报错。

- [ ] **Step 4: 提交代码**

```bash
git add backend/models.py backend/migrate_db.py
git commit -m "migration: add dimension and billing_account_ids fields"
```

---

### Task 2: Pydantic 数据结构 Schema 变更

**Files:**
* Modify: `backend/schemas.py`

**Interfaces:**
* Consumes: Task 1 中变更的数据库模型。
* Produces: 新的 Pydantic 数据验证结构，包括 `AlertConfig` 与 `AlertIncident` 的各操作对象。

- [ ] **Step 1: 修改 schemas.py**

在 `backend/schemas.py` 中更新 `AlertConfigBase` 与 `AlertIncidentBase` 及相关类：

```python
# 修改 backend/schemas.py 中的 AlertConfigBase (约第 45 行)
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

# 修改 backend/schemas.py 中的 AlertIncidentBase 和 AlertIncident (约第 74 行)
class AlertIncidentBase(BaseModel):
    alert_config_id: int
    project_id: Optional[str] = None # 改为 Optional
    billing_account_id: Optional[str] = None # 新增
    cost: float
    threshold: float
    usage_date: str
    status: str = "pending"
```

- [ ] **Step 2: 验证语法无报错**

运行：`venv/bin/python -c "import schemas; print('Schemas imported successfully')"`
预期输出：`Schemas imported successfully`

- [ ] **Step 3: 提交代码**

```bash
git add backend/schemas.py
git commit -m "feat: update schemas for billing dimension alert"
```

---

### Task 3: 路由与 API 参数校验变更

**Files:**
* Modify: `backend/main.py`

**Interfaces:**
* Consumes: Task 2 的 schema。
* Produces: `/api/alerts` 接口对 dimension 和字段关联的检验。

- [ ] **Step 1: 修改 validate_alert_config 校验逻辑**

在 `backend/main.py` 的 `validate_alert_config` 函数中增加维度校验（约第 309 行）：

```python
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
```

- [ ] **Step 2: 验证 API 运行正常**

运行现有测试确保没有破坏现有功能：
运行：`venv/bin/python -m unittest test_alert.py`
预期结果：OK

- [ ] **Step 3: 提交代码**

```bash
git add backend/main.py
git commit -m "feat: add dimension parameter validation in API"
```

---

### Task 4: 调度检测引擎实现与 Webhook 富文本富化

**Files:**
* Modify: `backend/scheduler.py`

**Interfaces:**
* Consumes: `DailyUsage`，`ProjectInfo`，`BillingAccount` 数据记录。
* Produces: 触发告警事件记录并在 Webhook 发送格式化的高阶富文本 Markdown 报警。

- [ ] **Step 1: 重构 check_billing_and_alert 检测器流程**

在 `backend/scheduler.py` 中重写 `check_billing_and_alert()`。需支持 `config.dimension == "billing"` 的分流费用累加与超额校验，以及对项目级和账单级告警中关联信息的补全展示。

```python
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

                    billing_details_list = []
                    for b in exceeded_billings:
                        bname = billing_name_map.get(b['id'], "未知账号")
                        if config.alert_type == "relative":
                            ratio_pct = b['change_ratio'] * 100
                            detail_header = (
                                f"> 🚨 **超标 Billing 账号**: `{b['id']} ({bname})`\n"
                                f"> - **当前总费用**: <font color=\"warning\">${b['cost']:.2f}</font> (日期: {b['date']})\n"
                                f"> - **历史同期费用**: ${b['history_cost']:.2f} (日期: {b['history_date']})\n"
                                f"> - **整体涨幅**: <font color=\"warning\">{ratio_pct:+.2f}%</font>"
                            )
                        else:
                            detail_header = (
                                f"> 🚨 **超标 Billing 账号**: `{b['id']} ({bname})`\n"
                                f"> - **当前单日费用**: <font color=\"warning\">${b['cost']:.2f}</font> (日期: {b['date']})"
                            )
                        
                        top_projs_str_list = []
                        for idx, p in enumerate(b['top_projects']):
                            top_projs_str_list.append(f"> {idx+1}. `{p['project_id']}` : **${p['cost']:.2f}** (占比 {p['percentage']:.1f}%)")
                        top_projs_block = "\n".join(top_projs_str_list) if top_projs_str_list else "> *(暂无项目明细数据)*"
                        
                        billing_details_list.append(f"{detail_header}\n>\n> 🔥 **该 Billing 下当日消费前 3 的 Top 项目**:\n{top_projs_block}")
                    
                    billing_details_all = "\n\n---\n\n".join(billing_details_list)
                    
                    threshold_display = f"{config.threshold_percentage * 100:.1f}%" if config.alert_type == "relative" else f"${config.threshold:.2f}"
                    message_content = (
                        f"> 告警名称: {config.alert_name}{service_info}\n"
                        f"> 检查范围: 过去 {days_to_check} 天\n\n"
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
                    if u.billing_account_id:
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
                        billing_id = project_billing_ids.get(p['id'], "未知Billing")
                        b_display = f"{billing_id} ({billing_name_map.get(billing_id, '未知')})" if billing_id != "未知Billing" else "未知Billing"
                        
                        if config.alert_type == "relative":
                            ratio_pct = p['change_ratio'] * 100
                            card_item = (
                                f"> 📦 **项目 [{idx+1}/{len(exceeded_projects)}]**: `{p['id']}`\n"
                                f"> - **所属客户**: `{cust_name}`\n"
                                f"> - **所属 Billing**: `{b_display}`\n"
                                f"> - **当前费用**: <font color=\"warning\">${p['cost']:.2f}</font> (日期: {p['date']})\n"
                                f"> - **历史费用**: ${p['history_cost']:.2f} (日期: {p['history_date']})\n"
                                f"> - **费用涨幅**: <font color=\"warning\">{ratio_pct:+.2f}%</font>"
                            )
                        else:
                            card_item = (
                                f"> 📦 **项目 [{idx+1}/{len(exceeded_projects)}]**: `{p['id']}`\n"
                                f"> - **所属客户**: `{cust_name}`\n"
                                f"> - **所属 Billing**: `{b_display}`\n"
                                f"> - **单日费用**: <font color=\"warning\">${p['cost']:.2f}</font> (日期: {p['date']})"
                            )
                        project_cards.append(card_item)

                    project_details_all = "\n>\n> ---\n>\n".join(project_cards)
                    message_content = (
                        f"> 告警名称: {config.alert_name}{service_info}\n"
                        f"> 检查范围: 过去 {days_to_check} 天\n\n"
                        f"> 🚨 **以下项目超出阈值（共 {len(exceeded_projects)} 个）**:\n>\n"
                        f"{project_details_all}"
                    )

                    if config.webhook_url:
                        send_webhook_alert(config.webhook_url, message_content, threshold_val, f"{start_dt} to {end_dt}", is_relative=(config.alert_type == "relative"))
                    if config.email:
                        send_email_alert(config.email, message_content, threshold_val, f"{start_dt} to {end_dt}", is_relative=(config.alert_type == "relative"))

    finally:
        db.close()
```

- [ ] **Step 2: 验证语法无报错**

运行现有的 11 个单元测试，确保代码重构完全向后兼容并且原有的用例仍然正常通过：
运行：`venv/bin/python -m unittest test_alert.py`
预期输出：OK

- [ ] **Step 3: 提交代码**

```bash
git add backend/scheduler.py
git commit -m "feat: complete billing-dimension check engine and rich formatted webhook notifications"
```

---

### Task 5: 前端管理展示页面迭代

**Files:**
* Modify: `frontend/src/pages/AlertSettings.jsx`
* Modify: `frontend/src/pages/AlertIncidents.jsx`

**Interfaces:**
* Consumes: 新增的 `dimension` 与 `billing_account_ids` API 字段。
* Produces: 支持配置 Billing 告警的控制表单及展示历史记录。

- [ ] **Step 1: 迭代修改 AlertSettings.jsx 配置项弹框**

在 `frontend/src/pages/AlertSettings.jsx` 中增加维度 `dimension` 选择，当维度为 `billing` 时显示 Billing 账号下拉框，并联动：

```javascript
// 1. 在 AlertSettings.jsx 引入 useEffect 获取所有的 billing accounts
const [billingAccounts, setBillingAccounts] = useState([]);
useEffect(() => {
  fetchBillingAccounts();
}, []);
const fetchBillingAccounts = async () => {
  try {
    const response = await api.get('/billing-accounts');
    setBillingAccounts(response.data);
  } catch (err) {
    console.error("Failed to load billing accounts", err);
  }
};

// 2. 修改 handleAdd 重置默认值 (约第 38 行)
form.setFieldsValue({ 
  is_active: true, 
  threshold: 100, 
  project_ids: [], 
  billing_account_ids: [],
  dimension: 'project',
  time_range_days: 1, 
  service_description: '',
  alert_type: 'absolute',
  comparison_window: 'week',
  threshold_percentage: 50
});

// 3. 修改 handleEdit 数据回显绑定 (约第 51 行)
form.setFieldsValue({
  ...record,
  project_ids: record.project_ids || [],
  billing_account_ids: record.billing_account_ids || [],
  threshold_percentage: record.threshold_percentage ? record.threshold_percentage * 100 : 50,
  comparison_window: compWindow,
  custom_comparison_days: customDays
});

// 4. 修改 handleModalOk 提单组装逻辑 (约第 79 行)
const payload = {
  ...values,
  project_ids: values.dimension === 'project' && values.project_ids && values.project_ids.length > 0 ? values.project_ids : null,
  billing_account_ids: values.dimension === 'billing' && values.billing_account_ids && values.billing_account_ids.length > 0 ? values.billing_account_ids : null,
  threshold_percentage: values.alert_type === 'relative' && values.threshold_percentage ? values.threshold_percentage / 100 : null,
  comparison_window: values.alert_type === 'relative' ? compWindow : null,
  threshold: values.alert_type === 'absolute' ? values.threshold : 0
};

// 5. 修改 Columns 配置展示 Target Projects 变更为展示 Target Entities (约第 168 行)
{
  title: 'Targets',
  key: 'targets',
  render: (_, record) => {
    if (record.dimension === 'billing') {
      const baccs = record.billing_account_ids;
      if (!baccs || baccs.length === 0) return <Tag color="orange">All Billing Accounts</Tag>;
      return <Space wrap>{baccs.map(b => <Tag color="orange" key={b}>{b}</Tag>)}</Space>;
    }
    const projectIds = record.project_ids;
    if (!projectIds || projectIds.length === 0) return <Tag color="blue">All Projects</Tag>;
    return <Space wrap>{projectIds.map(pid => <Tag key={pid}>{pid}</Tag>)}</Space>;
  }
},

// 6. 在 Form 弹窗组件中新增 Dimension 选择框与级联组件 (约第 310 行)
<Form.Item
  name="dimension"
  label="Alert Dimension (监控维度)"
  rules={[{ required: true, message: 'Please select dimension' }]}
>
  <Select onChange={() => form.setFieldsValue({ project_ids: [], billing_account_ids: [] })}>
    <Option value="project">Project Level (项目级)</Option>
    <Option value="billing">Billing Account Level (Billing级)</Option>
  </Select>
</Form.Item>

<Form.Item
  noStyle
  shouldUpdate={(prevValues, currentValues) => prevValues.dimension !== currentValues.dimension}
>
  {({ getFieldValue }) => 
    getFieldValue('dimension') === 'billing' ? (
      <Form.Item
        name="billing_account_ids"
        label="Target Billing Accounts (Leave empty for All)"
      >
        <Select
          mode="multiple"
          style={{ width: '100%' }}
          placeholder="Select Billing Accounts to monitor"
          optionFilterProp="children"
        >
          {billingAccounts.map(b => (
            <Option key={b.billing_account_id} value={b.billing_account_id}>
              {b.display_name} ({b.billing_account_id})
            </Option>
          ))}
        </Select>
      </Form.Item>
    ) : (
      <Form.Item
        name="project_ids"
        label="Target Projects (Leave empty for All Projects)"
      >
        <Select
          mode="tags"
          style={{ width: '100%' }}
          placeholder="Type project IDs and press enter"
          tokenSeparators={[',']}
        />
      </Form.Item>
    )
  }
</Form.Item>
```

- [ ] **Step 2: 迭代修改 AlertIncidents.jsx 告警历史记录**

在 `frontend/src/pages/AlertIncidents.jsx` 中，对 Table 列中 `Project ID` 字段增加当为 Billing 维度告警时的展示渲染：

```javascript
// 修改 AlertIncidents.jsx Columns 的 Project ID 列展示 (约第 94 行)
{
  title: 'Target Entity',
  key: 'target_entity',
  render: (_, record) => {
    if (record.project_id) {
      return <Text strong>{record.project_id}</Text>;
    } else if (record.billing_account_id) {
      return <Tag color="orange">Billing: {record.billing_account_id}</Tag>;
    }
    return <Text type="secondary">-</Text>;
  }
},

// 修改 Handle Modal 弹框内的说明文字 (约第 209 行)
<div style={{ marginBottom: 16, padding: 12, backgroundColor: '#fffbe6', border: '1px solid #ffe58f', borderRadius: 4 }}>
  {handlingIncident?.project_id ? (
    <>
      <Text strong>Project: </Text> <Text>{handlingIncident?.project_id}</Text><br/>
    </>
  ) : (
    <>
      <Text strong>Billing Account: </Text> <Text>{handlingIncident?.billing_account_id}</Text><br/>
    </>
  )}
  <Text strong>Cost: </Text> <Text type="danger">${handlingIncident?.cost}</Text><br/>
  <Text type="secondary" style={{ fontSize: 12 }}>
    * Marking this as handled will suppress new alerts for this entity for the next 3 days.
  </Text>
</div>
```

- [ ] **Step 3: 提交代码**

```bash
git add frontend/src/pages/AlertSettings.jsx frontend/src/pages/AlertIncidents.jsx
git commit -m "feat: frontend support for billing dimension alerts configuration and incident logs"
```

---

### Task 6: 单元测试用例扩充与全量测试验证

**Files:**
* Modify: `backend/test_alert.py`

**Interfaces:**
* Consumes: 完整的重构后的告警系统与测试 API。
* Produces: 新增的测试通过断言结果。

- [ ] **Step 1: 新增单元测试用例**

在 `backend/test_alert.py` 中重构并追加三个独立的测试用例：
1. `test_relative_alert_with_billing_dimension`：测试 Billing 维度日费加总及环比超标判定。
2. `test_absolute_alert_with_billing_dimension`：测试 Billing 维度绝对值计算和 Top 3 项目捕获。
3. `test_validate_alert_config_dimension`：校验 dimension 接口错误检测。

```python
# 追加到 backend/test_alert.py
    def test_validate_alert_config_dimension(self):
        # 错误的维度应该抛异常
        config = schemas.AlertConfigCreate(
            alert_name="Test Error Dimension",
            threshold=100.0,
            alert_type="absolute",
            dimension="unknown_dimension"
        )
        with self.assertRaises(HTTPException) as context:
            validate_alert_config(config)
        self.assertEqual(context.exception.status_code, 400)

    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_absolute_alert_with_billing_dimension(self, mock_send_webhook, mock_crud, mock_session_local):
        # 设定 Mock
        mock_db = MagicMock()
        mock_session_local.return_return_value = mock_db
        
        # 配置 Billing 维度的绝对额告警
        config = models.AlertConfig(
            id=2,
            alert_name="Billing Absolute Alert",
            dimension="billing",
            billing_account_ids=["billing-1"],
            threshold=1000.0,
            alert_type="absolute",
            time_range_days=1,
            webhook_url="http://mock-webhook"
        )
        mock_crud.get_alert_configs.return_value = [config]
        mock_crud.get_billing_accounts.return_value = [
            models.BillingAccount(billing_account_id="billing-1", display_name="Main Billing")
        ]
        mock_crud.get_all_project_infos.return_value = []
        
        # 组装 usages (单日花费加总 1200，超过阈值 1000)
        # 且包含 4 个项目，用于提取前 3 消费项目
        usage_date = (datetime.utcnow() - timedelta(days=1)).date()
        usages = [
            models.DailyUsage(project_id="proj-a", billing_account_id="billing-1", cost=500.0, usage_date=usage_date, currency="USD"),
            models.DailyUsage(project_id="proj-b", billing_account_id="billing-1", cost=400.0, usage_date=usage_date, currency="USD"),
            models.DailyUsage(project_id="proj-c", billing_account_id="billing-1", cost=200.0, usage_date=usage_date, currency="USD"),
            models.DailyUsage(project_id="proj-d", billing_account_id="billing-1", cost=100.0, usage_date=usage_date, currency="USD")
        ]
        mock_crud.get_daily_usage.return_value = usages
        
        # 运行检测
        check_billing_and_alert()
        
        # 检查是否成功触发 Webhook 报警，且参数格式化包含 Top 项目
        mock_send_webhook.assert_called_once()
        args = mock_send_webhook.call_args[0]
        self.assertEqual(args[0], "http://mock-webhook") # URL
        self.assertIn("Main Billing", args[1]) # 账单名称
        self.assertIn("proj-a", args[1]) # Top 1
        self.assertIn("proj-b", args[1]) # Top 2
        self.assertIn("proj-c", args[1]) # Top 3
        self.assertNotIn("proj-d", args[1]) # 确保 Top 4 被截断未显示
```

- [ ] **Step 2: 全量运行测试**

在 `BypassSandbox: true` 模式下执行测试：
运行：`venv/bin/python -m unittest test_alert.py`
预期输出：`Ran 13 tests ... OK` 且没有任何错误！

- [ ] **Step 3: 提交代码**

```bash
git add backend/test_alert.py
git commit -m "test: add unit tests for billing-dimension alert validation and checking logic"
```
