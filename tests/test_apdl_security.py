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

import base64
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

from ansys.mapdl.core.mapdl_core import _MapdlCore
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
import pytest

from ansys.mapdl.mcp import tools
from ansys.mapdl.mcp._security import _SecurityOptions
from ansys.mapdl.mcp.server import PyMAPDLAppContext

_NORMALIZED_HEADS = [
    ("'/SYS'", "/SYS"),
    ('"/sysignored"', "/SYS"),
    ("/ SYS", "/SYS"),
    ("/S YS", "/SYS"),
    ("/S Y Signored", "/SYS"),
    ("/\tSYS", "/SYS"),
    ("/S\tYS", "/SYS"),
    ("'/SYP'", "/SYP"),
    ('"/sypignored"', "/SYP"),
    ("/ SYP", "/SYP"),
    ("/S YP", "/SYP"),
    ("/S Y Pignored", "/SYP"),
    ("/\tSYP", "/SYP"),
    ("/S\tYP", "/SYP"),
    ("'/INPUT',missing", "/INPUT"),
    ('"/inputignored",missing', "/INPUT"),
    ("'/INP',missing", "/INPUT"),
    ('"/INP",missing', "/INPUT"),
    ("/ INPUT,missing", "/INPUT"),
    ("/I NPUT,missing", "/INPUT"),
    ("/IN PUT,missing", "/INPUT"),
    ("/I N P U Tignored,missing", "/INPUT"),
    ("/\tINPUT,missing", "/INPUT"),
    ("/I\tNPUT,missing", "/INPUT"),
    ("/IN\tPUT,missing", "/INPUT"),
    *[
        (f"{space}{quote}{head}{quote}{space}", family)
        for space in ("\u00a0", "\u2003")
        for head, family in (("/SYS", "/SYS"), ("/SYP", "/SYP"), ("/INPUT", "/INPUT"))
        for quote in ("", "'", '"')
    ],
]


@dataclass
class SubmissionSink:
    events: list = field(default_factory=list)
    _exited: bool = False
    _exiting: bool = False
    failure: bool = False

    com = _MapdlCore.com
    resume = _MapdlCore.resume
    cdread = _MapdlCore.cdread
    file = _MapdlCore.file
    post1 = _MapdlCore.post1

    def run(self, command, **kwargs):
        self.events.append(("run", command))
        return ""

    def input_strings(self, commands):
        self.events.append(("batch", commands))
        if self.failure:
            raise RuntimeError("Solver failed after an unknown prefix")
        return ""

    def screenshot(self, savefig):
        self.events.append(("capture",))
        Path(savefig).write_bytes(b"\x89PNG\r\n\x1a\nfixture-image")
        return savefig


@pytest.fixture
def restricted_context():
    sink = SubmissionSink()
    context = PyMAPDLAppContext(
        mapdl=sink,
        security_options=_SecurityOptions(blocked_commands=frozenset({"/SYS", "/SYP", "/INPUT"})),
    )
    return SimpleNamespace(request_context=SimpleNamespace(lifespan_context=context)), sink


@pytest.mark.unit
@pytest.mark.parametrize(
    "command,family",
    [
        (" /sYs,unused", "/SYS"),
        ("\t/SYSignored,unused", "/SYS"),
        ("/sypignored,unused", "/SYP"),
        ("/INP,missing", "/INPUT"),
        ("/inputignored,missing", "/INPUT"),
        ("FINISH$/SYS,unused", "/SYS"),
        ("FINISH\n/SYP,unused", "/SYP"),
        ("FINISH\r\n/INP,missing", "/INPUT"),
        ("FINISH\r/SYS,unused", "/SYS"),
        ("FINISH ! ignored\r\n/SYP,unused", "/SYP"),
        *_NORMALIZED_HEADS,
    ],
)
def test_direct_family_denial_precedes_metadata(restricted_context, command, family):
    context, sink = restricted_context
    with pytest.raises(ValueError, match=family):
        tools.run_mapdl_command(context, command, header="Header", comment="Comment")
    assert sink.events == []
    tools.run_mapdl_command(context, "FINISH", header="Header", comment="One\r\nTwo")
    assert sink.events == [
        ("run", "/COM,# Header"),
        ("run", "/COM,One"),
        ("run", "/COM,Two"),
        ("run", "FINISH"),
    ]


