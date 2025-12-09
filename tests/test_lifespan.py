"""Tests for MCP server lifespan management."""

from unittest.mock import MagicMock

import pytest

from ansys.mapdl.mcp.server import AppContext, app


@pytest.mark.unit
def test_app_context_dataclass():
    """Test that AppContext is properly defined as a dataclass."""
    from dataclasses import is_dataclass

    assert is_dataclass(AppContext)

    # Test creating AppContext with MAPDL
    mock_mapdl = MagicMock()
    ctx = AppContext(mapdl=mock_mapdl)
    assert ctx.mapdl == mock_mapdl

    # Test creating AppContext without MAPDL
    ctx_none = AppContext(mapdl=None)
    assert ctx_none.mapdl is None


@pytest.mark.unit
def test_mcp_server_initialization():
    """Test that MCP server is properly initialized."""
    assert app is not None
    assert app.name == "PyMAPDL-MCP"


@pytest.mark.unit
def test_mcp_server_has_tools():
    """Test that MCP server has registered tools."""
    # The mcp server should have tools registered
    # This is a basic check to ensure tools are defined
    from ansys.mapdl.mcp import check_mapdl_status, run_mapdl_command, write_comment

    # Verify tools are FunctionTool objects with callable .fn attribute
    assert hasattr(check_mapdl_status, "fn") and callable(check_mapdl_status.fn)
    assert hasattr(run_mapdl_command, "fn") and callable(run_mapdl_command.fn)
    assert hasattr(write_comment, "fn") and callable(write_comment.fn)
