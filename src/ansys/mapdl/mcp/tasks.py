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

"""Hybrid async task execution for potentially long-running MAPDL tools.

The work of a tool is run in the background and the tool waits for a short time
(``PYMAPDL_MCP_TASK_WAIT`` seconds, 5 by default). If the work finishes in time, the normal
result is returned. Otherwise, a reference to a *task* is returned and the result can be
retrieved with the ``get_task_status`` and ``get_task_result`` tools.

MAPDL cannot run commands in parallel, so only one task can be running per MAPDL instance. While
it is running, any other tool using that instance raises :class:`BusyError`.
"""

import asyncio
from collections.abc import Awaitable, Callable
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
import json
import os
import threading
import time
from typing import Any
import uuid

from fastmcp.exceptions import ToolError
from fastmcp.tools.base import ToolResult

from mcp.types import TextContent

TASK_WAIT_ENV = "PYMAPDL_MCP_TASK_WAIT"
TASK_TTL_ENV = "PYMAPDL_MCP_TASK_TTL"
DEFAULT_TASK_WAIT = 5.0
DEFAULT_TASK_TTL = 3600.0

RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"


class BusyError(ToolError):
    """Raised when MAPDL is busy running a task and cannot accept more calls."""


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def get_task_wait() -> float:
    """Seconds to wait for a tool result before returning a task reference."""
    return _env_float(TASK_WAIT_ENV, DEFAULT_TASK_WAIT)


@dataclass
class Task:
    """A background execution of a tool."""

    tool: str
    key: Any
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: str = RUNNING
    started: float = field(default_factory=time.monotonic)
    finished: float | None = None
    result: ToolResult | None = None
    error: BaseException | None = None

    @property
    def elapsed(self) -> float:
        """Seconds since the task started (frozen once finished)."""
        return round((self.finished or time.monotonic()) - self.started, 1)

    def summary(self) -> dict[str, Any]:
        """JSON-serializable description of the task."""
        info: dict[str, Any] = {
            "task_id": self.task_id,
            "tool": self.tool,
            "status": self.status,
            "elapsed_seconds": self.elapsed,
        }
        if self.error is not None:
            info["error"] = str(self.error)
        return info

    def _finish(self, result: ToolResult | None, error: BaseException | None) -> None:
        self.result = result
        self.error = error
        self.status = FAILED if error is not None else COMPLETED
        self.finished = time.monotonic()


class TaskManager:
    """Registry of tasks enforcing one running task per MAPDL instance."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="mapdl-task")

    def _purge(self) -> None:
        ttl = _env_float(TASK_TTL_ENV, DEFAULT_TASK_TTL)
        now = time.monotonic()
        for task_id in [
            t.task_id
            for t in self._tasks.values()
            if t.finished is not None and now - t.finished > ttl
        ]:
            del self._tasks[task_id]

    def running_task(self, key: Any) -> Task | None:
        """Return the task currently running for *key*, if any."""
        with self._lock:
            return next(
                (t for t in self._tasks.values() if t.key is key and t.status == RUNNING),
                None,
            )

    @staticmethod
    def _busy_error(task: Task) -> BusyError:
        return BusyError(
            f"MAPDL is busy running task '{task.task_id}' ({task.tool}, "
            f"{task.elapsed}s elapsed) and cannot accept other calls. "
            f"Use get_task_status('{task.task_id}') to poll it and "
            f"get_task_result('{task.task_id}') once it has completed. Do not retry."
        )

    def check_not_busy(self, key: Any) -> None:
        """Raise :class:`BusyError` if a task is running for *key*."""
        task = self.running_task(key)
        if task is not None:
            raise self._busy_error(task)

    def _register(self, tool: str, key: Any) -> Task:
        with self._lock:
            self._purge()
            running = next(
                (t for t in self._tasks.values() if t.key is key and t.status == RUNNING), None
            )
            if running is not None:
                raise self._busy_error(running)
            task = Task(tool=tool, key=key)
            self._tasks[task.task_id] = task
            return task

    def _discard(self, task: Task) -> None:
        with self._lock:
            self._tasks.pop(task.task_id, None)

    def get(self, task_id: str) -> Task:
        """Return a task by ID or raise :class:`ToolError` if unknown/expired."""
        with self._lock:
            self._purge()
            task = self._tasks.get(task_id)
        if task is None:
            raise ToolError(f"Unknown task '{task_id}'. It does not exist or has expired.")
        return task

    def list(self) -> list[Task]:
        """Return all known tasks."""
        with self._lock:
            self._purge()
            return list(self._tasks.values())

    def run(self, tool: str, key: Any, func: Callable[[], ToolResult]) -> ToolResult:
        """Run blocking *func* in the background and wait for it up to the configured time."""
        task = self._register(tool, key)
        future: Future[ToolResult] = self._executor.submit(func)

        def _done(fut: Future[ToolResult]) -> None:
            exc = fut.exception()
            task._finish(None if exc else fut.result(), exc)

        future.add_done_callback(_done)
        try:
            result = future.result(timeout=get_task_wait())
        except FutureTimeoutError:
            # The worker may itself raise TimeoutError (same class on Python >= 3.11)
            if not future.done():
                return running_result(task)
            self._discard(task)
            raise
        except BaseException:
            self._discard(task)
            raise
        self._discard(task)
        return result

    async def run_async(
        self, tool: str, key: Any, coro_factory: Callable[[], Awaitable[ToolResult]]
    ) -> ToolResult:
        """Run a coroutine in the background, like :meth:`run`."""
        task = self._register(tool, key)

        async def _wrapper() -> ToolResult:
            return await coro_factory()

        aio_task = asyncio.ensure_future(_wrapper())

        def _done(fut: "asyncio.Future[ToolResult]") -> None:
            if fut.cancelled():
                task._finish(None, asyncio.CancelledError())
                return
            exc = fut.exception()
            task._finish(None if exc else fut.result(), exc)

        aio_task.add_done_callback(_done)
        done, _ = await asyncio.wait({aio_task}, timeout=get_task_wait())
        if aio_task not in done:
            return running_result(task)
        self._discard(task)
        return aio_task.result()


def running_result(task: Task) -> ToolResult:
    """Build the result returned when a tool takes longer than the wait time."""
    info = task.summary()
    info["message"] = (
        "The operation is still running in the background. MAPDL cannot accept other calls "
        f"until it finishes. Poll get_task_status('{task.task_id}') and, once it is "
        f"'completed', call get_task_result('{task.task_id}'). Do not re-send the command."
    )
    return ToolResult(
        [TextContent(type="text", text=json.dumps(info, indent=2))], structured_content=info
    )


task_manager = TaskManager()
