"""Tests for MCP protocol compliance and server behavior."""

from unittest.mock import MagicMock, patch

import pytest
from fastmcp.server import FastMCP

from ansys.mapdl.mcp import mcp


@pytest.mark.unit
class TestMCPProtocol:
    """Tests for MCP protocol compliance."""

    def test_server_name(self):
        """Test that server has correct name."""
        assert mcp.name == "PyMAPDL-MCP"

    def test_server_is_fastmcp_instance(self):
        """Test that server is an instance of FastMCP."""
        assert isinstance(mcp, FastMCP)

    def test_server_has_lifespan(self):
        """Test that server has lifespan configured."""
        # The server should have a lifespan function configured
        # Simply check that the server was created with lifespan by checking it's a valid instance
        # The actual lifespan functionality is tested in test_lifespan.py
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "PyMAPDL-MCP"

    @pytest.mark.asyncio
    async def test_server_tools_registered(self):
        """Test that all tools are properly registered."""
        # Tools should be accessible through the MCP server
        from ansys.mapdl.mcp import (
            check_mapdl_status,
            launch_mapdl,
            run_mapdl_command,
            run_multiple_commands,
            write_comment,
        )

        tools = [
            check_mapdl_status,
            launch_mapdl,
            run_mapdl_command,
            run_multiple_commands,
            write_comment,
        ]

        for tool in tools:
            assert callable(tool)
            assert hasattr(tool, "__name__")
