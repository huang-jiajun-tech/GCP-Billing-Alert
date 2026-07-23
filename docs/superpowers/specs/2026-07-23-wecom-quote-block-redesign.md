# Design Spec: WeCom Quote-Block Overview & Card Redesign

**Date**: 2026-07-23  
**Status**: APPROVED  
**Goal**: Redesign WeChat Work (WeCom) alert notifications to use a clean Overview top block followed by individual quote blocks for each triggered project or billing account, strictly adhering to a single accent color (`<font color="warning">`) for cost values.

---

## 1. Design Overview

### Layout Architecture
Each alert message is divided into two distinct logical sections:
1. **Overview Section (总览区)**:
   - `# 🔴 GCP Billing Alert` header
   - Blockquote containing service description or alert name context
   - `**Threshold**` label followed by `🟠 $10,000.00` or `🟠 50.0%`
   - `**Alert Date**` label followed by `{start_dt} ~ {end_dt}`
   - `**Projects Triggered**` / `**Billings Triggered**` count

2. **Item Quote-Block Section (明细卡片区)**:
   - Level-2 header per item: `## 📦 {project_id}` or `## 💳 {billing_id} ({billing_name})`
   - Single quote block (`>`) containing all key-value attributes for that item
   - Key attributes formatted cleanly with dedicated emojis (`💰 Cost`, `📈 Increase`, `📜 History Cost`, `📅 Date`, `🏢 Billing`, `👤 Customer`, `🔝 Top Projects`)

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
# 🔴 GCP Billing Alert

> Vertex AI Daily Cost Exceeded

**Threshold**
🟠 $10,000.00

**Alert Date**
2026-07-19 ~ 2026-07-21

**Projects Triggered**
3

## 📦 dmqt-260527
> 💰 Cost: <font color="warning">$10,528.31</font>
> 📅 Date: 2026-07-19
> 🏢 Billing: `014945-B990E9-0ABB7C (dam-cm-128a)`
> 👤 Customer: Unknown

## 📦 wpqt-260527
> 💰 Cost: <font color="warning">$10,493.89</font>
> 📅 Date: 2026-07-19
> 🏢 Billing: `018FE4-A7883B-43CCAF (wepie-cm-128a)`
> 👤 Customer: Unknown
```

*For Relative Alerts (Project Dimension)*:
```markdown
## 📦 dmqt-260527
> 💰 Cost: <font color="warning">$10,528.31</font>
> 📈 Increase: <font color="warning">+60.00%</font>
> 📜 History Cost: $6,580.00
> 📅 Date: 2026-07-19
> 🏢 Billing: `014945-B990E9-0ABB7C (dam-cm-128a)`
> 👤 Customer: Unknown
```

---

### 3.2 Billing Dimension Template (Absolute & Relative)

```markdown
# 🔴 GCP Billing Alert

> Billing Absolute Alert

**Threshold**
🟠 $1,000.00

**Alert Date**
2026-07-21 ~ 2026-07-21

**Billings Triggered**
1

## 💳 014945-B990E9-0ABB7C (Main Billing)
> 💰 Cost: <font color="warning">$1,200.00</font>
> 📅 Date: 2026-07-21
> 🔝 Top Projects:
> 1. `proj-a` : **$500.00** (41.7%)
> 2. `proj-b` : **$400.00** (33.3%)
> 3. `proj-c` : **$200.00** (16.7%)
```

---

### 3.3 Helper Wrapper (`send_webhook_alert`) Template

```markdown
# 🔴 GCP Billing Alert

> System Connection Test

**Alert Date**
2026-07-22

**Test Content**
🔔 这是一条系统测试通知
```

---

## 4. Verification & Testing

1. All 23 unit tests in `backend/test_alert.py` will be updated to match the exact new structure and assertions.
2. Verified using bypassed sandbox execution: `/Users/huangjiajun/Project/Billing_Alert/backend/venv/bin/python test_alert.py`.
