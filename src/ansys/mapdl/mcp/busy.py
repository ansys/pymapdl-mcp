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

"""Single-flight guard for MAPDL instances.

Long-running tools are declared with ``task=True`` so that MCP clients supporting background
tasks can run them as FastMCP tasks (start, poll and retrieve the result later).

MAPDL cannot run commands in parallel: it blocks until the current set of commands (like
``SOLVE``) has completely finished. This module ensures only one tool uses a MAPDL instance at
a time. If another tool tries to use it meanwhile, :class:`BusyError` is raised.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import threading
import time
from typing import Any

from fastmcp.exceptions import ToolError


class BusyError(ToolError):
    """Raised when MAPDL is busy running another tool and cannot accept more calls."""


_lock = threading.Lock()
_running: dict[int, tuple[str, float]] = {}


def _busy_error(tool: str, started: float) -> BusyError:
    return BusyError(
        f"MAPDL is busy running '{tool}' ({time.monotonic() - started:.0f}s elapsed) and cannot "
        "accept other calls. MAPDL does not run commands in parallel. Wait for that operation to "
        "finish (check its task status) and do not retry in the meantime."
    )


def check_not_busy(mapdl: Any) -> None:
    """Raise :class:`BusyError` if a tool is currently using *mapdl*."""
    with _lock:
        running = _running.get(id(mapdl))
    if running is not None:
        raise _busy_error(*running)


@asynccontextmanager
async def exclusive(mapdl: Any, tool: str) -> AsyncIterator[None]:
    """Mark *mapdl* as in use by *tool*, raising :class:`BusyError` if it already is."""
    with _lock:
        running = _running.get(id(mapdl))
        if running is None:
            _running[id(mapdl)] = (tool, time.monotonic())
    if running is not None:
        raise _busy_error(*running)
    try:
        yield
    finally:
        with _lock:
            _running.pop(id(mapdl), None)
