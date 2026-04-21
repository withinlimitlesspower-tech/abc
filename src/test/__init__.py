"""
Test package initialization for Project.

This module initializes the test package and provides common test utilities
and configurations for the entire test suite.
"""

import sys
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

__version__ = "1.0.0"
__author__ = "Project Team"
__all__ = [
    "TestConfig",
    "TestBase",
    "setup_test_environment",
    "teardown_test_environment",
    "create_test_client",
    "assert_response_success",
    "assert_response_error",
]


class TestConfig:
    """Configuration class for test settings."""
    
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret-key-for-testing-only"
    DATABASE_URI = "sqlite:///:memory:"
    LOG_LEVEL = "ERROR"
    MAX_RETRIES = 3
    TIMEOUT = 5.0
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration values as a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary containing all configuration values.
        """
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }


class TestBase:
    """Base class for all test cases providing common functionality."""
    
    def __init__(self) -> None:
        """Initialize the test base class."""
        self.config = TestConfig()
        self._test_data: Dict[str, Any] = {}
    
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        try:
            self._setup_test_environment()
            self._initialize_test_data()
        except Exception as e:
            self.tearDown()
            raise RuntimeError(f"Failed to set up test: {str(e)}") from e
    
    def tearDown(self) -> None:
        """Clean up after each test method."""
        try:
            self._cleanup_test_data()
            self._teardown_test_environment()
        except Exception as e:
            print(f"Warning: Error during teardown: {str(e)}", file=sys.stderr)
    
    def _setup_test_environment(self) -> None:
        """Internal method to set up the test environment."""
        # This method should be overridden by subclasses
        pass
    
    def _teardown_test_environment(self) -> None:
        """Internal method to tear down the test environment."""
        # This method should be overridden by subclasses
        pass
    
    def _initialize_test_data(self) -> None:
        """Initialize test data for the test case."""
        self._test_data = {}
    
    def _cleanup_test_data(self) -> None:
        """Clean up test data after test execution."""
        self._test_data.clear()
    
    def assert_dict_contains(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> None:
        """Assert that actual dictionary contains all expected key-value pairs.
        
        Args:
            actual: The actual dictionary to check.
            expected: The expected key-value pairs that should be in actual.
            
        Raises:
            AssertionError: If actual doesn't contain all expected key-value pairs.
        """
        for key, value in expected.items():
            assert key in actual, f"Key '{key}' not found in actual dictionary"
            assert actual[key] == value, (
                f"Value mismatch for key '{key}': "
                f"expected {value}, got {actual[key]}"
            )


def setup_test_environment(config: Optional[TestConfig] = None) -> TestConfig:
    """Set up the global test environment.
    
    Args:
        config: Optional TestConfig instance. If None, uses default.
        
    Returns:
        TestConfig: The configuration used for setup.
        
    Raises:
        RuntimeError: If test environment setup fails.
    """
    try:
        if config is None:
            config = TestConfig()
        
        # Set environment variables for testing
        os.environ["TESTING"] = "True"
        os.environ["LOG_LEVEL"] = config.LOG_LEVEL
        
        print(f"Test environment setup complete with config: {config.get_config()}")
        return config
        
    except Exception as e:
        raise RuntimeError(f"Failed to setup test environment: {str(e)}") from e


def teardown_test_environment() -> None:
    """Clean up the global test environment.
    
    Raises:
        RuntimeError: If test environment teardown fails.
    """
    try:
        # Clean up environment variables
        if "TESTING" in os.environ:
            del os.environ["TESTING"]
        if "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]
        
        print("Test environment teardown complete")
        
    except Exception as e:
        raise RuntimeError(f"Failed to teardown test environment: {str(e)}") from e


def create_test_client() -> Any:
    """Create a test client for API testing.
    
    Returns:
        Any: A test client instance.
        
    Raises:
        ImportError: If required dependencies are not installed.
        RuntimeError: If test client creation fails.
    """
    try:
        # This is a placeholder - actual implementation depends on the web framework
        # For example, for Flask: return app.test_client()
        # For FastAPI: return TestClient(app)
        
        # For now, return a mock client
        class MockTestClient:
            def __init__(self):
                self.base_url = "http://testserver"
            
            def get(self, url: str, **kwargs) -> Dict[str, Any]:
                return {"status": "success", "url": url}
            
            def post(self, url: str, **kwargs) -> Dict[str, Any]:
                return {"status": "success", "url": url}
        
        return MockTestClient()
        
    except ImportError as e:
        raise ImportError(f"Required dependency not found: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to create test client: {str(e)}") from e


def assert_response_success(response: Dict[str, Any], expected_status: str = "success") -> None:
    """Assert that a response indicates success.
    
    Args:
        response: The response dictionary to check.
        expected_status: The expected status value.
        
    Raises:
        AssertionError: If response doesn't indicate success.
        ValueError: If response is not a dictionary.
    """
    if not isinstance(response, dict):
        raise ValueError(f"Response must be a dictionary, got {type(response)}")
    
    assert "status" in response, "Response missing 'status' field"
    assert response["status"] == expected_status, (
        f"Expected status '{expected_status}', got '{response['status']}'"
    )


def assert_response_error(response: Dict[str, Any], expected_error: Optional[str] = None) -> None:
    """Assert that a response indicates an error.
    
    Args:
        response: The response dictionary to check.
        expected_error: Optional specific error message to check for.
        
    Raises:
        AssertionError: If response doesn't indicate error or error doesn't match.
        ValueError: If response is not a dictionary.
    """
    if not isinstance(response, dict):
        raise ValueError(f"Response must be a dictionary, got {type(response)}")
    
    assert "status" in response, "Response missing 'status' field"
    assert response["status"] == "error", (
        f"Expected status 'error', got '{response['status']}'"
    )
    
    if expected_error is not None:
        assert "error" in response, "Response missing 'error' field"
        assert response["error"] == expected_error, (
            f"Expected error '{expected_error}', got '{response['error']}'"
        )