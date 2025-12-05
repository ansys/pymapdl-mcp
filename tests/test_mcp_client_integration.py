"""MCP Client-Server Integration Tests.

These tests verify that tools work correctly when invoked through the actual
MCP protocol, simulating how real users (Claude, VS Code, etc.) interact with
the server. This catches issues that unit tests miss, such as:

- JSON serialization/deserialization of parameters
- Type coercion and validation at the protocol level
- Async context handling
- Real parameter passing from MCP clients
- Tool discovery and invocation mechanics

Run with: pytest tests/test_mcp_client_integration.py -v
"""

import os

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport

from ansys.mapdl.mcp import mcp

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
async def main_mcp_client():
    async with Client(transport=mcp) as mcp_client:
        yield mcp_client


async def test_list_tools(main_mcp_client: Client[FastMCPTransport]):
    list_tools = await main_mcp_client.list_tools()

    assert len(list_tools) == 23


@pytest.mark.integration
@pytest.mark.slow
class TestMapdlIntegration:
    """Integration tests that require a real MAPDL connection."""

    @pytest.fixture(scope="class")
    def real_mapdl(self):
        """
        Fixture to connect to a real MAPDL instance.

        This requires MAPDL to be running on localhost:50052.
        Skip these tests if MAPDL is not available.
        """
        try:
            from ansys.mapdl.core import launch_mapdl

            mapdl = launch_mapdl(cleanup_on_exit=False, loglevel="ERROR")

            yield mapdl

            # Cleanup after tests
            # Don't exit since MAPDL is running externally
            mapdl.exit()

        except Exception as e:
            # Not allow to skip if running on CICD
            if os.getenv("ON_CI", False):
                raise e
            else:
                pytest.skip(f"MAPDL not available: {e}")

    @pytest.fixture(scope="class")
    def mapdl(self, real_mapdl):
        real_mapdl.clear()
        return real_mapdl

    @pytest.fixture()
    async def mcp_client(self):
        async with Client(transport=mcp) as mcp_client:
            yield mcp_client

    @pytest.fixture()
    async def connected_client(self, mcp_client, mapdl):
        """Fixture to provide a connected MCP client."""
        await mcp_client.call_tool(
            "connect_to_mapdl", arguments={"port": mapdl.port, "ip": "localhost"}
        )

        yield mcp_client

        await mcp_client.call_tool("disconnect_from_mapdl")

    @pytest.mark.asyncio
    async def test_run_multiple_commands_via_protocol(self, connected_client):
        # Now test running multiple commands
        result = await connected_client.call_tool(
            "run_multiple_commands",
            arguments={"commands": ["/PREP7", "ET,1,SOLID185", "MP,EX,1,200E9"]},
        )

        text = result.content[0].text
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_check_mapdl_status(self, connected_client):
        """Test check_mapdl_status tool via MCP protocol."""
        result = await connected_client.call_tool("check_mapdl_status")

        text = result.content[0].text
        assert isinstance(text, str)
        # Should return JSON with status information
        import json

        status = json.loads(text)
        assert "connection" in status
        assert "information" in status

    @pytest.mark.asyncio
    async def test_check_mapdl_installed(self, mcp_client):
        """Test check_mapdl_installed tool via MCP protocol."""
        result = await mcp_client.call_tool("check_mapdl_installed")

        text = result.content[0].text
        assert isinstance(text, str)
        assert "MAPDL" in text

    @pytest.mark.asyncio
    async def test_write_comment(self, connected_client):
        """Test write_comment tool via MCP protocol."""
        result = await connected_client.call_tool(
            "write_comment", arguments={"comment": "Test comment via MCP"}
        )

        text = result.content[0].text
        assert isinstance(text, str)
        assert "comment" in text.lower()

    @pytest.mark.asyncio
    async def test_run_mapdl_command(self, connected_client):
        """Test run_mapdl_command tool via MCP protocol."""
        result = await connected_client.call_tool("run_mapdl_command", arguments={"cmd": "/PREP7"})

        text = result.content[0].text
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_list_mapdl_instances(self, mcp_client):
        """Test list_mapdl_instances tool via MCP protocol."""
        result = await mcp_client.call_tool("list_mapdl_instances")

        text = result.content[0].text
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_list_pool_instances(self, connected_client):
        """Test list_pool_instances tool via MCP protocol."""
        result = await connected_client.call_tool("list_pool_instances")

        text = result.content[0].text
        assert isinstance(text, str)
        # Should show at least one instance (the connected one)
        assert "instance" in text.lower()

    @pytest.mark.asyncio
    async def test_set_default_instance(self, connected_client):
        """Test set_default_instance tool via MCP protocol."""
        result = await connected_client.call_tool("set_default_instance", arguments={"instance": 0})

        text = result.content[0].text
        assert isinstance(text, str)
        assert "default" in text.lower()

    @pytest.mark.asyncio
    async def test_assign_nickname(self, connected_client):
        """Test assign_nickname tool via MCP protocol."""
        result = await connected_client.call_tool(
            "assign_nickname", arguments={"instance": 0, "nickname": "test_instance"}
        )

        text = result.content[0].text
        assert isinstance(text, str)
        assert "nickname" in text.lower() or "test_instance" in text

    @pytest.mark.asyncio
    async def test_remove_nickname(self, connected_client):
        """Test remove_nickname tool via MCP protocol."""
        # First assign a nickname
        await connected_client.call_tool(
            "assign_nickname", arguments={"instance": 0, "nickname": "temp_nickname"}
        )

        # Then remove it
        result = await connected_client.call_tool(
            "remove_nickname", arguments={"nickname": "temp_nickname"}
        )

        text = result.content[0].text
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_screenshot(self, connected_client, mapdl):
        """Test screenshot tool via MCP protocol."""
        # Set up a simple geometry to visualize
        mapdl.clear()
        mapdl.prep7()
        mapdl.block(0, 1, 0, 1, 0, 1)

        result = await connected_client.call_tool("screenshot")

        # Screenshot returns both text and image content
        assert len(result.content) >= 1
        text = result.content[0].text
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_connect_disconnect_workflow(self, mcp_client, mapdl):
        """Test connect and disconnect workflow via MCP protocol."""
        # Connect
        connect_result = await mcp_client.call_tool(
            "connect_to_mapdl", arguments={"port": mapdl.port, "ip": "localhost"}
        )
        text = connect_result.content[0].text
        assert isinstance(text, str)
        assert "success" in text.lower()

        # Disconnect
        disconnect_result = await mcp_client.call_tool("disconnect_from_mapdl")
        text = disconnect_result.content[0].text
        assert isinstance(text, str)


