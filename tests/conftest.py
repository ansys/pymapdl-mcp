# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: ANSYS MCP SERVER TECHNOLOGY PREVIEW LICENSE AGREEMENT

#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Pytest configuration and fixtures for PyMAPDL MCP Server tests."""

import sys
from unittest.mock import AsyncMock, MagicMock

from mcp.server.session import ServerSession
import pytest

from ansys.mapdl.mcp.server import PyMAPDLAppContext


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
    """Create an PyMAPDLAppContext with a mock MAPDL instance."""
    return PyMAPDLAppContext(mapdl=mock_mapdl)


@pytest.fixture
def app_context_no_mapdl():
    """Create an PyMAPDLAppContext without MAPDL (simulating connection failure)."""
    return PyMAPDLAppContext(mapdl=None)


@pytest.fixture
def mock_server_session():
    """Create a mock ServerSession for testing."""
    session = MagicMock(spec=ServerSession)
    return session


@pytest.fixture
def mock_context(mock_server_session, app_context):
    """Create a mock Context with PyMAPDLAppContext for testing tools."""
    context = MagicMock()
    context.request_context = MagicMock()
    context.request_context.lifespan_context = app_context
    context.enable_components = AsyncMock()
    context.disable_components = AsyncMock()
    return context


@pytest.fixture
def mock_context_no_mapdl(mock_server_session, app_context_no_mapdl):
    """Create a mock Context without MAPDL for testing error handling."""
    context = MagicMock()
    context.request_context = MagicMock()
    context.request_context.lifespan_context = app_context_no_mapdl
    context.enable_components = AsyncMock()
    context.disable_components = AsyncMock()
    return context


@pytest.fixture
def app_server():
    """Create a FastMCP server instance for testing."""
    from ansys.mapdl.mcp.server import app

    return app


@pytest.fixture(autouse=True)
def reset_stderr():
    """Ensure stderr is reset between tests."""
    original_stderr = sys.stderr
    yield
    sys.stderr = original_stderr
