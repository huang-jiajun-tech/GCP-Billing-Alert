# GCP 账单 Billing 维度告警及 Webhook 通知富文本增强设计文档

## 1. 背景与目标

当前系统仅支持**项目（Project）维度**的告警。用户无法配置针对整个 Billing 账号（包含多个项目）的日费用告警，也无法在通知中直观地看到触发告警的项目所属的客户信息及 Billing 归属。

本设计的目标是：
1. 在告警配置中引入监控维度，支持 **Billing 账号维度** 的告警检测（日费用绝对值、同比环比等）。
2. 在项目级告警的 Webhook 通知中，自动关联并加入项目所属的 **Billing 账户信息** 与 **客户信息**。
3. 针对多个项目同时触发告警的情况，以及 Billing 维度告警中展示 Top 3 消耗项目的需求，进行 Webhook Markdown 通知的富文本排版设计。
4. 保证后端告警检测逻辑、数据库记录与前端展示页面的端到端打通。

---

## 2. 方案架构设计

本方案采用**通用内聚扩展模型**设计，复用现有的 `AlertConfig` 与 `AlertIncident` 结构，通过新增维度字段和关联查询来实现：

```mermaid
graph TD
    subgraph 数据库层
        DU[(daily_usage)]
        AC[(alert_configs)]
        AI[(alert_incidents)]
        BA[(billing_accounts)]
        PI[(project_info)]
    end

    subgraph 调度器检测层 (scheduler.py)
        CS[check_billing_and_alert]
        AP[按项目级统计检测]
        AB[按Billing账号统计检测]
    end

    subgraph 通知推送层
        WH[企业微信 Webhook]
    end

    CS -->|dimension = 'project'| AP
    CS -->|dimension = 'billing'| AB
    AP -->|查询费用| DU
    AB -->|查询费用| DU
    AP -->|补全客户与Billing名| PI
    AP -->|补全客户与Billing名| BA
    AB -->|获取Top 3消耗项目| DU
    AP -->|记录事件| AI
    AB -->|记录事件| AI
    AI -->|富文本推送| WH
```

---

## 3. 详细设计

### 3.1 数据库结构设计

#### (1) `alert_configs` 表变更
* 新增 `dimension` 字段，区分监控维度（`project` 或 `billing`）。
* 新增 `billing_account_ids` 字段，用于指定监控特定的 Billing 账号。

```sql
ALTER TABLE alert_configs ADD COLUMN IF NOT EXISTS dimension VARCHAR NOT NULL DEFAULT 'project';
ALTER TABLE alert_configs ADD COLUMN IF NOT EXISTS billing_account_ids JSONB;
```

#### (2) `alert_incidents` 表变更
* 将 `project_id` 设为可空（Nullable）。
* 新增 `billing_account_id` 字段，用于记录触发的 Billing 级告警。

```sql
ALTER TABLE alert_incidents ADD COLUMN IF NOT EXISTS billing_account_id VARCHAR;
ALTER TABLE alert_incidents ALTER COLUMN project_id DROP NOT NULL;
```

---

### 3.2 后端模型与校验设计

#### (1) SQLAlchemy Models (`models.py`)
```python
class AlertConfig(Base):
    __tablename__ = "alert_configs"
    # ... 现有字段 ...
    dimension = Column(String, nullable=False, default="project")  # "project" 或 "billing"
    billing_account_ids = Column(JSONB, nullable=True)  # List of billing account IDs

class AlertIncident(Base):
    __tablename__ = "alert_incidents"
    # ... 现有字段 ...
    project_id = Column(String, index=True, nullable=True)  # 改为可空
    billing_account_id = Column(String, index=True, nullable=True)  # 新增
```

#### (2) Pydantic Schemas (`schemas.py`)
* 在 `AlertConfigBase` 中新增 `dimension: str = "project"` 与 `billing_account_ids: Optional[List[str]] = None`。
* 在 `AlertIncidentBase` 中将 `project_id` 改为 `Optional[str]`，并新增 `billing_account_id: Optional[str] = None`。

#### (3) API 校验 (`main.py` -> `validate_alert_config`)
```python
def validate_alert_config(config):
    if config.dimension not in ["project", "billing"]:
        raise HTTPException(status_code=400, detail="dimension must be either 'project' or 'billing'")
    # ... 现有校验 ...
```

---

### 3.3 告警检测调度逻辑变更 (`scheduler.py`)

