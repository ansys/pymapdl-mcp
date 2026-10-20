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

"""Tool surface contract tests.

Deterministic checks on what an MCP client (and therefore an LLM) actually
sees through ``tools/list``: tool names, descriptions, input schemas, tags,
and connection-gated visibility.

Tool descriptions and schemas are what an LLM relies on to choose a tool, so
any change to them is captured by a snapshot and must be reviewed.

Related to `#118 <https://github.com/ansys/pymapdl-mcp/issues/118>`_.
Evaluating which tool a real LLM picks for a given prompt is out of scope.

To regenerate the snapshot after an intended change::

    UPDATE_TOOL_SNAPSHOT=1 pytest tests/test_tool_surface.py
"""

import json
import os
from pathlib import Path

from fastmcp import Client
import pytest

from ansys.mapdl.mcp import contexts, prompts, tools  # noqa: F401  (registers tools/prompts)
from ansys.mapdl.mcp.server import app
from ansys.mapdl.mcp.tools import REQUIRES_MAPDL_TAG

SNAPSHOT = Path(__file__).parent / "data" / "tool_surface.json"

# Tools an agent needs to discover, start, or reach MAPDL before any connection.
SESSION_ENTRY_TOOLS = {
    "check_mapdl_installed",
    "connect_to_mapdl",
    "launch_mapdl_session",
    "list_mapdl_instances",
}


async def _list_tools(hide_requires_mapdl: bool) -> dict:
    """Return the tools visible to an MCP client, keyed by name."""
    if hide_requires_mapdl:
        app.disable(tags={REQUIRES_MAPDL_TAG})
    async with Client(app) as client:
        return {t.name: t for t in await client.list_tools()}


async def _registered_tags() -> dict[str, list[str]]:
    """Return the tags of every registered tool, independent of visibility."""
    return {t.name: sorted(t.tags or []) for t in await app._local_provider._list_tools()}


@pytest.mark.unit
class TestVisibilityThroughProtocol:
    """Connection-gated visibility as observed by an MCP client."""

    @pytest.mark.asyncio
    async def test_requires_mapdl_tools_hidden_before_connection(self):
        """Hiding ``REQUIRES_MAPDL_TAG`` removes exactly the tagged tools from ``tools/list``."""
        all_visible = await _list_tools(hide_requires_mapdl=False)
        pre_connect = await _list_tools(hide_requires_mapdl=True)
        tags = await _registered_tags()

        tagged = {name for name, t in tags.items() if REQUIRES_MAPDL_TAG in t}
        assert tagged, f"No tool is tagged '{REQUIRES_MAPDL_TAG}'."
        assert set(all_visible) - set(pre_connect) == tagged

    @pytest.mark.asyncio
    async def test_session_entry_tools_visible_before_connection(self):
        """An agent must always have a path to start or reach MAPDL."""
        pre_connect = await _list_tools(hide_requires_mapdl=True)

        missing = SESSION_ENTRY_TOOLS - set(pre_connect)
        assert not missing, f"Session entry tools hidden before connection: {sorted(missing)}"


@pytest.mark.unit
class TestToolSurfaceSnapshot:
    """Tool names, descriptions, schemas, and tags as exposed to clients."""

    @pytest.mark.asyncio
    async def test_tool_surface_matches_snapshot(self):
        """Fail when any tool name, description, input schema, or tag changes."""
        visible = await _list_tools(hide_requires_mapdl=False)
        tags = await _registered_tags()
        current = {
            name: {
                "description": t.description,
                "input_schema": t.inputSchema,
                "tags": tags.get(name, []),
            }
            for name, t in sorted(visible.items())
        }

        if os.getenv("UPDATE_TOOL_SNAPSHOT"):
            SNAPSHOT.parent.mkdir(exist_ok=True)
            SNAPSHOT.write_text(
                json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            pytest.skip("Tool surface snapshot updated.")

        assert SNAPSHOT.exists(), (
            f"Missing snapshot {SNAPSHOT}. Generate it with UPDATE_TOOL_SNAPSHOT=1."
        )
        expected = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

        assert sorted(current) == sorted(expected), "Set of exposed tools changed."
        changed = [name for name in current if current[name] != expected[name]]
        assert not changed, (
            f"Tool surface changed for {changed}. If intended, regenerate the snapshot "
            "with UPDATE_TOOL_SNAPSHOT=1 and review the diff."
        )

    @pytest.mark.asyncio
    async def test_every_tool_and_parameter_is_described(self):
        """LLMs select tools and fill arguments from these descriptions."""
        undocumented = []
        for name, t in (await _list_tools(hide_requires_mapdl=False)).items():
            if not (t.description or "").strip():
                undocumented.append(name)
            for param, spec in t.inputSchema.get("properties", {}).items():
                if not (spec.get("description") or "").strip():
                    undocumented.append(f"{name}.{param}")
        assert not undocumented, f"Missing descriptions: {undocumented}"
