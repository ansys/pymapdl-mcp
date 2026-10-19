# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Private APDL admission and ownership of client-local native command logs."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from unicodedata import category
from uuid import uuid4

_BlockedCommand = Literal["/SYS", "/SYP", "/INPUT"]
_APDL_COMMAND_PREFIXES: dict[_BlockedCommand, str] = {
    "/SYS": "/SYS",
    "/SYP": "/SYP",
    "/INPUT": "/INP",
}


@dataclass(frozen=True)
class _SecurityOptions:
    apdl_log_dir: Path | None = None
    blocked_commands: frozenset[_BlockedCommand] = frozenset()
    python_enabled: bool = True


@dataclass(frozen=True)
class _LogRef:
    source: Literal["main", "python"]
    path: Path


def _check_apdl_request(
    commands: Sequence[str],
    blocked: frozenset[_BlockedCommand],
    *,
    header: str = "",
    comment: str = "",
) -> None:
    if not blocked:
        return
    if "$" in header or _has_unsafe_controls(header):
        raise ValueError("APDL request denied: unsafe delimiter or control in header.")
    if "$" in comment or _has_unsafe_controls(comment, multiline=True):
        raise ValueError("APDL request denied: unsafe delimiter or control in comment.")
    for command in commands:
        if _has_unsafe_controls(command, multiline=True):
            raise ValueError("APDL request denied: unsafe control in commands.")
        for line in command.splitlines():
            executable = line.split("!", 1)[0]
            if ("!" in line or "$" in executable) and any(quote in executable for quote in "'\""):
                raise ValueError("APDL request denied: ambiguous quoted command delimiter.")
            for segment in executable.split("$"):
                head = segment.split(",", 1)[0].strip()
                if head[:1] in ("'", '"'):
                    if (
                        len(head) <= 2
                        or head[-1] != head[0]
                        or any(character.isspace() for character in head[1:-1])
                    ):
                        raise ValueError("APDL request denied: unsupported quoted command head.")
                    head = head[1:-1]
                if any(quote in head for quote in "'\""):
                    raise ValueError("APDL request denied: ambiguous quoted command head.")
                if any(character.isspace() and character not in " \t" for character in head):
                    raise ValueError("APDL request denied: ambiguous whitespace in command head.")
                head = head.replace(" ", "").replace("\t", "")[:4].upper()
                for family, prefix in _APDL_COMMAND_PREFIXES.items():
                    if family in blocked and head == prefix:
                        raise ValueError(
                            f"APDL request denied: {family} command family is blocked."
                        )


def _check_apdl_literal(value: str, blocked: frozenset[_BlockedCommand]) -> None:
    if not blocked:
        return
    if any(character in "$!,\t\r\n" for character in value) or _has_unsafe_controls(value):
        raise ValueError("APDL request denied: unsafe delimiter or control in file_name.")


def _has_unsafe_controls(value: str, *, multiline: bool = False) -> bool:
    allowed = "\t\r\n" if multiline else "\t"
    return any(
        category(character) in ("Cc", "Cf", "Zl", "Zp") and character not in allowed
        for character in value
    )


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
    """Isolate PyMAPDL's private close API, which has no public equivalent."""
    mapdl._close_apdl_log()