@pytest.mark.unit
@pytest.mark.parametrize("separator", ["$", "\n", "\r\n", "\r"])
def test_late_batch_denial_has_no_effects(restricted_context, separator):
    context, sink = restricted_context
    result = tools.run_multiple_mapdl_commands(
        context,
        [" FINISH ", "", " /COM,allowed " + separator + " /INP,missing "],
        header="Header",
        comment="Comment",
    )
    assert "APDL request denied" in result.content[0].text
    assert "/INPUT" in result.content[0].text
    assert sink.events == []
    result = tools.run_multiple_mapdl_commands(
        context,
        [" FINISH ", "", " /COM,allowed "],
        header="Header",
        comment="One\nTwo",
    )
    assert result.structured_content["success"] is True
    assert result.structured_content["commands_executed"] == ["FINISH", "/COM,allowed"]
    assert sink.events == [
        ("run", "/COM,# Header"),
        ("run", "/COM,One"),
        ("run", "/COM,Two"),
        ("batch", ["FINISH", "/COM,allowed"]),
    ]


@pytest.mark.unit
@pytest.mark.parametrize("tool", [tools.run_mapdl_command, tools.run_multiple_mapdl_commands])
@pytest.mark.parametrize(
    "metadata",
    [
        {"header": "Title$/SYS,unused"},
        {"header": "Title\r\n/SYP,unused"},
        {"header": "Title\r/INP,missing"},
        {"header": "Title\x00"},
        {"comment": "One\nTwo$/INP,missing"},
        {"comment": "One\x0b/SYS,unused"},
        {"comment": "One\x1b"},
        {"comment": "One\u2028/SYS,unused"},
        {"comment": "One\ufeff/SYS,unused"},
        {"comment": "ignored ! $separator"},
        *[
            {field: "Title$" + command}
            for command, _ in _NORMALIZED_HEADS
            for field in ("header", "comment")
        ],
    ],
)
def test_metadata_denied_before_commands(restricted_context, tool, metadata):
    context, sink = restricted_context
    commands = "FINISH" if tool is tools.run_mapdl_command else ["FINISH"]
    if tool is tools.run_mapdl_command:
        with pytest.raises(ValueError, match="APDL request denied"):
            tool(context, commands, **metadata)
    else:
        assert "APDL request denied" in tool(context, commands, **metadata).content[0].text
    assert sink.events == []
    result = tool(context, commands, header="A model", comment="One\rTwo\nThree ! explanatory")
    assert "successfully" in result.content[-1].text.lower()
    assert sink.events[:4] == [
        ("run", "/COM,# A model"),
        ("run", "/COM,One"),
        ("run", "/COM,Two"),
        ("run", "/COM,Three ! explanatory"),
    ]


@pytest.mark.unit
@pytest.mark.parametrize("four_view", [False, True])
@pytest.mark.parametrize(
    "command", ["KPLOT$/INP,missing", *[item[0] for item in _NORMALIZED_HEADS]]
)
def test_screenshot_denial_never_captures_or_restores(
    restricted_context, monkeypatch, four_view, command
):
    context, sink = restricted_context
    created = []
    original = tools.tempfile.mkstemp

    def capture_tempfile(*args, **kwargs):
        result = original(*args, **kwargs)
        created.append(Path(result[1]))
        return result

    monkeypatch.setattr(tools.tempfile, "mkstemp", capture_tempfile)
    result = tools.screenshot(context, command, four_view=four_view)
    assert result.content[0].text.startswith("Failed to capture screenshot: APDL request denied")
    assert sink.events == []
    assert created == []
    try:
        result = tools.screenshot(context, "KPLOT", four_view=four_view)
        assert result.content[1].type == "image"
        assert base64.b64decode(result.content[1].data) == b"\x89PNG\r\n\x1a\nfixture-image"
        assert len(created) == 1
        assert sink.events[1] == ("capture",)
        if four_view:
            assert sink.events[0][0] == "batch"
            assert "/VIEW,4,1,1,1\n" in sink.events[0][1]
            assert sink.events[0][1].endswith("KPLOT\n")
            assert sink.events[2] == (
                "batch",
                "/WINDOW,1,FULL\n/WINDOW,2,OFF\n/WINDOW,3,OFF\n/WINDOW,4,OFF\n/TRIAD,ORIG\n",
            )
        else:
            assert sink.events == [("batch", "KPLOT"), ("capture",)]
    finally:
        for path in created:
            path.unlink(missing_ok=True)


