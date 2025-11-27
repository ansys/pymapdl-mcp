"""Pytest configuration and fixtures for PyMAPDL MCP tests."""

import pytest
from unittest.mock import Mock, MagicMock
from ansys.mapdl.mcp.context import PyMAPDLContext
from ansys.common.mcp.helpers import PersistentPythonSession


@pytest.fixture
def mock_python_session():
    """Create a mock PersistentPythonSession for testing."""
    session = Mock(spec=PersistentPythonSession)
    session.is_running.return_value = True
    session.execute.return_value = {
        "success": True,
        "stdout": "",
        "stderr": "",
    }
    return session


@pytest.fixture
def mock_context(mock_python_session):
    """Create a mock PyMAPDLContext for testing."""
    context = PyMAPDLContext(
        python_session=mock_python_session,
        command_history=[],
    )
    return context


@pytest.fixture
def mock_mapdl():
    """Create a mock MAPDL instance for testing."""
    mapdl = MagicMock()
    mapdl.ip = "localhost"
    mapdl.port = 50052
    mapdl.is_alive = True
    mapdl.__str__ = Mock(return_value="Mapdl\n-----\nPyMAPDL Version: 0.71.1\nMAPDL Version: 25.2")
    return mapdl


@pytest.fixture
def sample_command_history():
    """Provide sample command history for testing."""
    return [
        "mapdl.prep7()",
        "mapdl.et(1, 'SOLID186')",
        "mapdl.mp('EX', 1, 2e11)",
    ]


@pytest.fixture
def mock_get_context(mock_context):
    """Mock the get_context dependency injection."""
    def _get_context():
        # Create a mock that has the fastmcp._lifespan_result structure
        mock_ctx = Mock()
        mock_ctx.fastmcp._lifespan_result = mock_context
        return mock_ctx
    return _get_context


@pytest.fixture
def mock_subprocess_run(mocker):
    """Mock subprocess.run for testing CLI interactions."""
    return mocker.patch('subprocess.run')


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require MAPDL"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that require MAPDL connection"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take a long time to run"
    )
