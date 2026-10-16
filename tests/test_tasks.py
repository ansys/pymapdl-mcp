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


"""Tests for hybrid async task execution."""

import threading

from fastmcp.exceptions import ToolError
import pytest

from ansys.mapdl.mcp import tools
from ansys.mapdl.mcp.tasks import BusyError


@pytest.fixture
def short_wait(monkeypatch):
    monkeypatch.setenv("PYMAPDL_MCP_TASK_WAIT", "0.2")


@pytest.mark.unit
class TestHybridTasks:
    def test_fast_command_returns_result_directly(self, mock_context):
        result = tools.run_mapdl_command(mock_context, "/PREP7")

        assert "executed successfully" in result.content[0].text
        assert tools.list_tasks().structured_content == {"tasks": []}

    def test_slow_command_returns_task_and_blocks_other_tools(
        self, mock_context, mock_mapdl, short_wait
    ):
        release = threading.Event()
        mock_mapdl.run.side_effect = lambda cmd: release.wait(10) and "solved"

        result = tools.run_mapdl_command(mock_context, "SOLVE")
        info = result.structured_content
        assert info["status"] == "running"

        with pytest.raises(BusyError, match=info["task_id"]):
            tools.run_multiple_mapdl_commands(mock_context, ["/PREP7"])

        assert tools.get_task_status(info["task_id"]).structured_content["status"] == "running"

        release.set()
        for _ in range(100):
            if tools.get_task_status(info["task_id"]).structured_content["status"] != "running":
                break
            threading.Event().wait(0.05)

        final = tools.get_task_result(info["task_id"])
        assert "solved" in final.content[0].text

        # MAPDL is available again
        mock_mapdl.run.side_effect = None
        assert (
            "executed successfully"
            in tools.run_mapdl_command(mock_context, "/PREP7").content[0].text
        )

    def test_failed_task_reports_error(self, mock_context, mock_mapdl, short_wait):
        release = threading.Event()

        def _boom(cmd):
            release.wait(10)
            raise RuntimeError("solver crashed")

        mock_mapdl.run.side_effect = _boom
        task_id = tools.run_mapdl_command(mock_context, "SOLVE").structured_content["task_id"]
        release.set()
        for _ in range(100):
            if tools.get_task_status(task_id).structured_content["status"] == "failed":
                break
            threading.Event().wait(0.05)

        with pytest.raises(ToolError, match="solver crashed"):
            tools.get_task_result(task_id)

    def test_unknown_task(self):
        with pytest.raises(ToolError, match="Unknown task"):
            tools.get_task_status("nope")
