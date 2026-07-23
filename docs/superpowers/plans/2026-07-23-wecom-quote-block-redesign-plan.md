# WeCom Quote-Block Overview Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign WeCom Markdown notification alert text generation to use an Overview top block followed by clean, individual quote-block cards per item, strictly applying a single accent color (`<font color="warning">`) to cost numbers.

**Architecture:** Update text formatting routines in `backend/scheduler.py` for helper wrapper (`send_webhook_alert`), Billing dimension alerts, and Project dimension alerts in `check_billing_and_alert`. Update unit test suite assertions in `backend/test_alert.py`.

**Tech Stack:** Python 3.9, FastAPI, WeChat Work Webhook Markdown API.

## Global Constraints

- **Code Integrity**: Preserve all unrelated comments and docstrings.
- **Single Accent Color**: ONLY use `<font color="warning">` for cost values and increase ratios. No `<font color="comment">` or `<font color="info">`.
- **Test Verification**: All 23 unit tests in `backend/test_alert.py` must pass using bypassed sandbox python (`backend/venv/bin/python test_alert.py`).

---

### Task 1: Refactor `send_webhook_alert` Helper Wrapper Template

**Files:**
- Modify: `backend/scheduler.py:108-140`
- Test: `backend/test_alert.py:489-576`

**Interfaces:**
- Consumes: `message_content: str`, `threshold: float`, `date: str`, `is_relative: bool`
- Produces: `send_webhook_alert`

- [ ] **Step 1: Update `send_webhook_alert` template in `backend/scheduler.py`**

```python
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
            f"# 🔴 GCP Billing Alert\n"
            f"> System Connection Test\n\n"
            f"**Alert Date**\n"
            f"{date}\n\n"
            f"**Test Content**\n"
            f"{message_content}"
        )
    else:
        # 兼容性回退
        threshold_display = f"{threshold * 100:.1f}%" if is_relative else f"${threshold:.2f}"
        content = (
            f"# 🔴 GCP Billing Alert\n"
            f"> Legacy Alert Message\n\n"
            f"**Threshold**\n"
            f"🟠 {threshold_display}\n\n"
            f"**Alert Date**\n"
            f"{date}\n\n"
            f"**Details**\n"
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

- [ ] **Step 2: Update `TestSendWebhookAlert` test assertions in `backend/test_alert.py`**

Update `test_send_webhook_alert_system_test` and `test_send_webhook_alert_legacy_fallback_*` to assert the exact `# 🔴 GCP Billing Alert` overview structure.

- [ ] **Step 3: Run unit tests to verify**

Run: `backend/venv/bin/python test_alert.py`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/scheduler.py backend/test_alert.py
git commit -m "style: update send_webhook_alert overview layout"
```

---

### Task 2: Refactor Billing-Dimension Alert Generation

**Files:**
- Modify: `backend/scheduler.py:316-348`
- Test: `backend/test_alert.py:289-434`

**Interfaces:**
- Consumes: `exceeded_billings`, `config`, `start_dt`, `end_dt`, `days_to_check`
- Produces: `check_billing_and_alert` (Billing dimension block)

- [ ] **Step 1: Refactor Billing dimension text builder in `backend/scheduler.py`**

```python
                        bname = billing_account_names.get(b['id'], "Unknown Account")
                        if config.alert_type == "relative":
                            ratio_pct = b['change_ratio'] * 100
                            card_item = (
                                f"## 💳 `{b['id']}` ({bname})\n"
                                f"> 💰 Cost: <font color=\"warning\">${b['cost']:.2f}</font>\n"
                                f"> 📈 Increase: <font color=\"warning\">{ratio_pct:+.2f}%</font>\n"
                                f"> 📜 History Cost: ${b['history_cost']:.2f}\n"
                                f"> 📅 Date: {b['date']}"
                            )
                        else:
                            card_item = (
                                f"## 💳 `{b['id']}` ({bname})\n"
                                f"> 💰 Cost: <font color=\"warning\">${b['cost']:.2f}</font>\n"
                                f"> 📅 Date: {b['date']}"
                            )
                        
                        top_projs_str_list = []
                        for idx, p in enumerate(b['top_projects']):
                            top_projs_str_list.append(f"> {idx+1}. `{p['project_id']}` : **${p['cost']:.2f}** ({p['percentage']:.1f}%)")
                        
                        if top_projs_str_list:
                            card_item += "\n> 🔝 Top Projects:\n" + "\n".join(top_projs_str_list)
                        else:
                            card_item += "\n> 🔝 Top Projects: None"
                            
                        billing_details_list.append(card_item)
                    
                    billing_details_all = "\n\n".join(billing_details_list)
                    
                    threshold_display = f"{config.threshold_percentage * 100:.1f}%" if config.alert_type == "relative" else f"${config.threshold:.2f}"
                    desc_text = config.service_description if config.service_description else config.alert_name
                    message_content = (
                        f"# 🔴 GCP Billing Alert\n\n"
                        f"> {desc_text}\n\n"
                        f"**Threshold**\n"
                        f"🟠 {threshold_display}\n\n"
                        f"**Alert Date**\n"
                        f"{start_dt} ~ {end_dt}\n\n"
                        f"**Billings Triggered**\n"
                        f"{len(exceeded_billings)}\n\n"
                        f"{billing_details_all}"
                    )
