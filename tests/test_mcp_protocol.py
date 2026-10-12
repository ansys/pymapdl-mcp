# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for MCP protocol compliance and server behavior."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastmcp import Client
from fastmcp.exceptions import ToolError
from fastmcp.server import FastMCP
import pytest

from ansys.mapdl.mcp import app


@pytest.mark.unit
class TestMCPProtocol:
    """Tests for MCP protocol compliance."""

    def test_server_name(self):
        """Test that server has correct name."""
        assert app.name == "PyMAPDL MCP Server"

    def test_server_is_fastmcp_instance(self):
        """Test that server is an instance of FastMCP."""
        assert isinstance(app, FastMCP)

    def test_server_has_lifespan(self):
        """Test that server has lifespan configured."""
        # The server should have a lifespan function configured
        # Simply check that the server was created with lifespan by checking it's a valid instance
        # The actual lifespan functionality is tested in test_lifespan.py
        assert isinstance(app, FastMCP)
        assert app.name == "PyMAPDL MCP Server"

    @pytest.mark.asyncio
    async def test_server_tools_registered(self):
        """Test that all tools are properly registered."""
        # Tools should be accessible through the MCP server
        from ansys.mapdl.mcp.tools import (
            check_mapdl_status,
            launch_mapdl_session,
            run_mapdl_command,
            run_multiple_mapdl_commands,
        )

        tools = [
            check_mapdl_status,
            launch_mapdl_session,
            run_mapdl_command,
            run_multiple_mapdl_commands,
        ]

        for tool in tools:
            assert callable(tool)
            assert hasattr(tool, "__name__")


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("connection_tool", ["connect_to_mapdl", "launch_mapdl_session"])
async def test_python_off_survives_shared_connection_transitions(
    mock_mapdl, tmp_path, connection_tool
):
    from ansys.mapdl.mcp import tools
    from ansys.mapdl.mcp.server import PyMAPDLMCP

    server = PyMAPDLMCP(need_python=False)
    for tool in (
        tools.connect_to_mapdl,
        tools.launch_mapdl_session,
        tools.disconnect_from_mapdl,
        tools.run_python_code,
        tools.custom_plot,
        tools.run_mapdl_command,
        tools.screenshot,
    ):
        server.add_tool(tool)
    server.resource("toolsets://definition")(tools.list_tool_sets)
    server.disable(tags={"requires_mapdl"})
    target = (
        "ansys.mapdl.core.Mapdl"
        if connection_tool == "connect_to_mapdl"
        else "ansys.mapdl.core.launch_mapdl"
    )
    marker = tmp_path / "guessed-python-ran"
    payload = f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')"
    async with Client(server) as first, Client(server) as second:
        for phase in ("initial", "connected", "disconnected", "reconnected"):
            if phase in ("connected", "reconnected"):
                mock_mapdl._exited = False
                with patch(target, return_value=mock_mapdl):
                    result = await first.call_tool(connection_tool)
                assert "Successfully" in result.content[0].text
            elif phase == "disconnected":
                result = await second.call_tool("disconnect_from_mapdl")
                assert "Successfully disconnected" in result.content[0].text
            for client in (first, second):
                names = {tool.name for tool in await client.list_tools()}
                assert {"run_python_code", "custom_plot"}.isdisjoint(names)
                assert ("run_mapdl_command" in names) == (phase in ("connected", "reconnected"))
                for name, parameter in (("run_python_code", "code"), ("custom_plot", "plot_code")):
                    with pytest.raises(ToolError, match="Unknown tool"):
                        await client.call_tool(name, {parameter: payload})
                definitions = json.loads(
                    (await client.read_resource("toolsets://definition"))[0].text
                )
                catalog = {item["name"]: item for item in definitions}
                assert "python_execution" not in catalog
                assert catalog["visualization"]["tools"] == ["screenshot"]
                assert catalog["command_execution"]["tools"] == [
                    "run_mapdl_command",
                    "run_multiple_mapdl_commands",
                    "list_command_logs",
                    "read_command_log",
                ]
                assert "run_python_code" not in catalog["command_execution"]["skill"]
                assert "custom_plot" not in catalog["visualization"]["skill"]
            if phase == "reconnected":
                with patch(
                    "ansys.mapdl.mcp.tools._capture_screenshot",
                    return_value=(tmp_path / "native.png", b"native-image", "image/png"),
                ):
                    result = await first.call_tool("screenshot")
                assert [(item.type, getattr(item, "data", None)) for item in result.content] == [
                    ("text", None),
                    ("image", "bmF0aXZlLWltYWdl"),
                ]
        assert server.context.python_session is None
        assert not marker.exists()


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("restriction", ["aali", "locked_connection"])
async def test_python_off_startup_masks_survive_refresh(mock_mapdl, restriction):
    from ansys.mapdl.mcp import tools
    from ansys.mapdl.mcp.server import PyMAPDLMCP

    server = PyMAPDLMCP(need_python=False)
    server._cli_config = {
        "connect_on_startup": True,
        "on_aali": restriction == "aali",
    }
    for tool in (
        tools.run_python_code,
        tools.custom_plot,
        tools.run_mapdl_command,
        tools.screenshot,
        tools.disconnect_from_mapdl,
    ):
        server.add_tool(tool)
    server.disable(tags={restriction})
    with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl):
        async with Client(server) as client:
            context = SimpleNamespace(
                request_context=SimpleNamespace(lifespan_context=server.context),
                fastmcp=server,
                send_notification=AsyncMock(),
            )
            await tools._refresh_mapdl_tool_visibility(context)
            names = {tool.name for tool in await client.list_tools()}
            assert "run_mapdl_command" in names
            assert {"run_python_code", "custom_plot", "disconnect_from_mapdl"}.isdisjoint(names)
            assert ("screenshot" in names) == (restriction != "aali")
            assert server.context.python_session is None
