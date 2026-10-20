# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import pytest

from ansys.mapdl.mcp import tools
from ansys.mapdl.mcp._apdl_security import _check_apdl_literal, _check_apdl_request


@pytest.mark.parametrize(
    "command,family",
    [
        (" /sYs,unused", "/SYS"),
        ("FINISH$/SYP,unused", "/SYP"),
        ("FINISH\r\n/INP,missing", "/INPUT"),
        ("\u2003'/INPUT'\u2003,missing", "/INPUT"),
        ("/I\tNPUT,missing", "/INPUT"),
    ],
)
def test_direct_family_check_preserves_head_normalization(command, family):
    with pytest.raises(ValueError, match=family):
        _check_apdl_request([command], frozenset({family}))


@pytest.mark.parametrize("command", ["'/SYS", "FI\u2003NISH", "FINISH\x00/SYS"])
def test_ambiguous_command_fails_closed_when_restricted(command):
    with pytest.raises(ValueError, match="APDL request denied"):
        _check_apdl_request([command], frozenset({"/SYS"}))
    _check_apdl_request([command], frozenset())


@pytest.mark.parametrize("value", ["beam$other", "beam,other", "beam!comment", "beam\nother"])
def test_interpolated_filename_rejects_apdl_delimiters(value):
    with pytest.raises(ValueError, match="file_name"):
        _check_apdl_literal(value, frozenset({"/SYS"}))
    _check_apdl_literal(value, frozenset())


@pytest.fixture
def restricted_context():
    mapdl = SimpleNamespace(events=[])
    for name in ("run", "input_strings", "com", "post1", "resume", "cdread", "file"):
        def record(*args, _name=name, **kwargs):
            mapdl.events.append(_name)

        setattr(mapdl, name, record)
    context = SimpleNamespace(
        mapdl=mapdl, blocked_commands=frozenset({"/SYS", "/SYP", "/INPUT"})
    )
    return SimpleNamespace(request_context=SimpleNamespace(lifespan_context=context)), mapdl


def test_single_and_batch_reject_before_metadata_or_dispatch(restricted_context):
    ctx, mapdl = restricted_context
    with pytest.raises(ValueError, match="/SYS"):
        tools.run_mapdl_command(ctx, "/SYS,run", header="header", comment="comment")
    result = tools.run_multiple_mapdl_commands(
        ctx, ["FINISH", "/INPUT,file"], header="header", comment="comment"
    )
    assert "APDL request denied" in result.content[0].text


def test_screenshot_rejects_before_capture_or_view_restore(restricted_context, monkeypatch):
    ctx, _ = restricted_context
    monkeypatch.setattr(tools, "_capture_screenshot", lambda *args: pytest.fail("captured"))
    result = tools.screenshot(ctx, commands="/SYP,command", four_view=True)
    assert "APDL request denied" in result.content[0].text


@pytest.mark.parametrize(
    "call",
    [
        lambda ctx: tools.resume_model(ctx, "model$other", "db"),
        lambda ctx: tools.open_results(ctx, "results,other"),
    ],
)
def test_file_tools_reject_before_solver_side_effects(restricted_context, call):
    ctx, mapdl = restricted_context
    result = call(ctx)
    assert "APDL request denied" in result.content[0].text
    assert mapdl.events == []


def test_batch_failure_reports_unknown_execution_prefix(restricted_context):
    ctx, mapdl = restricted_context

    def fail(commands):
        raise RuntimeError("solver failure")

    mapdl.input_strings = fail
    result = tools.run_multiple_mapdl_commands(ctx, ["FINISH", "/COM,later"])
    assert "Attempted a batch of 2 commands" in result.content[0].text
    assert "Some commands may not have executed." in result.content[0].text