```

- [ ] **Step 2: Update Billing dimension unit tests in `backend/test_alert.py`**

Update `test_billing_dimension_alert_trigger`, `test_absolute_alert_with_billing_dimension`, and `test_relative_alert_with_billing_dimension`.

- [ ] **Step 3: Run unit tests to verify**

Run: `backend/venv/bin/python test_alert.py`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/scheduler.py backend/test_alert.py
git commit -m "style: reform Billing dimension alert quote-block layout"
```

---

### Task 3: Refactor Project-Dimension Alert Generation & Final Verification

**Files:**
- Modify: `backend/scheduler.py:454-498`
- Test: `backend/test_alert.py:132-181`, `test_alert.py:435-488`

**Interfaces:**
- Consumes: `exceeded_projects`, `config`, `start_dt`, `end_dt`, `days_to_check`
- Produces: `check_billing_and_alert` (Project dimension block)

- [ ] **Step 1: Refactor Project dimension text builder in `backend/scheduler.py`**

```python
                        cust_name = project_customer_map.get(p['id'], "Unknown")
                        billing_id = project_billing_ids.get(p['id'], "Unknown")
                        b_display = f"{billing_id} ({billing_name_map.get(billing_id, 'Unknown')})" if billing_id != "Unknown" else "Unknown"
                        
                        if config.alert_type == "relative":
                            ratio_pct = p['change_ratio'] * 100
                            card_item = (
                                f"## 📦 `{p['id']}`\n"
                                f"> 💰 Cost: <font color=\"warning\">${p['cost']:.2f}</font>\n"
                                f"> 📈 Increase: <font color=\"warning\">{ratio_pct:+.2f}%</font>\n"
                                f"> 📜 History Cost: ${p['history_cost']:.2f}\n"
                                f"> 📅 Date: {p['date']}\n"
                                f"> 🏢 Billing: `{b_display}`\n"
                                f"> 👤 Customer: {cust_name}"
                            )
                        else:
                            card_item = (
                                f"## 📦 `{p['id']}`\n"
                                f"> 💰 Cost: <font color=\"warning\">${p['cost']:.2f}</font>\n"
                                f"> 📅 Date: {p['date']}\n"
                                f"> 🏢 Billing: `{b_display}`\n"
                                f"> 👤 Customer: {cust_name}"
                            )
                        project_cards.append(card_item)

                    project_details_all = "\n\n".join(project_cards)
                    
                    threshold_display = f"{config.threshold_percentage * 100:.1f}%" if config.alert_type == "relative" else f"${config.threshold:.2f}"
                    desc_text = config.service_description if config.service_description else config.alert_name
                    message_content = (
                        f"# 🔴 GCP Billing Alert\n\n"
                        f"> {desc_text}\n\n"
                        f"**Threshold**\n"
                        f"🟠 {threshold_display}\n\n"
                        f"**Alert Date**\n"
                        f"{start_dt} ~ {end_dt}\n\n"
                        f"**Projects Triggered**\n"
                        f"{len(exceeded_projects)}\n\n"
                        f"{project_details_all}"
                    )
```

- [ ] **Step 2: Update Project dimension unit tests in `backend/test_alert.py`**

Update `test_relative_alert_trigger_with_increase` and `test_absolute_project_alert_trigger`.

- [ ] **Step 3: Run full unit test suite**

Run: `backend/venv/bin/python test_alert.py`
Expected: `OK` (23 passing)

- [ ] **Step 4: Commit**

```bash
git add backend/scheduler.py backend/test_alert.py
git commit -m "style: reform Project dimension alert quote-block layout"
```
