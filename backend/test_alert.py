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

if __name__ == '__main__':
    unittest.main()
