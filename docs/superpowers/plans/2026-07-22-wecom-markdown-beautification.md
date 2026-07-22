# 企业微信 Markdown 告警样式美化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构企业微信 Webhook 发送的 Markdown 告警消息排版样式，升级为高档、美观、信息层级分明的「方案 A + 红灰极简配色（组合 2）」，并在不破坏现有单元测试的前提下完成重构。

**Architecture:** 
- 重构 [scheduler.py](file:///Users/huangjiajun/Project/Billing_Alert/backend/scheduler.py) 中 `send_webhook_alert` 方法的外层卡片格式化逻辑，实现对高级格式、测试通知和回退通知的自适应包装。
- 重构 Billing 维度和 Project 维度的异常消息体生成拼接逻辑，去除陈旧的多层 `>` 嵌套排版，采用 `---` 分割、`*` 列表点、加粗和 `warning`/`comment` 色彩标签。

**Tech Stack:** Python 3.9, FastAPI, Requests

## Global Constraints
- **代码完整性**：必须完整保留与本需求无关的现有注释和文档字符串。
- **单元测试兼容性**：必须保证现有的 17 项单元测试在修改后依然全部通过，不得修改已有测试的核心判定条件。
- **极简红灰配色**：非异常/基准数据用 `comment`（灰色），核心超标数据/标识用 `warning`（橙红）。

---

### Task 1: 辅助函数 send_webhook_alert 改造

**Files:**
- Modify: `backend/scheduler.py:108-139`
- Test: `backend/test_alert.py`

**Interfaces:**
- Consumes: `message_content: str`, `threshold: float`, `date: str`, `is_relative: bool`
- Produces: `send_webhook_alert`

- [ ] **Step 1: 编写/检视现有 tests 确保能够覆盖测试通知与通用通知**

确认 `backend/test_alert.py` 能成功调用该函数。

- [ ] **Step 2: 改造 send_webhook_alert 的排版生成规则**

在 [scheduler.py](file:///Users/huangjiajun/Project/Billing_Alert/backend/scheduler.py) 中，将 `send_webhook_alert` 的实现修改为自适应格式化逻辑。

```python
def send_webhook_alert(webhook_url: str, message_content: str, threshold: float, date: str, is_relative: bool = False):
    """
    Send alert to Webhook (e.g., WeChat Work / 企业微信)
    """
    if not webhook_url:
        return
        
    if message_content.startswith("### 🔴"):
        # 已经是完整美化格式的卡片消息
        content = message_content
    elif message_content.startswith("🔔"):
        # 系统测试通知
        content = (
            f"### 🔴 GCP 费用超标告警\n"
            f"---\n"
            f"**📊 基本信息**\n"
            f"* **测试日期**：<font color=\"comment\">{date}</font>\n\n"
            f"**📢 测试内容**：\n"
            f"{message_content}"
        )
    else:
        # 兼容性回退
        threshold_display = f"{threshold * 100:.1f}%" if is_relative else f"${threshold:.2f}"
        content = (
            f"### 🔴 GCP 费用超标告警\n"
            f"---\n"
            f"**📊 基本信息**\n"
            f"* **告警日期**：<font color=\"comment\">{date}</font>\n"
            f"* **设定的告警阈值**：<font color=\"comment\">{threshold_display}</font>\n\n"
            f"**📋 详细内容**：\n"
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
```

- [ ] **Step 3: 运行单元测试验证功能正常**

在 `backend` 目录下运行：
`venv/bin/python test_alert.py`
预期输出：`OK`，测试全部通过。

- [ ] **Step 4: 提交 Task 1 的修改**

```bash
git add backend/scheduler.py
git commit -m "style: beautify send_webhook_alert wrapper template for WeCom"
```

---

### Task 2: 重构 Billing 维度告警排版生成

**Files:**
- Modify: `backend/scheduler.py:300-330`
- Test: `backend/test_alert.py`

**Interfaces:**
- Consumes: `exceeded_billings`, `config`, `start_dt`, `end_dt`, `days_to_check`
- Produces: `check_billing_and_alert` (Billing dimension block)

- [ ] **Step 1: 重构 scheduler.py 中 Billing 维度文本拼接逻辑**

定位到 [scheduler.py](file:///Users/huangjiajun/Project/Billing_Alert/backend/scheduler.py) 中，修改生成 `detail_header`、`top_projs_block` 和 `message_content` 的部分：

```python
                        if config.alert_type == "relative":
                            ratio_pct = b['change_ratio'] * 100
                            detail_header = (
                                f"**🚨 超标 Billing 账号**：`{b['id']}` ({bname})\n"
                                f"* **当前总费用**：<font color=\"warning\">${b['cost']:.2f}</font> (日期: {b['date']})\n"
                                f"* **历史同期费用**：<font color=\"comment\">${b['history_cost']:.2f}</font> (日期: {b['history_date']})\n"
                                f"* **整体费用涨幅**：<font color=\"warning\">{ratio_pct:+.2f}%</font>"
                            )
                        else:
                            detail_header = (
                                f"**🚨 超标 Billing 账号**：`{b['id']}` ({bname})\n"
                                f"* **当前单日费用**：<font color=\"warning\">${b['cost']:.2f}</font> (日期: {b['date']})"
                            )
                        
                        top_projs_str_list = []
                        for idx, p in enumerate(b['top_projects']):
                            top_projs_str_list.append(f"  {idx+1}. `{p['project_id']}` : **${p['cost']:.2f}** (占比 {p['percentage']:.1f}%)")
                        top_projs_block = "\n".join(top_projs_str_list) if top_projs_str_list else "  *(暂无项目明细数据)*"
                        
                        billing_details_list.append(f"{detail_header}\n* **该 Billing 下当日消费前 3 的 Top 项目**：\n{top_projs_block}")
                    
                    billing_details_all = "\n\n---\n\n".join(billing_details_list)
                    
                    threshold_display = f"{config.threshold_percentage * 100:.1f}%" if config.alert_type == "relative" else f"${config.threshold:.2f}"
                    message_content = (
                        f"### 🔴 GCP 费用超标告警\n"
                        f"---\n"
                        f"**📊 基本信息**\n"
                        f"* **告警名称**：`{config.alert_name}`{service_info}\n"
                        f"* **告警日期**：<font color=\"comment\">{start_dt} to {end_dt}</font>\n"
                        f"* **检查范围**：<font color=\"comment\">过去 {days_to_check} 天</font>\n"
                        f"* **设定的告警阈值**：<font color=\"comment\">{threshold_display}</font>\n\n"
                        f"**🚨 异常详情（共 {len(exceeded_billings)} 个账单账号超标）**\n"
                        f"---\n"
                        f"{billing_details_all}"
                    )
```

- [ ] **Step 2: 运行测试验证 Billing 维度断言正常通过**

在 `backend` 目录下运行：
`venv/bin/python test_alert.py`
确保 `test_billing_dimension_alert_trigger`、`test_absolute_alert_with_billing_dimension` 和 `test_relative_alert_with_billing_dimension` 等测试成功通过。
Expected output: `OK`

- [ ] **Step 3: 提交 Task 2 修改**

```bash
git add backend/scheduler.py
git commit -m "style: reform WeCom Billing alert layout with clean Red/Gray cards"
```

---

### Task 3: 重构 Project 维度告警排版生成

**Files:**
- Modify: `backend/scheduler.py:440-468`
- Test: `backend/test_alert.py`

**Interfaces:**
- Consumes: `exceeded_projects`, `config`, `start_dt`, `end_dt`, `days_to_check`
- Produces: `check_billing_and_alert` (Project dimension block)

- [ ] **Step 1: 重构 scheduler.py 中 Project 维度文本拼接逻辑**

定位并替换 Project 维度的消息构建部分：

```python
                        b_display = f"{billing_id} ({billing_name_map.get(billing_id, '未知')})" if billing_id != "未知Billing" else "未知Billing"
                        
                        if config.alert_type == "relative":
                            ratio_pct = p['change_ratio'] * 100
                            card_item = (
                                f"**📦 超标项目 [{idx+1}/{len(exceeded_projects)}]**：`{p['id']}`\n"
                                f"* **所属客户**：`{cust_name}`\n"
                                f"* **所属 Billing**：`{b_display}`\n"
                                f"* **当前费用**：<font color=\"warning\">${p['cost']:.2f}</font> (日期: {p['date']})\n"
                                f"* **历史费用**：<font color=\"comment\">${p['history_cost']:.2f}</font> (日期: {p['history_date']})\n"
                                f"* **费用涨幅**：<font color=\"warning\">{ratio_pct:+.2f}%</font>"
                            )
                        else:
                            card_item = (
                                f"**📦 超标项目 [{idx+1}/{len(exceeded_projects)}]**：`{p['id']}`\n"
                                f"* **所属客户**：`{cust_name}`\n"
                                f"* **所属 Billing**：`{b_display}`\n"
                                f"* **单日费用**：<font color=\"warning\">${p['cost']:.2f}</font> (日期: {p['date']})"
                            )
                        project_cards.append(card_item)

                    project_details_all = "\n\n---\n\n".join(project_cards)
                    
                    threshold_display = f"{config.threshold_percentage * 100:.1f}%" if config.alert_type == "relative" else f"${config.threshold:.2f}"
                    message_content = (
                        f"### 🔴 GCP 费用超标告警\n"
                        f"---\n"
                        f"**📊 基本信息**\n"
                        f"* **告警名称**：`{config.alert_name}`{service_info}\n"
                        f"* **告警日期**：<font color=\"comment\">{start_dt} to {end_dt}</font>\n"
                        f"* **检查范围**：<font color=\"comment\">过去 {days_to_check} 天</font>\n"
                        f"* **设定的告警阈值**：<font color=\"comment\">{threshold_display}</font>\n\n"
                        f"**🚨 异常详情（共 {len(exceeded_projects)} 个项目超标）**\n"
                        f"---\n"
                        f"{project_details_all}"
                    )
```

- [ ] **Step 2: 运行测试验证 Project 维度断言成功**

在 `backend` 目录下运行：
`venv/bin/python test_alert.py`
确保 `test_relative_alert_trigger_with_increase` 等项目维度相关测试均正常。
Expected output: `OK`

- [ ] **Step 3: 提交 Task 3 修改**

```bash
git add backend/scheduler.py
git commit -m "style: reform WeCom Project alert layout with clean Red/Gray cards"
```

---

## 4. 验证计划
在完成所有重构后，进行全局验证：
- 运行完整测试套件：`venv/bin/python test_alert.py`
- 确保测试没有任何报错，且所有通知的匹配逻辑全部稳健通过。
