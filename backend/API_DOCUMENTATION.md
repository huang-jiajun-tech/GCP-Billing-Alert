# Billing Alert System - 环比告警功能接口文档与使用说明

本文档详细说明了后端 `alert` 告警模块中新增的**环比类型监控维度告警设置功能**，包括数据库变更、接口定义、参数校验、计算逻辑及告警通知格式。

---

## 1. 功能概述

环比告警功能允许用户设置基于历史周期（同比上周、同比上月）的费用涨幅告警。当指定项目在当前周期的日费用相比历史对应日期的日费用涨幅超过预设比例（如 50%）时，系统将自动触发告警，并通过 Webhook 或邮件通知相关人员。

---

## 2. 数据库层面变更

在 `alert_configs`（告警规则配置表）中新增了以下字段，用于支持环比告警的核心配置参数：

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `alert_type` | `VARCHAR` | `NOT NULL` | `'absolute'` | 告警类型：`'absolute'` (绝对值告警), `'relative'` (环比告警) |
| `comparison_window` | `VARCHAR` | `NULL` | `NULL` | 环比计算的时间窗口：`'week'` (同比上周), `'month'` (同比上月) |
| `threshold_percentage` | `DOUBLE PRECISION` | `NULL` | `NULL` | 环比触发阈值比例（例如 `0.5` 表示涨幅超过 50% 触发告警） |

---

## 3. 接口变更与参数校验

### 3.1 新增/编辑告警规则接口

* **新增接口**：`POST /api/alerts`
* **编辑接口**：`PUT /api/alerts/{config_id}`

#### 请求参数说明（Pydantic Schema: `AlertConfigBase`）

在原有的参数基础上，新增了环比相关的可选参数：

```json
{
  "alert_name": "测试环比告警",
  "project_ids": ["project-a", "project-b"],
  "service_description": "Compute Engine",
  "time_range_days": 1,
  "threshold": 0.0,
  "email": "admin@example.com",
  "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
  "is_active": true,
  "alert_type": "relative",
  "comparison_window": "week",
  "threshold_percentage": 0.5
}
```

#### 参数校验规则（`validate_alert_config`）

接口层面对传入的参数进行了严格的合规性校验：

1. **告警类型校验**：`alert_type` 必须为 `'absolute'` 或 `'relative'` 之一。
2. **绝对值告警校验**（`alert_type == 'absolute'`）：
   * 阈值 `threshold` 必须大于 `0`。
3. **环比告警校验**（`alert_type == 'relative'`）：
   * 时间窗口 `comparison_window` 必须提供，且只能为 `'week'`（同比上周）或 `'month'`（同比上月）之一。
   * 阈值比例 `threshold_percentage` 必须提供，且必须大于 `0`。

---

## 4. 后端调度与计算逻辑

告警规则的执行调度逻辑（`check_billing_and_alert`）已完成改造，新增了环比指标的计算能力：

1. **历史数据拉取**：
   * 根据告警规则的 `comparison_window`，自动将数据查询范围往前推移（同比上周往前推 7 天，同比上月往前推 30 天），一次性拉取当前周期与历史周期的监控数据，避免多次查询数据库。
2. **环比指标计算**：
   * 针对当前周期内的每一天，计算其与历史对应日期的费用差值及涨幅比例：
     $$\text{涨幅比例} = \frac{\text{当前费用} - \text{历史费用}}{\text{历史费用}}$$
3. **边界场景与异常处理**：
   * **历史数据缺失或为 0**：如果历史对应日期的费用缺失或为 `0`，系统将自动跳过该天的环比计算，**不触发告警**，从而有效避免因新项目上线、历史数据不全导致的误告警，并防止除以零导致的系统崩溃。
   * **监控数据为 0**：如果当前费用为 `0`，且历史费用大于 `0`（即费用下跌），计算出的涨幅比例为负数，不会超过正数阈值，**不触发告警**。

---

## 5. 告警通知内容完善

触发环比告警后，系统发送的 Webhook（如企业微信）和邮件通知内容已进行适配和完善，清晰标注了环比告警的类型、具体涨跌幅数值、对比的历史周期等信息。

### 5.1 企业微信 Webhook 消息示例

```markdown
## ⚠️ GCP 费用超额告警
**告警日期**：2026-06-17 to 2026-06-24
**设定的告警阈值**：50.0%

> 告警名称: 测试环比告警 (服务: Compute Engine)
> 告警类型: 环比告警 (同比上周)
> 设定阈值比例: 50.0%
> 检查范围: 过去 1 天
> 环比超标项目详情:
> - project-a: 当前费用 $160.00 (日期: 2026-06-24), 历史费用 $100.00 (日期: 2026-06-17), 涨幅: +60.00%
```

---

## 6. 单元测试与验证

项目已编写完整的单元测试文件 `backend/test_alert.py`，覆盖了以下场景：
* 绝对值告警参数校验（成功与失败边界）
* 环比告警参数校验（缺失窗口、无效窗口、缺失比例、无效比例等）
* 环比告警触发逻辑（涨幅超过阈值触发、未超过不触发）
* 边界场景测试（历史数据缺失、历史数据为 0 时的异常处理）

### 运行测试命令
在 `backend` 目录下激活虚拟环境后运行：
```bash
python test_alert.py
```