在后台任务 `check_billing_and_alert()` 中，进行如下优化重构：

```python
def check_billing_and_alert():
    db = SessionLocal()
    try:
        configs = crud.get_alert_configs(db)
        active_configs = [c for c in configs if c.is_active]
        if not active_configs:
            return

        # 1. 预先拉取基础关联数据以供富文本补全
        billing_accounts = crud.get_billing_accounts(db, limit=5000)
        billing_name_map = {acc.billing_account_id: acc.display_name for acc in billing_accounts}
        
        project_infos = crud.get_all_project_infos(db)
        project_customer_map = {pi.project_id: pi.customer_name for pi in project_infos}

        for config in active_configs:
            # 计算检测的时间窗口 (start_dt, end_dt)
            # ... 时间窗口计算保持一致 ...

            if config.dimension == "billing":
                # ========================================================
                # 【Billing 维度检测逻辑】
                # ========================================================
                usages = crud.get_daily_usage(db, query_start_dt, end_dt, service_description=config.service_description)
                
                # 聚合：{ billing_account_id: { date_str: daily_cost } }
                billing_daily_costs = {}
                # 用于统计 Top 3 项目费用的临时存储：{ billing_account_id: { date_str: { project_id: cost } } }
                billing_project_costs = {}

                for u in usages:
                    bid = u.billing_account_id
                    if not bid:
                        continue
                    date_str = u.usage_date.strftime('%Y-%m-%d')
                    
                    if bid not in billing_daily_costs:
                        billing_daily_costs[bid] = {}
                    billing_daily_costs[bid][date_str] = billing_daily_costs[bid].get(date_str, 0.0) + u.cost

                    # 记录该 Billing 下各个项目的每日账单
                    if bid not in billing_project_costs:
                        billing_project_costs[bid] = {}
                    if date_str not in billing_project_costs[bid]:
                        billing_project_costs[bid][date_str] = {}
                    billing_project_costs[bid][date_str][u.project_id] = billing_project_costs[bid][date_str].get(u.project_id, 0.0) + u.cost

                # 决定检查哪些 Billing 账号
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
                        # 24小时内未处理 pending 告警去重
                        # ... 去重逻辑与之前一致，使用 billing_account_id 进行过滤 ...

                        # 取出最新超标的一天，提取 Top 3 消费项目
                        exceeding_days.sort(key=lambda x: x['date'], reverse=True)
                        latest_exceeding = exceeding_days[0]
                        latest_date_str = latest_exceeding["date"]

                        # 获取当天该 Billing 账号下的项目排行
                        project_costs_on_day = billing_project_costs.get(bid, {}).get(latest_date_str, {})
                        sorted_projects = sorted(project_costs_on_day.items(), key=lambda x: x[1], reverse=True)
                        top_projects = []
                        for pid, pcost in sorted_projects[:3]:
                            top_projects.append({
                                "project_id": pid,
                                "cost": pcost,
                                "percentage": (pcost / latest_exceeding["cost"] * 100) if latest_exceeding["cost"] > 0 else 0
                            })

                        exceeded_info = {
                            "id": bid,
                            "cost": latest_exceeding["cost"],
                            "date": latest_date_str,
                            "top_projects": top_projects
                        }
                        if config.alert_type == "relative":
                            exceeded_info.update({
                                "history_date": latest_exceeding["history_date"],
                                "history_cost": latest_exceeding["history_cost"],
                                "change_ratio": latest_exceeding["change_ratio"]
                            })
                        exceeded_billings.append(exceeded_info)

                        # 记录 AlertIncident
                        incident_data = schemas.AlertIncidentCreate(
                            alert_config_id=config.id,
                            project_id=None,
                            billing_account_id=bid,
                            cost=latest_exceeding["cost"],
                            threshold=config.threshold_percentage if config.alert_type == "relative" else config.threshold,
                            usage_date=latest_date_str
                        )
                        crud.create_alert_incident(db, incident_data)

                # 发送 Webhook & 邮件通知
                if exceeded_billings:
                    # 按照富文本模板组装并发送 Billing 维度告警通知
                    # ...

            else:
                # ========================================================
                # 【项目维度检测逻辑 - 复用并增强富文本】
                # ========================================================
                # 查询并按项目过滤检测
                # ...
                # 在组装项目超标的 details 时，自动注入关联的 Billing 名与客户名：
                for p in exceeded_projects:
                    cust_name = project_customer_map.get(p['id'], "未知客户")
                    # 通过 usages 数据寻找项目所使用的 billing_account_id
                    billing_id = "未知Billing"
                    for u in usages:
                        if u.project_id == p['id']:
                            billing_id = u.billing_account_id
                            break
                    billing_display = f"{billing_id} ({billing_name_map.get(billing_id, '未知')})" if billing_id else "未知Billing"
                    # 拼装 Markdown details
                    # ...
```

