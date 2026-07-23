# WeCom Separate Message Cards Per Item Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `check_billing_and_alert` in `backend/scheduler.py` so that each exceeded Project or Billing account is dispatched as its own independent WeCom Markdown alert card message via Webhook.

**Architecture:** Update Project dimension loop and Billing dimension loop in `backend/scheduler.py` to construct per-item `message_content` cards and call `send_webhook_alert` per item. Update test assertions in `backend/test_alert.py`.

---

## Global Constraints

- **Code Integrity**: Preserve all unrelated comments and docstrings.
- **Single Accent Color**: ONLY use `<font color="warning">` for cost values and increase ratios.
- **Chinese Labels**: All field labels (e.g. `告警阈值`, `告警日期`, `单日费用`, `所属 Billing`, `所属客户`, `Top 消费项目`) must use Chinese.
- **Test Verification**: All unit tests in `backend/test_alert.py` must pass (`backend/venv/bin/python test_alert.py`).

---

### Task 1: Refactor Billing-Dimension Loop to Send Separate Card Per Billing Account

**Files:**
- Modify: `backend/scheduler.py:316-348`
- Test: `backend/test_alert.py:289-434`

- [ ] **Step 1: Update Billing dimension alert loop in `backend/scheduler.py`**

Loop over `exceeded_billings`, construct per-billing card `message_content`, and invoke `send_webhook_alert` for each billing item.

```python
                    threshold_display = f"{config.threshold_percentage * 100:.1f}%" if config.alert_type == "relative" else f"${config.threshold:.2f}"
                    desc_text = config.service_description if config.service_description else config.alert_name

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
                        
                        message_content = (
                            f"# 🔴 GCP 费用超标告警\n\n"
                            f"> {desc_text}\n\n"
                            f"**告警阈值**\n"
                            f"🟠 {threshold_display}\n\n"
                            f"**告警日期**\n"
                            f"{start_dt} ~ {end_dt}\n\n"
                            f"{card_item}"
                        )
                        send_webhook_alert(config.webhook_url, message_content, config.threshold, start_dt, is_relative=(config.alert_type == "relative"))
```

- [ ] **Step 2: Update Billing dimension unit test assertions in `backend/test_alert.py`**

- [ ] **Step 3: Verify with unit tests**

Run: `backend/venv/bin/python test_alert.py`

- [ ] **Step 4: Commit**

```bash
git add backend/scheduler.py backend/test_alert.py
git commit -m "feat: send separate message card per exceeded billing account"
```

---

### Task 2: Refactor Project-Dimension Loop to Send Separate Card Per Project Item & Verify

**Files:**
- Modify: `backend/scheduler.py:454-498`
- Test: `backend/test_alert.py:132-181`, `test_alert.py:435-488`

- [ ] **Step 1: Update Project dimension alert loop in `backend/scheduler.py`**

Loop over `exceeded_projects`, construct per-project card `message_content`, and invoke `send_webhook_alert` for each project item.

```python
                    threshold_display = f"{config.threshold_percentage * 100:.1f}%" if config.alert_type == "relative" else f"${config.threshold:.2f}"
                    desc_text = config.service_description if config.service_description else config.alert_name

                    for p in exceeded_projects:
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
                            
                        message_content = (
                            f"# 🔴 GCP 费用超标告警\n\n"
                            f"> {desc_text}\n\n"
                            f"**告警阈值**\n"
                            f"🟠 {threshold_display}\n\n"
                            f"**告警日期**\n"
                            f"{start_dt} ~ {end_dt}\n\n"
                            f"{card_item}"
                        )
                        send_webhook_alert(config.webhook_url, message_content, config.threshold, start_dt, is_relative=(config.alert_type == "relative"))
```

- [ ] **Step 2: Update Project dimension unit test assertions in `backend/test_alert.py`**

- [ ] **Step 3: Run full unit test suite**

Run: `backend/venv/bin/python test_alert.py`

- [ ] **Step 4: Commit**

```bash
git add backend/scheduler.py backend/test_alert.py
git commit -m "feat: send separate message card per exceeded project item"
```
