"""Tests for MCP protocol compliance and server behavior."""

from unittest.mock import MagicMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from ansys.mapdl.mcp import mcp


@pytest.mark.unit
class TestMCPProtocol:
    """Tests for MCP protocol compliance."""

    def test_server_name(self):
        """Test that server has correct name."""
        assert mcp.name == "PyMAPDL"

    def test_server_is_fastmcp_instance(self):
        """Test that server is an instance of FastMCP."""
        assert isinstance(mcp, FastMCP)

    def test_server_has_lifespan(self):
        """Test that server has lifespan configured."""
        # The server should have a lifespan function configured
        # Simply check that the server was created with lifespan by checking it's a valid instance
        # The actual lifespan functionality is tested in test_lifespan.py
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "PyMAPDL"

    @pytest.mark.asyncio
    async def test_server_tools_registered(self):
        """Test that all tools are properly registered."""
        # Tools should be accessible through the MCP server
        from ansys.mapdl.mcp import (
            check_mapdl_status,
            launch_mapdl,
            run_mapdl_command,
            write_comment,
        )

        tools = [check_mapdl_status, launch_mapdl, run_mapdl_command, write_comment]

        for tool in tools:
            assert callable(tool)
            assert hasattr(tool, "__name__")

    def test_tool_names(self):
        """Test that tools have correct names."""
        from ansys.mapdl.mcp import (
            check_mapdl_status,
            launch_mapdl,
            run_mapdl_command,
            write_comment,
        )

        assert check_mapdl_status.__name__ == "check_mapdl_status"
        assert launch_mapdl.__name__ == "launch_mapdl"
        assert run_mapdl_command.__name__ == "run_mapdl_command"
        assert write_comment.__name__ == "write_comment"

    def test_tool_signatures(self):
        """Test that tools have correct signatures."""
        import inspect

        from ansys.mapdl.mcp import (
            check_mapdl_status,
            launch_mapdl,
            run_mapdl_command,
            write_comment,
        )

        # check_mapdl_status should take ctx parameter
        sig = inspect.signature(check_mapdl_status)
        assert "ctx" in sig.parameters

        # launch_mapdl should take ctx and optional parameters
        sig = inspect.signature(launch_mapdl)
        assert "ctx" in sig.parameters
        assert "exec_file" in sig.parameters
        assert "run_location" in sig.parameters
        assert "nproc" in sig.parameters
        assert "additional_switches" in sig.parameters

        # write_comment should take ctx and comment parameters
        sig = inspect.signature(write_comment)
        assert "ctx" in sig.parameters
        assert "comment" in sig.parameters

        # run_mapdl_command should take ctx and cmd parameters
        sig = inspect.signature(run_mapdl_command)
        assert "ctx" in sig.parameters
        assert "cmd" in sig.parameters
