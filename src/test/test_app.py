"""
Unit tests for the main application module.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from typing import Any, Dict

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.app import App, AppConfig, AppError


class TestAppConfig(unittest.TestCase):
    """Test cases for AppConfig class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.valid_config_data: Dict[str, Any] = {
            'host': 'localhost',
            'port': 8080,
            'debug': True,
            'max_connections': 100
        }
    
    def test_config_initialization_valid(self) -> None:
        """Test AppConfig initialization with valid data."""
        config = AppConfig(**self.valid_config_data)
        
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.port, 8080)
        self.assertTrue(config.debug)
        self.assertEqual(config.max_connections, 100)
    
    def test_config_initialization_invalid_port(self) -> None:
        """Test AppConfig initialization with invalid port."""
        invalid_data = self.valid_config_data.copy()
        invalid_data['port'] = -1
        
        with self.assertRaises(ValueError):
            AppConfig(**invalid_data)
    
    def test_config_initialization_missing_required_field(self) -> None:
        """Test AppConfig initialization with missing required field."""
        incomplete_data = self.valid_config_data.copy()
        del incomplete_data['host']
        
        with self.assertRaises(TypeError):
            AppConfig(**incomplete_data)
    
    def test_config_to_dict(self) -> None:
        """Test conversion of AppConfig to dictionary."""
        config = AppConfig(**self.valid_config_data)
        config_dict = config.to_dict()
        
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict['host'], 'localhost')
        self.assertEqual(config_dict['port'], 8080)


class TestApp(unittest.TestCase):
    """Test cases for App class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = AppConfig(
            host='localhost',
            port=8080,
            debug=True,
            max_connections=100
        )
        self.app = App(self.config)
    
    def test_app_initialization(self) -> None:
        """Test App initialization with configuration."""
        self.assertEqual(self.app.config.host, 'localhost')
        self.assertEqual(self.app.config.port, 8080)
        self.assertFalse(self.app.is_running)
    
    def test_app_initialization_invalid_config(self) -> None:
        """Test App initialization with invalid configuration."""
        with self.assertRaises(TypeError):
            App(None)  # type: ignore
    
    @patch('src.app.time.sleep')
    @patch('src.app.logging')
    def test_app_start_success(self, mock_logging: MagicMock, mock_sleep: MagicMock) -> None:
        """Test successful app start."""
        # Mock external dependencies
        mock_sleep.side_effect = None
        
        try:
            self.app.start()
            self.assertTrue(self.app.is_running)
        finally:
            # Clean up
            self.app.stop()
    
    @patch('src.app.time.sleep')
    def test_app_start_already_running(self, mock_sleep: MagicMock) -> None:
        """Test app start when already running."""
        self.app.is_running = True
        
        with self.assertRaises(AppError):
            self.app.start()
    
    @patch('src.app.logging')
    def test_app_stop_success(self, mock_logging: MagicMock) -> None:
        """Test successful app stop."""
        self.app.is_running = True
        self.app.stop()
        
        self.assertFalse(self.app.is_running)
    
    def test_app_stop_not_running(self) -> None:
        """Test app stop when not running."""
        # Should not raise an error when stopping an app that's not running
        self.app.stop()
        self.assertFalse(self.app.is_running)
    
    @patch('src.app.logging')
    def test_app_restart(self, mock_logging: MagicMock) -> None:
        """Test app restart functionality."""
        self.app.is_running = True
        
        with patch.object(self.app, 'stop') as mock_stop, \
             patch.object(self.app, 'start') as mock_start:
            self.app.restart()
            
            mock_stop.assert_called_once()
            mock_start.assert_called_once()
    
    def test_app_get_status(self) -> None:
        """Test app status retrieval."""
        status = self.app.get_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('running', status)
        self.assertIn('host', status)
        self.assertIn('port', status)
        self.assertEqual(status['running'], self.app.is_running)
    
    @patch('src.app.logging')
    def test_app_context_manager(self, mock_logging: MagicMock) -> None:
        """Test app as context manager."""
        with patch.object(self.app, 'start') as mock_start, \
             patch.object(self.app, 'stop') as mock_stop:
            with self.app:
                mock_start.assert_called_once()
            
            mock_stop.assert_called_once()
    
    def test_app_handle_request_valid(self) -> None:
        """Test handling valid request."""
        request_data = {'action': 'test', 'data': 'sample'}
        response = self.app.handle_request(request_data)
        
        self.assertIsInstance(response, dict)
        self.assertIn('status', response)
        self.assertIn('message', response)
        self.assertEqual(response['status'], 'success')
    
    def test_app_handle_request_invalid(self) -> None:
        """Test handling invalid request."""
        with self.assertRaises(ValueError):
            self.app.handle_request(None)  # type: ignore
    
    def test_app_handle_request_empty(self) -> None:
        """Test handling empty request."""
        response = self.app.handle_request({})
        
        self.assertEqual(response['status'], 'success')
        self.assertEqual(response['message'], 'Request processed')


class TestAppError(unittest.TestCase):
    """Test cases for AppError class."""
    
    def test_app_error_initialization(self) -> None:
        """Test AppError initialization."""
        error_message = "Test error message"
        error_code = 500
        
        app_error = AppError(error_message, error_code)
        
        self.assertEqual(str(app_error), error_message)
        self.assertEqual(app_error.error_code, error_code)
    
    def test_app_error_default_code(self) -> None:
        """Test AppError with default error code."""
        error_message = "Test error message"
        
        app_error = AppError(error_message)
        
        self.assertEqual(str(app_error), error_message)
        self.assertEqual(app_error.error_code, 400)  # Default error code


def run_tests() -> None:
    """Run all tests and display results."""
    try:
        # Create test suite
        test_suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
        
        # Run tests
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        
        # Exit with appropriate code
        sys.exit(0 if result.wasSuccessful() else 1)
        
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)


if __name__ == '__main__':
    run_tests()