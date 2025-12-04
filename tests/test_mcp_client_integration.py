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
    async def test_run_multiple_commands_via_protocol(self, mapdl, connected_client):
        # Now test running multiple commands
        result = await connected_client.call_tool(
            "run_multiple_commands",
            arguments={"commands": ["/PREP7", "ET,1,SOLID185", "MP,EX,1,200E9"]},
        )

        text = result.content[0].text
        assert isinstance(text, str)
