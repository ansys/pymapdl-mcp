"""Pytest configuration and fixtures for PyMAPDL MCP Server tests."""

import sys
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, MagicMock


class MockMapdl(MagicMock):
    """MagicMock subclass that exposes exited/exiting properties backed by
    the private _exited/_exiting attributes so tests can set either form.

    This ensures accessing `.exited` or `._exited` remains consistent.
    """

    @property
    def exited(self) -> bool:  # type: ignore[misc]
        return bool(getattr(self, "_exited", False))

    @exited.setter
    def exited(self, val: Any) -> None:  # type: ignore[misc]
        object.__setattr__(self, "_exited", bool(val))

    @property
    def exiting(self) -> bool:  # type: ignore[misc]
        return bool(getattr(self, "_exiting", False))

    @exiting.setter
    def exiting(self, val: Any) -> None:  # type: ignore[misc]
        object.__setattr__(self, "_exiting", bool(val))


import pytest
from mcp.server.session import ServerSession

from ansys.mapdl.mcp.mcp import AppContext


@pytest.fixture
def mock_mapdl():
    """Create a mock MAPDL instance for testing."""
    mapdl = MockMapdl()
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
    # Provide explicit boolean flags used by the code under test
    mapdl.exited = False
    mapdl.exiting = False
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
def mock_pool(mock_mapdl):
    """Create a mock MapdlPool instance."""
    pool = MagicMock()
    pool._instances = [mock_mapdl]
    pool._n_instances = 1
    pool._ips = ["127.0.0.1"]
    pool._ports = [50052]
    pool.__len__ = MagicMock(return_value=1)
    pool.__getitem__ = MagicMock(return_value=mock_mapdl)
    pool.exit = MagicMock()
    return pool


def create_mock_pool_with_mapdl():
    """Helper function to create a mock pool with MAPDL instance for patching."""
    mock_mapdl = MockMapdl()
    mock_mapdl.version = "2024 R2"
    mock_mapdl.ip = "127.0.0.1"
    mock_mapdl.port = 50052
    mock_mapdl.directory = "/tmp/ansys_mapdl"
    mock_mapdl._exited = False
    mock_mapdl._exiting = False
    # Provide explicit boolean flags used by the code under test
    mock_mapdl.exited = False
    mock_mapdl.exiting = False
    mock_mapdl.com = MagicMock(return_value="Comment written")
    mock_mapdl.run = MagicMock(return_value="Command executed")
    mock_mapdl.exit = MagicMock()

    mock_pool = MagicMock()
    mock_pool._instances = [mock_mapdl]
    mock_pool._n_instances = 1
    mock_pool._ips = ["127.0.0.1"]
    mock_pool._ports = [50052]
    mock_pool.__getitem__ = MagicMock(return_value=mock_mapdl)
    mock_pool.__len__ = MagicMock(return_value=1)
    mock_pool.exit = MagicMock()

    return mock_pool


@pytest.fixture
def app_context(mock_pool):
    """Create an AppContext with a mock MAPDL instance in a pool."""
    ctx = AppContext()
    ctx.pool = mock_pool
    return ctx


@pytest.fixture
def app_context_no_mapdl():
    """Create an AppContext without MAPDL (simulating connection failure)."""
    return AppContext()


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