@pytest.mark.integration
class TestContextTools:
    """Test context/documentation tools via MCP protocol."""

    @pytest.fixture()
    async def mcp_client(self):
        async with Client(transport=mcp) as mcp_client:
            yield mcp_client

    @pytest.mark.asyncio
    async def test_get_context_for_workflow_overview(self, mcp_client):
        """Test get_context_for_workflow_overview tool."""
        result = await mcp_client.call_tool("get_context_for_workflow_overview")

        text = result.content[0].text
        assert isinstance(text, str)
        assert "workflow" in text.lower()
        assert len(text) > 100  # Should be substantial documentation

    @pytest.mark.asyncio
    async def test_get_context_for_preprocessing_geometry(self, mcp_client):
        """Test get_context_for_preprocessing_geometry tool."""
        result = await mcp_client.call_tool("get_context_for_preprocessing_geometry")

        text = result.content[0].text
        assert isinstance(text, str)
        assert "geometry" in text.lower()

    @pytest.mark.asyncio
    async def test_get_context_for_preprocessing_elements(self, mcp_client):
        """Test get_context_for_preprocessing_elements tool."""
        result = await mcp_client.call_tool("get_context_for_preprocessing_elements")

        text = result.content[0].text
        assert isinstance(text, str)
        assert "element" in text.lower()

    @pytest.mark.asyncio
    async def test_get_context_for_preprocessing_materials(self, mcp_client):
        """Test get_context_for_preprocessing_materials tool."""
        result = await mcp_client.call_tool("get_context_for_preprocessing_materials")

        text = result.content[0].text
        assert isinstance(text, str)
        assert "material" in text.lower()

    @pytest.mark.asyncio
    async def test_get_context_for_preprocessing_mesh(self, mcp_client):
        """Test get_context_for_preprocessing_mesh tool."""
        result = await mcp_client.call_tool("get_context_for_preprocessing_mesh")

        text = result.content[0].text
        assert isinstance(text, str)
        assert "mesh" in text.lower()

    @pytest.mark.asyncio
    async def test_get_context_for_preprocessing_boundary_conditions(self, mcp_client):
        """Test get_context_for_preprocessing_boundary_conditions tool."""
        result = await mcp_client.call_tool("get_context_for_preprocessing_boundary_conditions")

        text = result.content[0].text
        assert isinstance(text, str)
        assert "boundary" in text.lower() or "constraint" in text.lower()

    @pytest.mark.asyncio
    async def test_get_context_for_solution_phase(self, mcp_client):
        """Test get_context_for_solution_phase tool."""
        result = await mcp_client.call_tool("get_context_for_solution_phase")

        text = result.content[0].text
        assert isinstance(text, str)
        assert "solution" in text.lower() or "solve" in text.lower()

    @pytest.mark.asyncio
    async def test_get_context_for_postprocessing_phase(self, mcp_client):
        """Test get_context_for_postprocessing_phase tool."""
        result = await mcp_client.call_tool("get_context_for_postprocessing_phase")

        text = result.content[0].text
        assert isinstance(text, str)
        assert "post" in text.lower() or "result" in text.lower()

    @pytest.mark.asyncio
    async def test_get_context_for_general_rules(self, mcp_client):
        """Test get_context_for_general_rules tool."""
        result = await mcp_client.call_tool("get_context_for_general_rules")

        text = result.content[0].text
        assert isinstance(text, str)
        assert len(text) > 50  # Should contain useful guidance
