"""Tests for MCP server lifespan management."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ansys.mapdl.mcp.mpc import AppContext, app_lifespan, mcp


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
    assert mcp is not None
    assert mcp.name == "PyMAPDL"


@pytest.mark.unit
def test_mcp_server_has_tools():
    """Test that MCP server has registered tools."""
    # The mcp server should have tools registered
    # This is a basic check to ensure tools are defined
    from ansys.mapdl.mcp import check_mapdl_status, run_mapdl_command, write_comment

    # Verify tools are callable
    assert callable(check_mapdl_status)
    assert callable(run_mapdl_command)
    assert callable(write_comment)
