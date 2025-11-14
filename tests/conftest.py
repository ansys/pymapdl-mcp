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
    mapdl.directory = "/tmp"
    mapdl.parameters = {}

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