---

### 3.4 Webhook 富文本通知设计

#### (1) 项目级告警 Markdown 消息组装
支持展示多个项目。当有多个项目同时触发时，以水平分隔线 `---` 划分为多个“项目卡片块”，增强易读性：

```markdown
## <font color="warning">⚠️ GCP 费用超额告警 (项目级)</font>
**告警日期**：<font color="comment">2026-07-20</font>
**设定的告警阈值**：<font color="info">{threshold_display}</font>

**告警详情**：
> 告警名称: {config.alert_name}
> 检查范围: 过去 {days_to_check} 天
> 
> 🚨 **以下项目超出阈值（共 {count} 个）**:
> 
> ---
> 📦 **项目 [1/2]**: `analytics-prod`
> - **所属客户**: `百度 (Baidu)`
> - **所属 Billing**: `01A2B3-C4D5E6-F7G8H9 (百度专用托管账号)`
> - **当前费用**: <font color="warning">$150.25</font> (历史费用: $80.00, 涨幅: +87.81%)
```

#### (2) Billing 级告警 Markdown 消息组装
显示触发告警的 Billing 账号，并以列表形式精细化输出该 Billing 账号当天消耗排名前 3 的 Top 项目：

```markdown
## <font color="warning">⚠️ GCP 费用超额告警 (Billing级)</font>
**告警日期**：<font color="comment">2026-07-20</font>
**设定的告警阈值**：<font color="info">{threshold_display}</font>

**告警详情**：
> 告警名称: {config.alert_name}
> 
> 🚨 **超标 Billing 账号**: `012345-6789AB-CDEF01 (百道主账号)`
> - **当前总费用**: <font color="warning">$5000.00</font> (历史同期: $3000.00, 涨幅: +66.67%)
> 
> 🔥 **该 Billing 下当日消费前 3 的 Top 项目**:
> 1. `bigdata-warehouse` : **$3200.00** (占比 64.0%)
> 2. `ai-training-vertex` : **$1100.00** (占比 22.0%)
> 3. `web-backend-prod` : **$500.00** (占比 10.0%)
```

---

### 3.5 前端配置与展示设计

#### (1) 告警配置编辑弹窗 (`AlertSettings.jsx`)
* 新增维度选择：`dimension` (Dropdown Select)。
* 当选择 `Project Level` 时，展示原有的标签选择器 `Target Projects`。
* 当选择 `Billing Account Level` 时，展示新增的 `Target Billing Accounts` 多选下拉框。下拉框数据通过查询后端 `/api/billing-accounts` 的结果进行渲染。

#### (2) 告警事件页 (`AlertIncidents.jsx`)
* 优化 Table 中 `Project ID` 列的渲染。若记录为 Billing 维度（即 `project_id` 为 None，而 `billing_account_id` 存在），则展示为 `Billing: {billing_account_id}` 的橙色标签。

---

## 4. 验证计划

### 4.1 自动化测试 (Automated Tests)
在 `backend/test_alert.py` 中，编写对全新告警逻辑的单元测试用例：
1. **测试项目维度多项目同时触发 Webhook 发送格式。**
2. **测试 Billing 维度日费用计算、超标检测及 Top 3 提取逻辑。**
3. **测试带 dimension 与 billing_account_ids 时的告警配置 API 校验。**

通过命令运行验证：
```bash
venv/bin/python -m unittest test_alert.py
```

### 4.2 手动功能测试 (Manual Verification)
1. 启动后端 API，运行迁移脚本补全数据库新字段。
2. 通过 Swagger UI (`/docs`) 或前端配置页面，分别创建：
   * 一个项目级相对告警配置（故意调低阈值以触发多个项目）。
   * 一个Billing级绝对费用告警配置。
3. 触发检测任务，拦截并审查发送到企业微信 Webhook 机器人的富文本格式，确保显示排版精美。
