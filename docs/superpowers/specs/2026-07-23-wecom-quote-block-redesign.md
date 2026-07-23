# Design Spec: WeCom Quote-Block Overview & Card Redesign (Chinese Labels)

**Date**: 2026-07-23  
**Status**: APPROVED  
**Goal**: Redesign WeChat Work (WeCom) alert notifications to use a clean Chinese Overview top block followed by individual quote blocks for each triggered project or billing account, strictly adhering to a single accent color (`<font color="warning">`) for cost values.

---

## 1. Design Overview

### Layout Architecture
Each alert message is divided into two distinct logical sections:
1. **Overview Section (总览区 - 中文)**:
   - `# 🔴 GCP 费用超标告警` header
   - Blockquote containing service description or alert name context (e.g., `> Vertex AI 日费用超标`)
   - `**告警阈值**` label followed by `🟠 $10,000.00` or `🟠 50.0%`
   - `**告警日期**` label followed by `{start_dt} ~ {end_dt}`
   - `**超标项目数**` / `**超标 Billing 数**` count

2. **Item Quote-Block Section (明细卡片区 - 中文)**:
   - Level-2 header per item: `## 📦 {project_id}` or `## 💳 {billing_id} ({billing_name})`
   - Single quote block (`>`) containing all key-value attributes for that item
   - Key attributes formatted cleanly with dedicated emojis (`💰 单日费用`, `📈 费用涨幅`, `📜 历史费用`, `📅 费用日期`, `🏢 所属 Billing`, `👤 所属客户`, `🔝 Top 消费项目`)

---

## 2. Color System Specifications

- **Accent Color (`<font color="warning">`)**:
  - ONLY used for current cost values (e.g., `<font color="warning">$10,528.31</font>`) and percentage increases (e.g., `<font color="warning">+60.00%</font>`).
- **Default Text Color**:
  - All other fields (dates, thresholds, account IDs, customer names, history costs, static labels) use default Markdown text color without any `<font>` wrappers.
- **Removed Colors**:
  - `<font color="comment">` and `<font color="info">` are completely eliminated to keep the palette minimal and clean.

---

## 3. Detailed Templates

### 3.1 Project Dimension Template (Absolute & Relative)

```markdown
# 🔴 GCP 费用超标告警

> Vertex AI 日费用超标

**告警阈值**
🟠 $10,000.00

**告警日期**
2026-07-19 ~ 2026-07-21

**超标项目数**
3

## 📦 dmqt-260527
> 💰 单日费用：<font color="warning">$10,528.31</font>
> 📅 费用日期：2026-07-19
> 🏢 所属 Billing：`014945-B990E9-0ABB7C (dam-cm-128a)`
> 👤 所属客户：未知客户

## 📦 wpqt-260527
> 💰 单日费用：<font color="warning">$10,493.89</font>
> 📅 费用日期：2026-07-19
> 🏢 所属 Billing：`018FE4-A7883B-43CCAF (wepie-cm-128a)`
> 👤 所属客户：未知客户
```

*For Relative Alerts (Project Dimension)*:
```markdown
## 📦 dmqt-260527
> 💰 单日费用：<font color="warning">$10,528.31</font>
> 📈 费用涨幅：<font color="warning">+60.00%</font>
> 📜 历史费用：$6,580.00
> 📅 费用日期：2026-07-19
> 🏢 所属 Billing：`014945-B990E9-0ABB7C (dam-cm-128a)`
> 👤 所属客户：未知客户
```

---

### 3.2 Billing Dimension Template (Absolute & Relative)

```markdown
# 🔴 GCP 费用超标告警

> Billing 账号额度监控

**告警阈值**
🟠 $1,000.00

**告警日期**
2026-07-21 ~ 2026-07-21

**超标 Billing 数**
1

## 💳 014945-B990E9-0ABB7C (Main Billing)
> 💰 单日费用：<font color="warning">$1,200.00</font>
> 📅 费用日期：2026-07-21
> 🔝 Top 消费项目：
> 1. `proj-a` : **$500.00** (41.7%)
> 2. `proj-b` : **$400.00** (33.3%)
> 3. `proj-c` : **$200.00** (16.7%)
```

---

### 3.3 Helper Wrapper (`send_webhook_alert`) Template

```markdown
# 🔴 GCP 费用超标告警

> 系统连接测试

**测试日期**
2026-07-22

**测试内容**
🔔 这是一条系统测试通知
```

---

## 4. Verification & Testing

1. All 23 unit tests in `backend/test_alert.py` will be updated to match the exact Chinese label structure and assertions.
2. Verified using bypassed sandbox execution: `/Users/huangjiajun/Project/Billing_Alert/backend/venv/bin/python test_alert.py`.
