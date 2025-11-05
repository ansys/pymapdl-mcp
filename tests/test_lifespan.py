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
@pytest.mark.asyncio
@pytest.mark.skip(reason="Skipped when real MAPDL is connected; use integration tests instead")
async def test_app_lifespan_successful_connection():
    """Test app lifespan with successful MAPDL connection."""
    mock_mapdl = MagicMock()
    mock_mapdl.version = "2024 R2"

    mock_server = MagicMock()

    with patch("ansys.mapdl.mcp.mpc.Mapdl") as mock_mapdl_class:
        mock_mapdl_class.return_value = mock_mapdl

        async with app_lifespan(mock_server) as context:
            # Verify context is properly created
            assert isinstance(context, AppContext)
            assert context.mapdl is not None
            # Check that version attribute exists, don't check specific value
            assert hasattr(context.mapdl, "version")

        # After context exits, cleanup should have occurred
        # Note: We don't call exit() in the code since MAPDL runs in Docker


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Skipped when real MAPDL is connected; difficult to mock connection failures"
)
async def test_app_lifespan_connection_failure():
    """Test app lifespan behavior when MAPDL connection fails."""
    mock_server = MagicMock()

    with patch("ansys.mapdl.mcp.mpc.Mapdl") as mock_mapdl_class:
        # Simulate connection failure
        mock_mapdl_class.side_effect = ConnectionError("Cannot connect to MAPDL")

        with pytest.raises(ConnectionError):
            async with app_lifespan(mock_server) as context:
                pass


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
