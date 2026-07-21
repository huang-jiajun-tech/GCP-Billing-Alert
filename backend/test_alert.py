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
from scheduler import check_billing_and_alert

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
        self.assertIn("Main Billing", args[1]) # 账单名称
        self.assertIn("proj-a", args[1]) # Top 1
        self.assertIn("proj-b", args[1]) # Top 2
        self.assertIn("proj-c", args[1]) # Top 3
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
        self.assertIn("Main Billing", args[1]) # 账单名称
        self.assertIn("proj-a", args[1]) # Top 1
        self.assertIn("proj-b", args[1]) # Top 2
        # 验证涨幅数据在格式化内容中 (60.00%)
        self.assertIn("+60.00%", args[1])

if __name__ == '__main__':
    unittest.main()
