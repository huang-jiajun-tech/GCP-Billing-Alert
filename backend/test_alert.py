import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, date
from fastapi import HTTPException

# Import modules to test
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import schemas
import models
from main import validate_alert_config
from scheduler import check_billing_and_alert, send_webhook_alert

class TestAlertConfigValidation(unittest.TestCase):
    def test_absolute_alert_validation_success(self):
        # Valid absolute alert
        config = schemas.AlertConfigCreate(
            alert_name="Test Absolute",
            threshold=100.0,
            alert_type="absolute"
        )
        # Should not raise exception
        validate_alert_config(config)

    def test_dimension_validation_success_billing(self):
        # Valid billing dimension alert
        config = schemas.AlertConfigCreate(
            alert_name="Test Billing Dimension",
            threshold=100.0,
            alert_type="absolute",
            dimension="billing"
        )
        # Should not raise exception
        validate_alert_config(config)

    def test_dimension_validation_failure_invalid(self):
        # Invalid dimension parameter value
        config = schemas.AlertConfigCreate(
            alert_name="Test Invalid Dimension",
            threshold=100.0,
            alert_type="absolute",
            dimension="invalid_dimension"
        )
        with self.assertRaises(HTTPException) as context:
            validate_alert_config(config)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "dimension must be either 'project' or 'billing'")

    def test_absolute_alert_validation_failure(self):
        # Invalid absolute alert (threshold <= 0)
        config = schemas.AlertConfigCreate(
            alert_name="Test Absolute",
            threshold=0.0,
            alert_type="absolute"
        )
        with self.assertRaises(HTTPException) as context:
            validate_alert_config(config)
        self.assertEqual(context.exception.status_code, 400)

    def test_relative_alert_validation_success(self):
        # Valid relative alert
        config = schemas.AlertConfigCreate(
            alert_name="Test Relative",
            alert_type="relative",
            comparison_window="week",
            threshold_percentage=0.5
        )
        # Should not raise exception
        validate_alert_config(config)

    def test_relative_alert_validation_missing_window(self):
        # Missing comparison_window
        config = schemas.AlertConfigCreate(
            alert_name="Test Relative",
            alert_type="relative",
            threshold_percentage=0.5
        )
        with self.assertRaises(HTTPException) as context:
            validate_alert_config(config)
        self.assertEqual(context.exception.status_code, 400)

    def test_relative_alert_validation_invalid_window(self):
        # Invalid comparison_window
        config = schemas.AlertConfigCreate(
            alert_name="Test Relative",
            alert_type="relative",
            comparison_window="year",
            threshold_percentage=0.5
        )
        with self.assertRaises(HTTPException) as context:
            validate_alert_config(config)
        self.assertEqual(context.exception.status_code, 400)

    def test_relative_alert_validation_missing_percentage(self):
        # Missing threshold_percentage
        config = schemas.AlertConfigCreate(
            alert_name="Test Relative",
            alert_type="relative",
            comparison_window="week"
        )
        with self.assertRaises(HTTPException) as context:
            validate_alert_config(config)
        self.assertEqual(context.exception.status_code, 400)

    def test_relative_alert_validation_invalid_percentage(self):
        # Invalid threshold_percentage (<= 0)
        config = schemas.AlertConfigCreate(
            alert_name="Test Relative",
            alert_type="relative",
            comparison_window="week",
            threshold_percentage=-0.1
        )
        with self.assertRaises(HTTPException) as context:
            validate_alert_config(config)
        self.assertEqual(context.exception.status_code, 400)

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


