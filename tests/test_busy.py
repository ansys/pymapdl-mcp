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


"""Tests for background task support and the single-flight guard on MAPDL."""

import asyncio
import threading

from fastmcp import Client
from fastmcp_tasks import call_tool_task
import pytest

from ansys.mapdl.mcp import app, tools
from ansys.mapdl.mcp.busy import BusyError, check_not_busy, exclusive, run_exclusive


@pytest.mark.unit
class TestExclusive:
    async def test_busy_while_running(self, mock_mapdl):
        async with exclusive(mock_mapdl, "run_mapdl_command"):
            with pytest.raises(BusyError, match="run_mapdl_command"):
                check_not_busy(mock_mapdl)
            with pytest.raises(BusyError):
                async with exclusive(mock_mapdl, "upload_file"):
                    pass

        check_not_busy(mock_mapdl)

    async def test_released_after_error(self, mock_mapdl):
        with pytest.raises(RuntimeError):
            async with exclusive(mock_mapdl, "run_mapdl_command"):
                raise RuntimeError("boom")

        check_not_busy(mock_mapdl)

    async def test_guard_held_until_thread_finishes_after_cancel(self, mock_mapdl):
        release = threading.Event()
        task = asyncio.create_task(run_exclusive(mock_mapdl, "solve", lambda: release.wait(10)))
        await asyncio.sleep(0.2)

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        with pytest.raises(BusyError, match="solve"):
            check_not_busy(mock_mapdl)

        release.set()
        for _ in range(50):
            await asyncio.sleep(0.05)
            try:
                check_not_busy(mock_mapdl)
                break
            except BusyError:
                continue
        check_not_busy(mock_mapdl)

    async def test_other_tools_raise_busy(self, mock_context, mock_mapdl):
        async with exclusive(mock_mapdl, "run_mapdl_command"):
            with pytest.raises(BusyError):
                await tools.run_multiple_mapdl_commands(mock_context, ["/PREP7"])
            with pytest.raises(BusyError):
                await tools.upload_file(mock_context, __file__)


@pytest.mark.unit
class TestBackgroundTask:
    @pytest.mark.parametrize("tool", ["run_mapdl_command", "run_multiple_mapdl_commands"])
    async def test_tools_declared_as_tasks(self, tool):
        registered = await app.get_tool(tool)

        assert registered is not None
        assert registered.task_config.supports_tasks()

    async def test_solve_runs_as_task_and_blocks_others(self, mock_mapdl):
        release = threading.Event()
        mock_mapdl._exited = False
        mock_mapdl._exiting = False
        mock_mapdl.run.side_effect = lambda cmd: release.wait(10) and "solved"

        async with Client(app, mode="auto") as client:
            app.context.mapdl = mock_mapdl
            try:
                task = await call_tool_task(client, "run_mapdl_command", {"cmd": "SOLVE"})
                await asyncio.sleep(0.5)

                with pytest.raises(Exception, match="busy"):
                    await client.call_tool("run_multiple_mapdl_commands", {"commands": ["/PREP7"]})

                release.set()
                result = await task.result()
                assert "solved" in result.content[0].text
            finally:
                release.set()
                app.context.mapdl = None
