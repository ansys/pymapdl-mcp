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

"""Private helpers for native MAPDL client command logs."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4


@dataclass(frozen=True)
class _LogRef:
    source: Literal["main", "python"]
    path: Path


def _allocate_log(context: Any, source: Literal["main", "python"]) -> tuple[str, _LogRef] | None:
    if context.command_log_dir is None:
        return None
    log_id = uuid4().hex
    return log_id, _LogRef(source, context.command_log_dir / f"{source}-{log_id}.log")


def _register_log(context: Any, allocation: tuple[str, _LogRef]) -> None:
    log_id, ref = allocation
    with context.command_log_lock:
        context.command_logs[log_id] = ref


def _attach_main_log(context: Any, mapdl: Any) -> None:
    allocation = _allocate_log(context, "main")
    if allocation is None:
        return
    try:
        mapdl.open_apdl_log(str(allocation[1].path), mode="x")
    except Exception as exc:
        try:
            _retire_native_log(mapdl)
        except Exception as close_exc:
            raise RuntimeError(
                f"Failed to attach native main command log: {exc}. "
                f"Failed to close native log: {close_exc}"
            ) from exc
        raise RuntimeError(f"Failed to attach native main command log: {exc}") from exc
    _register_log(context, allocation)


def _retire_native_log(mapdl: Any) -> None:
    """Close PyMAPDL's native log using its private API."""
    mapdl._close_apdl_log()