class TestAlertSchedulerLogic(unittest.TestCase):
    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_relative_alert_trigger_with_increase(self, mock_send_webhook, mock_crud, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        config = models.AlertConfig(
            id=1,
            alert_name="Relative Week Alert",
            alert_type="relative",
            comparison_window="week",
            threshold_percentage=0.5,
            time_range_days=1,
            is_active=True,
            webhook_url="http://mock-webhook"
        )
        mock_crud.get_alert_configs.return_value = [config]
        
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        history_day = yesterday - timedelta(days=7)
        
        usage_current = MagicMock(project_id="proj-1", cost=160.0, usage_date=yesterday) # 60% increase
        usage_history = MagicMock(project_id="proj-1", cost=100.0, usage_date=history_day)
        
        mock_crud.get_daily_usage.return_value = [usage_current, usage_history]
        mock_crud.get_recent_handled_incidents.return_value = []
        mock_db.query().filter().first.return_value = None
        
        check_billing_and_alert()
        
        # Verify webhook was called
        mock_send_webhook.assert_called_once()
        call_args = mock_send_webhook.call_args[0]
        webhook_url_arg = call_args[0]
        message_content_arg = call_args[1]
        
        self.assertEqual(webhook_url_arg, "http://mock-webhook")
        self.assertIn("# 🔴 GCP 费用超标告警\n\n", message_content_arg)
        self.assertIn("> Relative Week Alert\n\n", message_content_arg)
        self.assertIn("## 📦 `proj-1`\n", message_content_arg)
        self.assertIn("> 💰 单日费用：<font color=\"warning\">$160.00</font>\n", message_content_arg)
        self.assertIn("> 📈 费用涨幅：<font color=\"warning\">+60.00%</font>\n", message_content_arg)
        self.assertIn("> 📜 历史费用：$100.00\n", message_content_arg)
        self.assertIn("> 📅 费用日期：", message_content_arg)
        self.assertIn("> 🏢 所属 Billing：`未知 Billing`\n", message_content_arg)
        self.assertIn("> 👤 所属客户：未知客户", message_content_arg)
        
        # Verify incident was created
        mock_crud.create_alert_incident.assert_called_once()

    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_relative_alert_no_trigger_low_increase(self, mock_send_webhook, mock_crud, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        config = models.AlertConfig(
            id=1,
            alert_name="Relative Week Alert",
            alert_type="relative",
            comparison_window="week",
            threshold_percentage=0.5,
            time_range_days=1,
            is_active=True,
            webhook_url="http://mock-webhook"
        )
        mock_crud.get_alert_configs.return_value = [config]
        
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        history_day = yesterday - timedelta(days=7)
        
        usage_current = MagicMock(project_id="proj-1", cost=120.0, usage_date=yesterday) # 20% increase
        usage_history = MagicMock(project_id="proj-1", cost=100.0, usage_date=history_day)
        
        mock_crud.get_daily_usage.return_value = [usage_current, usage_history]
        mock_crud.get_recent_handled_incidents.return_value = []
        mock_db.query().filter().first.return_value = None
        
        check_billing_and_alert()
        
        # Verify webhook was NOT called
        mock_send_webhook.assert_not_called()
        mock_crud.create_alert_incident.assert_not_called()

    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_relative_alert_boundary_missing_history(self, mock_send_webhook, mock_crud, mock_session_local):
        # Test boundary: history data is missing
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        config = models.AlertConfig(
            id=1,
            alert_name="Relative Week Alert",
            alert_type="relative",
            comparison_window="week",
            threshold_percentage=0.5,
            time_range_days=1,
            is_active=True,
            webhook_url="http://mock-webhook"
        )
        mock_crud.get_alert_configs.return_value = [config]
        
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        
        usage_current = MagicMock(project_id="proj-1", cost=160.0, usage_date=yesterday)
        # No history data returned
        mock_crud.get_daily_usage.return_value = [usage_current]
        mock_crud.get_recent_handled_incidents.return_value = []
        mock_db.query().filter().first.return_value = None
        
        # Should not raise exception and should not trigger alert
        check_billing_and_alert()
        
        mock_send_webhook.assert_not_called()
        mock_crud.create_alert_incident.assert_not_called()

    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_relative_alert_boundary_zero_history(self, mock_send_webhook, mock_crud, mock_session_local):
        # Test boundary: history data is 0
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        config = models.AlertConfig(
            id=1,
            alert_name="Relative Week Alert",
            alert_type="relative",
            comparison_window="week",
            threshold_percentage=0.5,
            time_range_days=1,
            is_active=True,
            webhook_url="http://mock-webhook"
        )
        mock_crud.get_alert_configs.return_value = [config]
        
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        history_day = yesterday - timedelta(days=7)
        
        usage_current = MagicMock(project_id="proj-1", cost=160.0, usage_date=yesterday)
        usage_history = MagicMock(project_id="proj-1", cost=0.0, usage_date=history_day) # History cost is 0
        
        mock_crud.get_daily_usage.return_value = [usage_current, usage_history]
        mock_crud.get_recent_handled_incidents.return_value = []
        mock_db.query().filter().first.return_value = None
        
        # Should not raise exception and should not trigger alert
        check_billing_and_alert()
        
        mock_send_webhook.assert_not_called()
        mock_crud.create_alert_incident.assert_not_called()

    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_billing_dimension_alert_trigger(self, mock_send_webhook, mock_crud, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock billing accounts display names
        billing_acc1 = MagicMock(billing_account_id="billing-1", display_name="Test Account 1")
        mock_crud.get_billing_accounts.return_value = [billing_acc1]
        
        # Mock project info for customer names
        proj_info1 = MagicMock(project_id="proj-1", customer_name="Customer A")
        mock_crud.get_all_project_infos.return_value = [proj_info1]

        config = models.AlertConfig(
            id=2,
            alert_name="Billing Absolute Alert",
            alert_type="absolute",
            threshold=100.0,
            time_range_days=1,
            is_active=True,
            dimension="billing",
            webhook_url="http://mock-webhook"
        )
        mock_crud.get_alert_configs.return_value = [config]
        
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        
        # Specify type of billing_account_id as string so our scheduler accepts it
        usage_current_1 = MagicMock(project_id="proj-1", billing_account_id="billing-1", cost=150.0, usage_date=yesterday)
        
        mock_crud.get_daily_usage.return_value = [usage_current_1]
        mock_db.query().filter().first.return_value = None
        
        check_billing_and_alert()
        
        # Verify webhook was called
        mock_send_webhook.assert_called_once()
        args = mock_send_webhook.call_args[0]
        self.assertEqual(args[0], "http://mock-webhook")
        self.assertIn("# 🔴 GCP 费用超标告警\n\n", args[1])
        self.assertIn("## 💳 `billing-1` (Test Account 1)\n", args[1])
        self.assertIn("> 💰 单日费用：<font color=\"warning\">$150.00</font>\n", args[1])
        # Verify incident was created
        mock_crud.create_alert_incident.assert_called_once()

    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_absolute_alert_with_billing_dimension(self, mock_send_webhook, mock_crud, mock_session_local):
        # 设定 Mock
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # 配置 Billing 维度的绝对额告警
        config = models.AlertConfig(
            id=2,
            alert_name="Billing Absolute Alert",
            dimension="billing",
            billing_account_ids=["billing-1"],
            threshold=1000.0,
            alert_type="absolute",
            time_range_days=1,
            is_active=True,
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
        mock_db.query().filter().first.return_value = None
        
        # 运行检测
        check_billing_and_alert()
        
        # 检查是否成功触发 Webhook 报警，且参数格式化包含 Top 项目
        mock_send_webhook.assert_called_once()
        args = mock_send_webhook.call_args[0]
        self.assertEqual(args[0], "http://mock-webhook") # URL
        self.assertIn("# 🔴 GCP 费用超标告警\n\n", args[1])
        self.assertIn("> Billing Absolute Alert\n\n", args[1])
        self.assertIn("## 💳 `billing-1` (Main Billing)\n", args[1])
        self.assertIn("> 💰 单日费用：<font color=\"warning\">$1200.00</font>\n", args[1])
        self.assertIn("> 🔝 Top 消费项目：\n", args[1])
        self.assertIn("> 1. `proj-a` : **$500.00** (41.7%)", args[1])
        self.assertIn("> 2. `proj-b` : **$400.00** (33.3%)", args[1])
        self.assertIn("> 3. `proj-c` : **$200.00** (16.7%)", args[1])
        self.assertNotIn("proj-d", args[1]) # 确保 Top 4 被截断未显示

    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_relative_alert_with_billing_dimension(self, mock_send_webhook, mock_crud, mock_session_local):
        # 设定 Mock
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # 配置 Billing 维度的环比告警
        config = models.AlertConfig(
            id=3,
            alert_name="Billing Relative Alert",
            dimension="billing",
            billing_account_ids=["billing-1"],
            threshold_percentage=0.5,
            alert_type="relative",
            comparison_window="week",
            time_range_days=1,
            is_active=True,
            webhook_url="http://mock-webhook"
        )
        mock_crud.get_alert_configs.return_value = [config]
        mock_crud.get_billing_accounts.return_value = [
            models.BillingAccount(billing_account_id="billing-1", display_name="Main Billing")
        ]
        mock_crud.get_all_project_infos.return_value = []
        
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        history_day = yesterday - timedelta(days=7)
        
        # 组装 usages (昨日花费加总为 160，历史同期为 100，涨幅 60% 超过阈值 50%)
        usages = [
            models.DailyUsage(project_id="proj-a", billing_account_id="billing-1", cost=100.0, usage_date=yesterday, currency="USD"),
            models.DailyUsage(project_id="proj-b", billing_account_id="billing-1", cost=60.0, usage_date=yesterday, currency="USD"),
            models.DailyUsage(project_id="proj-a", billing_account_id="billing-1", cost=100.0, usage_date=history_day, currency="USD")
        ]
        mock_crud.get_daily_usage.return_value = usages
        mock_db.query().filter().first.return_value = None
        
        # 运行检测
        check_billing_and_alert()
        
        # 检查是否成功触发 Webhook 报警
        mock_send_webhook.assert_called_once()
        args = mock_send_webhook.call_args[0]
        self.assertEqual(args[0], "http://mock-webhook") # URL
        self.assertIn("# 🔴 GCP 费用超标告警\n\n", args[1])
        self.assertIn("> Billing Relative Alert\n\n", args[1])
        self.assertIn("## 💳 `billing-1` (Main Billing)\n", args[1])
        self.assertIn("> 💰 单日费用：<font color=\"warning\">$160.00</font>\n", args[1])
        self.assertIn("> 📈 费用涨幅：<font color=\"warning\">+60.00%</font>\n", args[1])
        self.assertIn("> 📜 历史费用：$100.00\n", args[1])
        self.assertIn("> 1. `proj-a` : **$100.00** (62.5%)", args[1])
        self.assertIn("> 2. `proj-b` : **$60.00** (37.5%)", args[1])

    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_absolute_alert_with_multiple_billing_dimensions(self, mock_send_webhook, mock_crud, mock_session_local):
        # 设定 Mock
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # 配置 Billing 维度的绝对额告警
        config = models.AlertConfig(
            id=2,
            alert_name="Billing Absolute Alert",
            dimension="billing",
            billing_account_ids=["billing-1", "billing-2"],
            threshold=100.0,
            alert_type="absolute",
            time_range_days=1,
            is_active=True,
            webhook_url="http://mock-webhook"
        )
        mock_crud.get_alert_configs.return_value = [config]
        mock_crud.get_billing_accounts.return_value = [
            models.BillingAccount(billing_account_id="billing-1", display_name="Main Billing 1"),
            models.BillingAccount(billing_account_id="billing-2", display_name="Main Billing 2")
        ]
        mock_crud.get_all_project_infos.return_value = []
        
        usage_date = (datetime.utcnow() - timedelta(days=1)).date()
        usages = [
            models.DailyUsage(project_id="proj-a", billing_account_id="billing-1", cost=150.0, usage_date=usage_date, currency="USD"),
            models.DailyUsage(project_id="proj-b", billing_account_id="billing-2", cost=200.0, usage_date=usage_date, currency="USD")
        ]
        mock_crud.get_daily_usage.return_value = usages
        mock_db.query().filter().first.return_value = None
        
        # 运行检测
        check_billing_and_alert()
        
        # 检查是否成功触发 Webhook 报警，且因为有两个超标 billing，所以分别发送了独立的消息卡片
        self.assertEqual(mock_send_webhook.call_count, 2)
        
        # 检查两次调用的参数
        calls = mock_send_webhook.call_args_list
        urls = [call[0][0] for call in calls]
        contents = [call[0][1] for call in calls]
        
        self.assertEqual(urls, ["http://mock-webhook", "http://mock-webhook"])
        
        # 必须一个包含 billing-1，一个包含 billing-2
        has_billing_1 = any("## 💳 `billing-1` (Main Billing 1)" in content for content in contents)
        has_billing_2 = any("## 💳 `billing-2` (Main Billing 2)" in content for content in contents)
        self.assertTrue(has_billing_1)
        self.assertTrue(has_billing_2)

    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_absolute_project_alert_trigger(self, mock_send_webhook, mock_crud, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock billing accounts display names
        billing_acc = MagicMock(billing_account_id="billing-123", display_name="Test Billing Account")
        mock_crud.get_billing_accounts.return_value = [billing_acc]
        
        # Mock project info for customer names
        proj_info = MagicMock(project_id="proj-absolute", customer_name="Customer XYZ")
        mock_crud.get_all_project_infos.return_value = [proj_info]

        config = models.AlertConfig(
            id=3,
            alert_name="Project Absolute Alert",
            alert_type="absolute",
            threshold=50.0,
            time_range_days=1,
            is_active=True,
            dimension="project",
            webhook_url="http://mock-webhook"
        )
        mock_crud.get_alert_configs.return_value = [config]
        
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        
        # Current cost is $75.0, which exceeds absolute threshold of $50.0
        usage_current = MagicMock(project_id="proj-absolute", billing_account_id="billing-123", cost=75.0, usage_date=yesterday)
        
        mock_crud.get_daily_usage.return_value = [usage_current]
        mock_crud.get_recent_handled_incidents.return_value = []
        mock_db.query().filter().first.return_value = None
        
        check_billing_and_alert()
        
        # Verify webhook was called with correct arguments
        mock_send_webhook.assert_called_once()
        call_args = mock_send_webhook.call_args[0]
        webhook_url_arg = call_args[0]
        message_content_arg = call_args[1]
        
        self.assertEqual(webhook_url_arg, "http://mock-webhook")
        self.assertIn("# 🔴 GCP 费用超标告警\n\n", message_content_arg)
        self.assertIn("> Project Absolute Alert\n\n", message_content_arg)
        self.assertIn("## 📦 `proj-absolute`\n", message_content_arg)
        self.assertIn("> 💰 单日费用：<font color=\"warning\">$75.00</font>\n", message_content_arg)
        self.assertIn("> 📅 费用日期：", message_content_arg)
        self.assertIn("> 🏢 所属 Billing：`billing-123 (Test Billing Account)`\n", message_content_arg)
        self.assertIn("> 👤 所属客户：Customer XYZ", message_content_arg)
        
        # Verify incident was created
        mock_crud.create_alert_incident.assert_called_once()

    @patch('scheduler.SessionLocal')
    @patch('scheduler.crud')
    @patch('scheduler.send_webhook_alert')
    def test_absolute_project_alert_trigger_multiple_projects(self, mock_send_webhook, mock_crud, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock billing accounts display names
        billing_acc = MagicMock(billing_account_id="billing-123", display_name="Test Billing Account")
        mock_crud.get_billing_accounts.return_value = [billing_acc]
        
        # Mock project info for customer names
        proj_info_1 = MagicMock(project_id="proj-absolute-1", customer_name="Customer XYZ")
        proj_info_2 = MagicMock(project_id="proj-absolute-2", customer_name="Customer ABC")
        mock_crud.get_all_project_infos.return_value = [proj_info_1, proj_info_2]

        config = models.AlertConfig(
            id=3,
            alert_name="Project Absolute Alert",
            alert_type="absolute",
            threshold=50.0,
            time_range_days=1,
            is_active=True,
            dimension="project",
            webhook_url="http://mock-webhook"
        )
        mock_crud.get_alert_configs.return_value = [config]
        
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        
        # Two projects exceed absolute threshold of $50.0
        usage_current_1 = MagicMock(project_id="proj-absolute-1", billing_account_id="billing-123", cost=75.0, usage_date=yesterday)
        usage_current_2 = MagicMock(project_id="proj-absolute-2", billing_account_id="billing-123", cost=120.0, usage_date=yesterday)
        
        mock_crud.get_daily_usage.return_value = [usage_current_1, usage_current_2]
        mock_crud.get_recent_handled_incidents.return_value = []
        mock_db.query().filter().first.return_value = None
        
        check_billing_and_alert()
        
        # Verify webhook was called TWICE (one for each project)
        self.assertEqual(mock_send_webhook.call_count, 2)
        
        calls = mock_send_webhook.call_args_list
        urls = [call[0][0] for call in calls]
        contents = [call[0][1] for call in calls]
        
        self.assertEqual(urls, ["http://mock-webhook", "http://mock-webhook"])
        
        # Check that one content contains proj-absolute-1 and the other proj-absolute-2
        has_proj_1 = any("## 📦 `proj-absolute-1`" in content for content in contents)
        has_proj_2 = any("## 📦 `proj-absolute-2`" in content for content in contents)
        self.assertTrue(has_proj_1)
        self.assertTrue(has_proj_2)
        
        # Verify incident was created for both
        self.assertEqual(mock_crud.create_alert_incident.call_count, 2)

class TestSendWebhookAlert(unittest.TestCase):
    @patch('scheduler.requests.post')
    def test_send_webhook_alert_beautified(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        webhook_url = "http://mock-webhook"
        
        # Test with ### 🔴
        message_content_3 = "### 🔴 GCP 费用超标告警\n---\n**📊 基本信息**"
        send_webhook_alert(webhook_url, message_content_3, 100.0, "2026-07-22")
        self.assertEqual(mock_post.call_args[1]["json"]["markdown"]["content"], message_content_3)
        
        # Test with # 🔴
        mock_post.reset_mock()
        message_content_1 = "# 🔴 GCP 费用超标告警\n\n> 告警通知"
        send_webhook_alert(webhook_url, message_content_1, 100.0, "2026-07-22")
        self.assertEqual(mock_post.call_args[1]["json"]["markdown"]["content"], message_content_1)

    @patch('scheduler.requests.post')
    def test_send_webhook_alert_system_test(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        webhook_url = "http://mock-webhook"
        message_content = "🔔 这是一条系统测试通知"
        send_webhook_alert(webhook_url, message_content, 100.0, "2026-07-22")

        mock_post.assert_called_once()
        called_json = mock_post.call_args[1]["json"]
        expected_content = (
            f"# 🔴 GCP 费用超标告警\n\n"
            f"> 系统连接测试\n\n"
            f"**测试日期**\n"
            f"2026-07-22\n\n"
            f"**测试内容**\n"
            f"🔔 这是一条系统测试通知"
        )
        self.assertEqual(called_json["markdown"]["content"], expected_content)

    @patch('scheduler.requests.post')
    def test_send_webhook_alert_legacy_fallback_absolute(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        webhook_url = "http://mock-webhook"
        message_content = "Some legacy error alert message"
        send_webhook_alert(webhook_url, message_content, 150.5, "2026-07-22", is_relative=False)

        mock_post.assert_called_once()
        called_json = mock_post.call_args[1]["json"]
        expected_content = (
            f"# 🔴 GCP 费用超标告警\n\n"
            f"> 告警通知\n\n"
            f"**告警阈值**\n"
            f"🟠 $150.50\n\n"
            f"**告警日期**\n"
            f"2026-07-22\n\n"
            f"**详细内容**\n"
            f"Some legacy error alert message"
        )
        self.assertEqual(called_json["markdown"]["content"], expected_content)

    @patch('scheduler.requests.post')
    def test_send_webhook_alert_legacy_fallback_relative(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        webhook_url = "http://mock-webhook"
        message_content = "Some legacy relative alert message"
        send_webhook_alert(webhook_url, message_content, 0.55, "2026-07-22", is_relative=True)

        mock_post.assert_called_once()
        called_json = mock_post.call_args[1]["json"]
        expected_content = (
            f"# 🔴 GCP 费用超标告警\n\n"
            f"> 告警通知\n\n"
            f"**告警阈值**\n"
            f"🟠 55.0%\n\n"
            f"**告警日期**\n"
            f"2026-07-22\n\n"
            f"**详细内容**\n"
            f"Some legacy relative alert message"
        )
        self.assertEqual(called_json["markdown"]["content"], expected_content)

    @patch('scheduler.requests.post')
    def test_send_webhook_alert_no_url(self, mock_post):
        send_webhook_alert("", "Some message", 100.0, "2026-07-22")
        mock_post.assert_not_called()

class TestDeleteAlertConfigCascade(unittest.TestCase):
    def test_delete_alert_config_cascade_incidents(self):
        import crud
        mock_db = MagicMock()
        
        # Setup mock return values for get_alert_config
        mock_config = models.AlertConfig(id=4, alert_name="Test Delete Cascade")
        
        # We need mock_db.query to handle both AlertIncident and AlertConfig differently if needed,
        # but since we're using MagicMock we can mock the chain of calls
        mock_query_incident = MagicMock()
        mock_query_config = MagicMock()
        
        # Assign mock_db.query to return different query chain mocks depending on the argument
        def query_side_effect(model):
            if model == models.AlertIncident:
                return mock_query_incident
            elif model == models.AlertConfig:
                return mock_query_config
            return MagicMock()
        mock_db.query.side_effect = query_side_effect
        
        mock_query_config.filter.return_value.first.return_value = mock_config
        
        # Run deletion
        deleted_config = crud.delete_alert_config(mock_db, config_id=4)
        
        # Assertions
        # 1. Incident deletion chain was called
        mock_query_incident.filter.assert_called_once()
        mock_query_incident.filter.return_value.delete.assert_called_once()
        
        # 2. Config query filter was called
        mock_query_config.filter.assert_called_once()
        
        # 3. Config deletion was called with the matching config object
        mock_db.delete.assert_called_once_with(mock_config)
        mock_db.commit.assert_called_once()
        self.assertEqual(deleted_config, mock_config)

if __name__ == '__main__':
    unittest.main()
