# Design Spec: WeCom Separate Message Cards Per Exceeded Item (Option 2)

**Date**: 2026-07-23  
**Status**: APPROVED  
**Goal**: Refactor WeChat Work (WeCom) alert notification dispatch logic so that each exceeded Project or Billing account is sent as its own independent message card via Webhook, rather than combining all exceeded items into a single long message.

---

## Architecture & Layout Changes

### 1. Project Dimension (Separate Card Per Exceeded Project)

For every project `p` in `exceeded_projects`, send an independent Markdown webhook alert card:

**Absolute Alert:**
```markdown
# 🔴 GCP 费用超标告警

> {service_description or alert_name}

**告警阈值**
🟠 ${threshold}

**告警日期**
{start_dt} ~ {end_dt}

## 📦 `{project_id}`
> 💰 单日费用：<font color="warning">${cost}</font>
> 📅 费用日期：{date}
> 🏢 所属 Billing：`{billing_id} ({billing_name})`
> 👤 所属客户：{customer_name}
```

**Relative Alert:**
```markdown
# 🔴 GCP 费用超标告警

> {service_description or alert_name}

**告警阈值**
🟠 {threshold_percentage}%

**告警日期**
{start_dt} ~ {end_dt}

## 📦 `{project_id}`
> 💰 单日费用：<font color="warning">${cost}</font>
> 📈 费用涨幅：<font color="warning">+{change_ratio}%</font>
> 📜 历史费用：${history_cost}
> 📅 费用日期：{date}
> 🏢 所属 Billing：`{billing_id} ({billing_name})`
> 👤 所属客户：{customer_name}
```

---

### 2. Billing Dimension (Separate Card Per Exceeded Billing Account)

For every billing account `b` in `exceeded_billings`, send an independent Markdown webhook alert card:

**Absolute Alert:**
```markdown
# 🔴 GCP 费用超标告警

> {service_description or alert_name}

**告警阈值**
🟠 ${threshold}

**告警日期**
{start_dt} ~ {end_dt}

## 💳 `{billing_account_id}` ({billing_display_name})
> 💰 单日费用：<font color="warning">${cost}</font>
> 📅 费用日期：{date}
> 🔝 Top 消费项目：
> 1. `{project_id}` : **${cost}** ({percentage}%)
```

**Relative Alert:**
```markdown
# 🔴 GCP 费用超标告警

> {service_description or alert_name}

**告警阈值**
🟠 {threshold_percentage}%

**告警日期**
{start_dt} ~ {end_dt}

## 💳 `{billing_account_id}` ({billing_display_name})
> 💰 单日费用：<font color="warning">${cost}</font>
> 📈 费用涨幅：<font color="warning">+{change_ratio}%</font>
> 📜 历史费用：${history_cost}
> 📅 费用日期：{date}
> 🔝 Top 消费项目：
> 1. `{project_id}` : **${cost}** ({percentage}%)
```

---

## Key Constraints

1. **Multiple Webhook Calls**: If 3 projects trigger alerts, 3 `send_webhook_alert` calls are executed sequentially.
2. **Single Accent Color**: Only cost and increase values use `<font color="warning">`.
3. **Chinese Labels**: All field labels strictly use Chinese.
4. **Unit Test Coverage**: Update all 24 unit tests in `backend/test_alert.py` to match the per-item card structure and webhook call counts.