@pytest.mark.unit
@pytest.mark.parametrize(
    "file_name",
    [
        "beam$/SYS,unused",
        "'beam$/SYS,unused'",
        '"beam!/INP,missing"',
        "beam\r/INP,missing",
        "beam\nFINISH",
        "beam!",
        "beam,rst",
        "beam\x00",
        "beam\x7f",
        "beam\t",
        "beam\u2029",
        "beam\ufeff",
        "beam$'/SYS'",
        "beam$/S YP",
        "beam$/I\tNPUT,missing",
    ],
)
@pytest.mark.parametrize("extension", ["db", "cdb"])
def test_interpolated_filename_denial_precedes_model_or_post1(
    restricted_context, file_name, extension
):
    context, sink = restricted_context
    result = tools.resume_model(context, file_name, extension)
    assert "APDL request denied" in result.content[0].text
    result = tools.open_results(context, file_name)
    assert result.content[0].text.startswith("Failed to open results: APDL request denied")
    assert sink.events == []
    result = tools.resume_model(context, "C:/models/a model", extension)
    assert "Model resumed successfully" in result.content[0].text
    result = tools.open_results(context, "C:/models/a model")
    assert "Entered POST1 and set active results file" in result.content[0].text
    expected = (
        "RESUME,C:/models/a model,db,,,"
        if extension == "db"
        else "CDREAD,db,C:/models/a model,cdb,,,"
    )
    assert sink.events == [
        ("run", expected),
        ("run", "/POST1"),
        ("run", "FILE,C:/models/a model,rst"),
    ]


@pytest.mark.unit
def test_selected_families_are_independent_and_default_is_unrestricted(restricted_context):
    context, sink = restricted_context
    context.request_context.lifespan_context.security_options = _SecurityOptions(
        blocked_commands=frozenset({"/SYS"})
    )
    tools.run_mapdl_command(context, "/SYP,unused")
    tools.run_mapdl_command(context, "/INP,missing")
    assert sink.events == [("run", "/SYP,unused"), ("run", "/INP,missing")]
    context.request_context.lifespan_context.security_options = _SecurityOptions()
    result = tools.run_multiple_mapdl_commands(
        context, ["/SYS,unused"], header="Title$literal\nline", comment="Text$literal"
    )
    assert result.structured_content["success"] is True
    tools.open_results(context, "beam$literal")
    assert sink.events[2:] == [
        ("run", "/COM,# Title$literal\nline"),
        ("run", "/COM,Text$literal"),
        ("batch", ["/SYS,unused"]),
        ("run", "/POST1"),
        ("run", "FILE,beam$literal,rst"),
    ]


@pytest.mark.unit
def test_batch_failure_does_not_claim_all_entries_executed(restricted_context):
    context, sink = restricted_context
    sink.failure = True
    result = tools.run_multiple_mapdl_commands(context, ["FINISH", "/COM,later"])
    assert "Attempted a batch of 2 commands" in result.content[0].text
    assert "Some commands may not have executed." in result.content[0].text
    assert sink.events == [("batch", ["FINISH", "/COM,later"])]
    sink.failure = False
    result = tools.run_multiple_mapdl_commands(context, ["FINISH"])
    assert result.structured_content["success"] is True
    assert sink.events[-1] == ("batch", ["FINISH"])


