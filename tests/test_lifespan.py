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

"""Tests for MCP server lifespan management."""

from unittest.mock import MagicMock

import pytest

from ansys.mapdl.mcp.server import PyMAPDLAppContext, app


@pytest.mark.unit
def test_app_context_dataclass():
    """Test that PyMAPDLAppContext is properly defined as a dataclass."""
    from dataclasses import is_dataclass

    assert is_dataclass(PyMAPDLAppContext)

    # Test creating PyMAPDLAppContext with MAPDL
    mock_mapdl = MagicMock()
    ctx = PyMAPDLAppContext(mapdl=mock_mapdl)
    assert ctx.mapdl == mock_mapdl

    # Test creating PyMAPDLAppContext without MAPDL
    ctx_none = PyMAPDLAppContext(mapdl=None)
    assert ctx_none.mapdl is None


@pytest.mark.unit
def test_mcp_server_initialization():
    """Test that MCP server is properly initialized."""
    assert app is not None
    assert app.name == "PyMAPDL MCP Server"


@pytest.mark.unit
def test_mcp_server_has_tools():
    """Test that MCP server has registered tools."""
    # The mcp server should have tools registered
    # This is a basic check to ensure tools are defined
    from ansys.mapdl.mcp.tools import (
        check_mapdl_status,
        run_mapdl_command,
        write_comment,
    )

    assert callable(check_mapdl_status)
    assert callable(run_mapdl_command)
    assert callable(write_comment)
