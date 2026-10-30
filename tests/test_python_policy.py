# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
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

"""Tests for disabling Python execution."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from ansys.mapdl.mcp import app
from ansys.mapdl.mcp.contexts import get_guidelines_for
from ansys.mapdl.mcp.helpers import connect_to_mapdl_in_persistent_python
from ansys.mapdl.mcp.server import PyMAPDLAppContext, PyMAPDLMCP, launcher
from ansys.mapdl.mcp.tools import custom_plot, list_tool_sets, run_python_code

PYTHON_GUIDANCE = ("run_python_code", "custom_plot", "persistent Python session")


@pytest.mark.unit
@pytest.mark.parametrize("disabled_by", ["method", "programmatic"])
@pytest.mark.asyncio
async def test_disabled_python_never_constructs_a_session(monkeypatch, disabled_by):
    def unexpected_session(**kwargs):
        raise AssertionError("Disabled Python constructed a session")

    monkeypatch.setattr("ansys.mapdl.mcp.server.PersistentPythonSession", unexpected_session)
    server = PyMAPDLMCP(need_python=disabled_by != "programmatic")
    if disabled_by == "method":
        server.disable_python()

    async with server.product_lifespan(server) as context:
        assert context.python_session is None
        assert context.python_enabled is False


@pytest.mark.unit
def test_cli_option_disables_python(monkeypatch):
    monkeypatch.setattr(app, "_cli_config", getattr(app, "_cli_config", None), raising=False)
    monkeypatch.setattr(app, "_need_python", app._need_python)
    with (
        patch.object(asyncio, "run", side_effect=lambda coroutine: coroutine.close()),
        patch.object(app, "disable") as disable,
    ):
        launcher(["--disable-python"])

    assert app._need_python is False
    assert any(
        "python_execution" in call.kwargs.get("tags", set()) for call in disable.call_args_list
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_python_tools_and_helper_reject_before_accessing_session(mock_context):
    class ForbiddenSession:
        @property
        def metadata(self):
            raise AssertionError("Python session was accessed")

        def execute(self, *args, **kwargs):
            raise AssertionError("Python session was executed")

    context = mock_context.request_context.lifespan_context
    context.python_enabled = False
    context.python_session = ForbiddenSession()

    result = await run_python_code(mock_context, "raise RuntimeError('must not run')")
    assert json.loads(result.content[0].text) == {
        "success": False,
        "error": "Python execution is disabled by the operator.",
    }
    assert custom_plot(mock_context, "raise RuntimeError('must not run')").content[0].text == (
        "Python execution is disabled by the operator."
    )
    assert connect_to_mapdl_in_persistent_python(mock_context) == (
        "Python execution is disabled by the operator."
    )
    assert context.mapdl.mock_calls == []


@pytest.mark.unit
def test_toolsets_follow_request_python_policy(mock_context, monkeypatch):
    assert PyMAPDLAppContext().python_enabled is True

    no_request = SimpleNamespace(request_context=None)
    for need_python in (True, False):
        monkeypatch.setattr(app, "_need_python", need_python)
        names = {item["name"] for item in list_tool_sets(no_request)}
        assert ("python_execution" in names) is need_python

    context = mock_context.request_context.lifespan_context
    context.python_enabled = False
    disabled = {item["name"]: item for item in list_tool_sets(mock_context)}
    assert "python_execution" not in disabled
    assert {"run_mapdl_command", "run_multiple_mapdl_commands"}.issubset(
        disabled["command_execution"]["tools"]
    )
    assert "run_python_code" not in disabled["command_execution"]["tools"]
    assert "run_python_code" not in disabled["command_execution"]["skill"]
    assert disabled["visualization"]["tools"] == ["screenshot"]
    assert "custom_plot" not in disabled["visualization"]["skill"]

    context.python_enabled = True
    enabled = {item["name"]: item for item in list_tool_sets(mock_context)}
    assert enabled["python_execution"]["tools"] == ["run_python_code", "custom_plot"]
    assert enabled["visualization"]["tools"] == ["screenshot", "custom_plot"]
    assert "run_python_code" in enabled["command_execution"]["tools"]
    assert "run_python_code" in enabled["command_execution"]["skill"]
    assert "custom_plot" in enabled["visualization"]["skill"]


@pytest.mark.unit
def test_guidelines_follow_python_policy(monkeypatch):
    enabled = get_guidelines_for(content="postprocessing")
    assert all(text in enabled for text in PYTHON_GUIDANCE)

    monkeypatch.setattr(app, "_need_python", False)
    disabled = get_guidelines_for(content="postprocessing")
    assert not any(text in disabled for text in PYTHON_GUIDANCE)
    assert "screenshot" in disabled
    assert "Example Postprocessing Workflow" in disabled


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("connection_tool", ["connect_to_mapdl", "launch_mapdl_session"])
async def test_disabled_python_stays_hidden_across_connection_changes(
    mock_mapdl, tmp_path, connection_tool
):
    from ansys.mapdl.mcp import tools

    server = PyMAPDLMCP(need_python=False)
    for tool in (
        tools.connect_to_mapdl,
        tools.launch_mapdl_session,
        tools.disconnect_from_mapdl,
        tools.run_python_code,
        tools.custom_plot,
        tools.run_mapdl_command,
        tools.screenshot,
        get_guidelines_for,
    ):
        server.add_tool(tool)
    server.resource("toolsets://definition")(tools.list_tool_sets)
    server.disable(tags={"requires_mapdl"})
    target = (
        "ansys.mapdl.core.Mapdl"
        if connection_tool == "connect_to_mapdl"
        else "ansys.mapdl.core.launch_mapdl"
    )
    marker = tmp_path / "python-ran"
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
                assert {"run_mapdl_command", "run_multiple_mapdl_commands"}.issubset(
                    catalog["command_execution"]["tools"]
                )
                assert "run_python_code" not in catalog["command_execution"]["tools"]
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

        guidelines = await first.call_tool("get_guidelines_for", {"content": "postprocessing"})
        assert not any(text in guidelines.content[0].text for text in PYTHON_GUIDANCE)
        assert server.context.python_session is None
        assert not marker.exists()


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("restriction", ["aali", "locked_connection"])
async def test_python_policy_refresh_preserves_other_tool_restrictions(mock_mapdl, restriction):
    from ansys.mapdl.mcp import tools

    server = PyMAPDLMCP(need_python=False)
    server._cli_config = {
        "connect_on_startup": restriction == "locked_connection",
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
    server.disable(tags={"requires_mapdl", restriction})
    mock_mapdl._exited = False

    with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl):
        async with Client(server) as client:
            context = SimpleNamespace(
                request_context=SimpleNamespace(lifespan_context=server.context),
                fastmcp=server,
                send_notification=AsyncMock(),
            )
            for phase in ("connected", "disconnected", "reconnected"):
                connected = phase != "disconnected"
                server.context.mapdl = mock_mapdl if connected else None
                await tools._refresh_mapdl_tool_visibility(context)
                names = {tool.name for tool in await client.list_tools()}
                assert ("run_mapdl_command" in names) is connected
                assert ("screenshot" in names) is (connected and restriction != "aali")
                assert {"run_python_code", "custom_plot", "disconnect_from_mapdl"}.isdisjoint(names)
            assert server.context.python_session is None