@pytest.mark.unit
async def test_actual_mcp_denies_whole_batch_and_allows_normal_workflow(restricted_context):
    context, sink = restricted_context

    @asynccontextmanager
    async def lifespan(server):
        yield context.request_context.lifespan_context

    server = FastMCP("APDL admission", lifespan=lifespan)
    for function in (
        tools.run_mapdl_command,
        tools.run_multiple_mapdl_commands,
        tools.open_results,
        tools.resume_model,
        tools.screenshot,
    ):
        server.add_tool(function)
    async with Client(server) as client:
        with pytest.raises(ToolError, match="APDL request denied"):
            await client.call_tool("run_mapdl_command", {"cmd": "FINISH", "header": "bad$/SYS"})
        assert sink.events == []
        for name, arguments in (
            ("screenshot", {"commands": "EPLOT$/INP,missing", "four_view": True}),
            ("resume_model", {"file_name": "model$/SYS,unused", "extension": "cdb"}),
            ("open_results", {"file_name": "model$/INP,missing"}),
        ):
            result = await client.call_tool(name, arguments)
            assert "APDL request denied" in result.content[0].text
            assert sink.events == []
        denied = await client.call_tool(
            "run_multiple_mapdl_commands",
            {"commands": ["FINISH", "/INP,missing"], "header": "Title"},
        )
        assert "APDL request denied" in denied.content[0].text
        assert sink.events == []
        for command, family in _NORMALIZED_HEADS:
            with pytest.raises(ToolError, match=family):
                await client.call_tool(
                    "run_mapdl_command", {"cmd": command, "header": "Title", "comment": "Comment"}
                )
            assert sink.events == []
            denied = await client.call_tool(
                "run_multiple_mapdl_commands",
                {"commands": ["'/TITLE',never issued", command], "header": "Title"},
            )
            assert family in denied.content[0].text
            assert sink.events == []
            for four_view in (False, True):
                denied = await client.call_tool(
                    "screenshot", {"commands": command, "four_view": four_view}
                )
                assert family in denied.content[0].text
                assert sink.events == []
        allowed = await client.call_tool(
            "run_multiple_mapdl_commands", {"commands": ["FI NISH", "'/TITLE',ordinary"]}
        )
        assert allowed.structured_content["success"] is True
        assert sink.events == [("batch", ["FI NISH", "'/TITLE',ordinary"])]
        result = await client.call_tool("resume_model", {"file_name": "model", "extension": "cdb"})
        assert "Model resumed successfully" in result.content[0].text
        result = await client.call_tool("open_results")
        assert "Entered POST1 using the current jobname results file" in result.content[0].text
        assert sink.events[-2:] == [("run", "CDREAD,db,model,cdb,,,"), ("run", "/POST1")]
        sink.events.clear()
        for command in ("\u00a0FINISH\u00a0", "\u2003'/TITLE'\u2003,ordinary"):
            await client.call_tool("run_mapdl_command", {"cmd": command})
            assert sink.events == [("run", command)]
            sink.events.clear()
        allowed = await client.call_tool(
            "run_multiple_mapdl_commands",
            {"commands": ["\u00a0FINISH\u00a0", "\u2003'/TITLE'\u2003,ordinary"]},
        )
        assert allowed.structured_content["success"] is True
        assert sink.events == [("batch", ["FINISH", "'/TITLE'\u2003,ordinary"])]


@pytest.mark.unit
@pytest.mark.parametrize(
    "command",
    [
        "/COM,'quoted$/SYS,unused'",
        '/TITLE,"quoted$/SYP,unused"',
        "/COM,'quoted!/INP,missing'$/SYS,unused",
        "*SET,APDLPROBE,'left!right'",
        "*SET,APDLPROBE,'left$right'",
        '*SET,APDLPROBE,"left!right"',
        "/COM,'doubled''$/COM,ordinary'",
        "/COM,'backslash\\'$/COM,ordinary'",
        "'/TITLE',ordinary$FINISH",
        '"/TITLE",ordinary!comment',
    ],
)
def test_unverified_quoted_delimiters_fail_closed(restricted_context, command):
    context, sink = restricted_context
    with pytest.raises(ValueError, match="APDL request denied"):
        tools.run_mapdl_command(context, command)
    result = tools.run_multiple_mapdl_commands(context, ["FINISH", command])
    assert "APDL request denied" in result.content[0].text
    assert sink.events == []
    tools.run_mapdl_command(context, "/TITLE,'A quoted title without delimiters'")
    assert sink.events == [("run", "/TITLE,'A quoted title without delimiters'")]


@pytest.mark.unit
@pytest.mark.parametrize(
    "command",
    [
        "FINISH ! /SYS,unused$/SYP,unused",
        "! '/INPUT,missing'$\"/SYS,unused\"",
        "/COM,ordinary ! /SYS,unused\r\nFINISH",
        "/COM,/SYS is mentioned as data",
        "/SY,unknown-short-command",
        "/SYX,unknown-command",
        "/IN,unknown-short-command",
        "*USE,ordinary_macro",
        "CDREAD,DB,ordinary_model,CDB",
        "'/TITLE',ordinary",
        '"/TITLE",ordinary',
        "/TI TLE,ordinary",
        "/TI\tTLE,ordinary",
        "FI NISH",
        "FI\tNISH",
        "'/TITLE',/SYS is argument data",
        "'/IN',unknown-short-command",
        "\u00a0FINISH\u00a0",
        "\u2003FINISH\u2003",
        "\u00a0'/TITLE'\u00a0,ordinary",
        '\u2003"/TITLE"\u2003,ordinary',
        "/TITLE,ordinary\u00a0title\u2003argument",
    ],
)
def test_actual_comments_data_and_indirect_commands_remain_allowed(restricted_context, command):
    context, sink = restricted_context
    tools.run_mapdl_command(context, command)
    assert sink.events == [("run", command)]
    sink.events.clear()
    result = tools.run_multiple_mapdl_commands(context, [command, "FINISH"])
    assert result.structured_content["success"] is True
    assert sink.events == [("batch", [command.strip(), "FINISH"])]


