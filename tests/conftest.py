"""Pytest configuration and fixtures for PyMAPDL MCP Server tests."""

import sys
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.server.session import ServerSession

from ansys.mapdl.mcp.mcp import AppContext


@pytest.fixture
def mock_mapdl():
    """Create a mock MAPDL instance for testing."""
    mapdl = MagicMock()
    mapdl.version = "2024 R2"
    mapdl.com = MagicMock(return_value="Comment written")
    mapdl.run = MagicMock(return_value="Command executed")
    mapdl.exit = MagicMock()

    # Mock common MAPDL attributes
    mapdl.jobname = "file"
    mapdl.name = "MAPDL instance 0"
    mapdl.check_status = "RUNNING"
    mapdl.directory = "/tmp"
    mapdl.parameters = {}
    mapdl.is_alive = True
    mapdl.is_local = True
    mapdl.port = 50052
    mapdl.ip = "127.0.0.1"
    mapdl._exited = False
    mapdl._exiting = False
    mapdl.platform = "linux"

    # Mock Information class
    mapdl.information = MagicMock()
    mapdl.information.title = "Test Analysis"
    mapdl.information.jobname = "file"
    mapdl.information.routine = "PREP7"
    mapdl.information.units = "SI"
    mapdl.information.revision = "2024 R2"
    mapdl.information.product = "ANSYS Mechanical Enterprise"

    # Mock Geometry class
    mapdl.geometry = MagicMock()
    mapdl.geometry.n_keypoint = 0
    mapdl.geometry.n_line = 0
    mapdl.geometry.n_area = 0
    mapdl.geometry.n_volu = 0

    # Mock Post_processing class
    mapdl.post_processing = MagicMock()
    mapdl.post_processing.nsets = 0

    # Mock Mesh class
    mapdl.mesh = MagicMock()
    mapdl.mesh.n_node = 0
    mapdl.mesh.n_elem = 0

    return mapdl


@pytest.fixture
def app_context(mock_mapdl):
    """Create an AppContext with a mock MAPDL instance."""
    return AppContext(mapdl=mock_mapdl)


@pytest.fixture
def app_context_no_mapdl():
    """Create an AppContext without MAPDL (simulating connection failure)."""
    return AppContext(mapdl=None)


@pytest.fixture
def mock_server_session():
    """Create a mock ServerSession for testing."""
    session = MagicMock(spec=ServerSession)
    return session


@pytest.fixture
def mock_context(mock_server_session, app_context):
    """Create a mock Context with AppContext for testing tools."""
    context = MagicMock()
    context.request_context = MagicMock()
    context.request_context.lifespan_context = app_context
    return context


@pytest.fixture
def mock_context_no_mapdl(mock_server_session, app_context_no_mapdl):
    """Create a mock Context without MAPDL for testing error handling."""
    context = MagicMock()
    context.request_context = MagicMock()
    context.request_context.lifespan_context = app_context_no_mapdl
    return context


@pytest.fixture
def mcp_server():
    """Create a FastMCP server instance for testing."""
    from ansys.mapdl.mcp.mcp import mcp

    return mcp


@pytest.fixture(autouse=True)
def reset_stderr():
    """Ensure stderr is reset between tests."""
    original_stderr = sys.stderr
    yield
    sys.stderr = original_stderr
