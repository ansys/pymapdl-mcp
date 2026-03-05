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
    from ansys.mapdl.mcp.tools import check_mapdl_status, run_mapdl_command, write_comment

    assert callable(check_mapdl_status)
    assert callable(run_mapdl_command)
    assert callable(write_comment)