@pytest.mark.unit
@pytest.mark.parametrize(
    "command",
    ["FINISH\x00/SYS", "FINISH\x0c/SYS", "FINISH\x85/SYS", "\ufeff/SYS", "FINISH\u200b"],
)
def test_ambiguous_command_controls_denied_with_ordinary_control(restricted_context, command):
    context, sink = restricted_context
    with pytest.raises(ValueError, match="unsafe control"):
        tools.run_mapdl_command(context, command)
    assert sink.events == []
    tools.run_mapdl_command(context, "\t FINISH")
    assert sink.events == [("run", "\t FINISH")]


@pytest.mark.unit
def test_family_names_in_effective_com_metadata_are_not_invocations(restricted_context):
    context, sink = restricted_context
    tools.run_mapdl_command(
        context,
        "FINISH",
        header="'/SYS' policy",
        comment="/S YP is blocked\n/I\tNPUT is blocked",
    )
    assert sink.events == [
        ("run", "/COM,# '/SYS' policy"),
        ("run", "/COM,/S YP is blocked"),
        ("run", "/COM,/I\tNPUT is blocked"),
        ("run", "FINISH"),
    ]


@pytest.mark.unit
@pytest.mark.parametrize("command,family", _NORMALIZED_HEADS)
def test_normalized_late_batch_denial_preserves_raw_allowed_heads(
    restricted_context, command, family
):
    context, sink = restricted_context
    result = tools.run_multiple_mapdl_commands(
        context, ["'/TITLE',never issued", "FI NISH", command], header="Header", comment="Comment"
    )
    assert "APDL request denied" in result.content[0].text
    assert family in result.content[0].text
    assert sink.events == []
    result = tools.run_multiple_mapdl_commands(
        context, ["'/TITLE',ordinary", "FI NISH"], header="Header", comment="Comment"
    )
    assert result.structured_content["success"] is True
    assert result.structured_content["commands_executed"] == ["'/TITLE',ordinary", "FI NISH"]
    assert sink.events == [
        ("run", "/COM,# Header"),
        ("run", "/COM,Comment"),
        ("batch", ["'/TITLE',ordinary", "FI NISH"]),
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    "command",
    [
        "'/SYS",
        "\"/SYP'",
        "/'INPUT',missing",
        "'/I N P U T',missing",
        '"/I\tNPUT",missing',
        "'/SYS''",
        "'/TITLE'extra,ordinary",
        "'',ordinary",
        "'/SYS\u00a0'",
        "/S\u00a0YS",
        "/S\u2003YP",
        "/I\u00a0NPUT,missing",
        "FI\u2003NISH",
        "\u00a0'/SYS",
        "\u2003/'INPUT',missing",
    ],
)
def test_malformed_or_unsupported_heads_fail_closed_only_when_restricted(
    restricted_context, command
):
    context, sink = restricted_context
    with pytest.raises(ValueError, match="APDL request denied"):
        tools.run_mapdl_command(context, command, header="Header", comment="Comment")
    result = tools.run_multiple_mapdl_commands(context, ["FINISH", command], header="Header")
    assert "APDL request denied" in result.content[0].text
    assert sink.events == []
    context.request_context.lifespan_context.security_options = _SecurityOptions()
    tools.run_mapdl_command(context, command)
    assert sink.events == [("run", command)]


@pytest.mark.unit
@pytest.mark.parametrize("command,family", _NORMALIZED_HEADS)
def test_normalized_heads_keep_selected_families_independent(restricted_context, command, family):
    context, sink = restricted_context
    context.request_context.lifespan_context.security_options = _SecurityOptions(
        blocked_commands=frozenset({"/SYS", "/SYP", "/INPUT"} - {family})
    )
    tools.run_mapdl_command(context, command)
    assert sink.events == [("run", command)]
    context.request_context.lifespan_context.security_options = _SecurityOptions(
        blocked_commands=frozenset({family})
    )
    with pytest.raises(ValueError, match=family):
        tools.run_mapdl_command(context, command)
    assert sink.events == [("run", command)]
    context.request_context.lifespan_context.security_options = _SecurityOptions()
    result = tools.run_multiple_mapdl_commands(context, [command])
    assert result.structured_content["success"] is True
    assert sink.events == [("run", command), ("batch", [command.strip()])]
