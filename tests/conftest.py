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

import os
import sys
from unittest.mock import MagicMock

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
    return context


@pytest.fixture
def mock_context_no_mapdl(mock_server_session, app_context_no_mapdl):
    """Create a mock Context without MAPDL for testing error handling."""
    context = MagicMock()
    context.request_context = MagicMock()
    context.request_context.lifespan_context = app_context_no_mapdl
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


@pytest.fixture
def stateful_mock_mapdl():
    """Create a stateful mock MAPDL instance that tracks entity creation.

    This mock tracks the creation of geometric entities (keypoints, lines, etc.)
    through method calls, updating entity counts appropriately.
    """
    mapdl = MagicMock()
    mapdl.version = "2024 R2"

    # Track created entities
    mapdl._entities = {
        "keypoints": {},
        "lines": {},
        "areas": {},
        "volumes": {},
        "nodes": {},
        "elements": {},
    }

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

    # Create property-based getters for geometry that reflect current state
    mapdl.geometry = MagicMock()

    def get_n_keypoint():
        return len(mapdl._entities["keypoints"])

    def get_n_line():
        return len(mapdl._entities["lines"])

    def get_n_area():
        return len(mapdl._entities["areas"])

    def get_n_volu():
        return len(mapdl._entities["volumes"])

    type(mapdl.geometry).n_keypoint = property(lambda self: get_n_keypoint())
    type(mapdl.geometry).n_line = property(lambda self: get_n_line())
    type(mapdl.geometry).n_area = property(lambda self: get_n_area())
    type(mapdl.geometry).n_volu = property(lambda self: get_n_volu())

    # Mock Mesh class
    mapdl.mesh = MagicMock()

    def get_n_node():
        return len(mapdl._entities["nodes"])

    def get_n_elem():
        return len(mapdl._entities["elements"])

    type(mapdl.mesh).n_node = property(lambda self: get_n_node())
    type(mapdl.mesh).n_elem = property(lambda self: get_n_elem())

    # Mock Post_processing class
    mapdl.post_processing = MagicMock()
    mapdl.post_processing.nsets = 0

    # Create tracking functions for entity creation
    def track_keypoint(kp_id, *args, **kwargs):
        """Track keypoint creation."""
        mapdl._entities["keypoints"][kp_id] = {"id": kp_id, "coords": args[:3] if args else ()}
        return ""

    def track_line(l_id, *args, **kwargs):
        """Track line creation."""
        mapdl._entities["lines"][l_id] = {"id": l_id}
        return ""

    def track_area(a_id, *args, **kwargs):
        """Track area creation."""
        mapdl._entities["areas"][a_id] = {"id": a_id}
        return ""

    def track_volume(v_id, *args, **kwargs):
        """Track volume creation."""
        mapdl._entities["volumes"][v_id] = {"id": v_id}
        return ""

    # Attach tracking methods to corresponding MAPDL methods
    mapdl.k = MagicMock(side_effect=track_keypoint)
    mapdl.l = MagicMock(side_effect=track_line)
    mapdl.a = MagicMock(side_effect=track_area)
    mapdl.v = MagicMock(side_effect=track_volume)

    # Mock other common methods
    mapdl.prep7 = MagicMock(return_value="")
    mapdl.solu = MagicMock(return_value="")
    mapdl.post1 = MagicMock(return_value="")
    mapdl.post26 = MagicMock(return_value="")
    mapdl.et = MagicMock(return_value="")
    mapdl.mp = MagicMock(return_value="")
    mapdl.esize = MagicMock(return_value="")
    mapdl.eplot = MagicMock(return_value="")
    mapdl.meshing = MagicMock()
    mapdl.meshing.mesh = MagicMock(return_value="")
    mapdl.mesh.esize = MagicMock(return_value="")
    mapdl.com = MagicMock(return_value="")
    mapdl.run = MagicMock(return_value="")
    mapdl.exit = MagicMock(return_value="")
    mapdl.clear = MagicMock(return_value="")

    return mapdl


@pytest.fixture
def azure_openai_client():
    """Create Azure OpenAI client or skip if credentials not available.

    The client requires the following environment variables:
    - AZURE_OPENAI_KEY: API key for Azure OpenAI
    - AZURE_OPENAI_ENDPOINT: Endpoint URL for Azure OpenAI
    - AZURE_OPENAI_DEPLOYMENT: Deployment name for the model

    Returns
    -------
    openai.AzureOpenAI or None
        The Azure OpenAI client, or None if credentials are not available.
    """
    key = os.getenv("AZURE_OPENAI_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    if not all([key, endpoint, deployment]):
        pytest.skip(
            "Azure OpenAI credentials not configured. "
            "Set AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT."
        )

    try:
        from openai import AzureOpenAI
    except ImportError:
        pytest.skip("openai library not installed. Install with: pip install openai")

    try:
        client = AzureOpenAI(
            api_key=key,
            api_version="2024-02-15-preview",
            azure_endpoint=endpoint,
        )
        return client
    except Exception as e:
        pytest.skip(f"Could not initialize Azure OpenAI client: {e}")
