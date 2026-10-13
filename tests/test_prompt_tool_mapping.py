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

"""Prompt-to-tool mapping regression tests (`#118 <https://github.com/ansys/pymapdl-mcp/issues/118>`_).

Issue #118 lists natural-language prompts alongside the MCP tool(s) an AI
agent is expected to call for each one (e.g. "which MAPDL instances are
available?" -> ``list_mapdl_instances``). Fully validating that mapping
requires routing each prompt through a real tool-calling LLM, which this
suite intentionally does **not** do (no LLM API key is available in this
environment/CI). Instead, this module is a deterministic, static substitute
that catches the class of regression that *would* break the LLM's ability
to make the right call, without needing a model in the loop:

1. **Tool-existence drift** -- every tool name referenced by an issue #118
   case must exist in the live registry under that exact name. This is a
   real regression gate: it already caught issue #118's case 7 referencing
   ``run_mapdl_commands`` (does not exist) instead of the actual batch tool
   ``run_multiple_mapdl_commands``.
2. **Visibility-gating correctness** -- cases whose expected tools are
   tagged ``REQUIRES_MAPDL_TAG`` (``check_mapdl_status``,
   ``disconnect_from_mapdl``, ``screenshot``, ``run_multiple_mapdl_commands``)
   are verified two ways:

   a. Pre-connect, they are confirmed hidden from ``tools/list`` using
      FastMCP's in-memory :class:`~fastmcp.Client` against the real ``app``
      (mirrors the pattern used by pymechanical-mcp's
      ``test_e2e_tool_visibility.py``). Only the PyMAPDL SDK boundary
      (``ansys.mapdl.core.Mapdl`` / ``launch_mapdl``) is mocked.
   b. Post-connect, ``connect_to_mapdl``/``launch_mapdl_session`` are
      verified to call ``ctx.enable_components(tags={REQUIRES_MAPDL_TAG})``
      directly against a mocked ``Context`` -- the same pattern already used
      throughout ``test_tools.py``. A round-trip through the in-memory
      ``Client`` (connect, then a second ``list_tools()`` call on the same
      client) was tried first but does not work with the installed fastmcp
      version: it does not preserve MCP session identity across separate
      in-memory ``Client`` round-trips, so the session-scoped visibility
      rule set by ``enable_components`` is never observed by a subsequent
      ``list_tools()`` call on that same client.

**Known gap -- explicitly out of scope for this module:** cases 4 and 5 in
the issue both start from the *same* prompt ("let's start to work with
MAPDL") but expect a *different* second tool call (``launch_mapdl_session``
vs. ``connect_to_mapdl``) depending on whether ``list_mapdl_instances``
reports zero or one running instance. Choosing correctly between those two
always-visible tools is a semantic judgment call that only a real
tool-calling LLM can make -- no static/deterministic check can validate it
without risking a false sense of security (it would only prove our own
matcher works, not that a production agent picks correctly). Those two
cases are marked as explicit ``pytest.skip`` below as a visible
placeholder for future LLM-in-the-loop evaluation once a provider/API key
is available, rather than being silently dropped.
"""

from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

from fastmcp import Client
import pytest

from ansys.mapdl.mcp import contexts, prompts, tools  # noqa: F401  (registers tools/prompts)
from ansys.mapdl.mcp.server import app
from ansys.mapdl.mcp.tools import REQUIRES_MAPDL_TAG


@dataclass
class PromptCase:
    """One prompt -> expected tool-call sequence case from issue #118.

    Parameters
    ----------
    case_id : str
        Short identifier matching the issue's "Case N" heading.
    prompt : str
        The natural-language user prompt from the issue.
    tools_executed : list[str]
        Expected ordered sequence of tool names an agent should call.
    notes : str
        Free-form clarification (e.g. naming corrections applied vs. the
        issue's literal text).
    """

    case_id: str
    prompt: str
    tools_executed: list[str] = field(default_factory=list)
    notes: str = ""


# Cases transcribed verbatim from issue #118, except where noted. Case 7's
# ``run_mapdl_commands`` was corrected to the real registered tool name
# ``run_multiple_mapdl_commands`` (see module docstring, point 1).
PROMPT_CASES: list[PromptCase] = [
    PromptCase(
        case_id="case_1_list_instances",
        prompt="which MAPDL instances are available?",
        tools_executed=["list_mapdl_instances"],
    ),
    PromptCase(
        case_id="case_2_status",
        prompt="tell me the status of my MAPDL instance",
        tools_executed=["connect_to_mapdl", "check_mapdl_status"],
    ),
    PromptCase(
        case_id="case_3_disconnect",
        prompt="I am done with the session",
        tools_executed=["disconnect_from_mapdl"],
    ),
    PromptCase(
        case_id="case_4_start_no_instance",
        prompt="let's start to work with MAPDL",
        tools_executed=["list_mapdl_instances", "launch_mapdl_session"],
        notes="Branch: no MAPDL instance running. Semantic-only; see module docstring.",
    ),
    PromptCase(
        case_id="case_5_start_with_instance",
        prompt="let's start to work with MAPDL",
        tools_executed=["list_mapdl_instances", "connect_to_mapdl"],
        notes="Branch: an MAPDL instance IS running. Semantic-only; see module docstring.",
    ),
    PromptCase(
        case_id="case_6_screenshot",
        prompt="Show me the model",
        tools_executed=["screenshot"],
    ),
    PromptCase(
        case_id="case_7_beam_model",
        prompt="Create a simple beam model.",
        tools_executed=[
            "list_mapdl_instances",
            "launch_mapdl_session",
            "run_multiple_mapdl_commands",
            "screenshot",
        ],
        notes=(
            "Issue #118 literally names 'run_mapdl_commands', which does not exist. "
            "Corrected to the real batch-execution tool 'run_multiple_mapdl_commands'."
        ),
    ),
    PromptCase(
        case_id="case_8_check_installed",
        prompt="Tell me which MAPDL versions I have available",
        tools_executed=["check_mapdl_installed"],
    ),
]

# Cases whose expected branch cannot be verified without a real tool-calling
# LLM (see module docstring).
_SEMANTIC_ONLY_CASE_IDS = {"case_4_start_no_instance", "case_5_start_with_instance"}


@pytest.fixture(autouse=True)
def _isolated_app_tag_state():
    """Reset global ``app`` tag-visibility state before and after each test.

    ``app`` is a module-level singleton (same instance ``launcher()`` mutates
    via ``app.disable``/``app.enable``). Without this, a test that disables a
    tag could leak that state into unrelated test modules run later in the
    same session -- which is exactly what happens today: ``test_main.py``'s
    ``test_mapdl_args_work_with_http`` calls the real ``launcher()`` with
    ``--connect-on-startup``, which calls the real (unmocked)
    ``app.disable(tags={"locked_connection"})`` and never restores it. That
    permanently hides ``connect_to_mapdl``/``launch_mapdl_session`` from
    ``tools/list`` for every test running afterward in the same session. This
    fixture resets every tag this module cares about, so these tests pass
    regardless of execution order / prior leakage from other modules.
    """
    app.enable(tags={REQUIRES_MAPDL_TAG, "locked_connection", "aali"})
    yield
    app.enable(tags={REQUIRES_MAPDL_TAG, "locked_connection", "aali"})


def _mock_mapdl_instance() -> MagicMock:
    mapdl = MagicMock()
    mapdl.version = "2024 R2"
    mapdl.directory = "/tmp"
    mapdl._ip = "127.0.0.1"
    mapdl._port = 50052
    mapdl.ip = "127.0.0.1"
    mapdl.port = 50052
    mapdl._exited = False
    mapdl._exiting = False
    return mapdl


@pytest.mark.unit
class TestToolExistence:
    """Every tool referenced by an issue #118 case must exist under that exact name."""

    @pytest.mark.parametrize(
        "case",
        PROMPT_CASES,
        ids=[c.case_id for c in PROMPT_CASES],
    )
    @pytest.mark.asyncio
    async def test_expected_tools_are_registered(self, case: PromptCase):
        """All tools in ``tools_executed`` exist in the full (unfiltered) registry."""
        registered_names = {
            key.split(":", 1)[1].split("@", 1)[0]
            for key in app.local_provider._components
            if key.startswith("tool:")
        }

        missing = [name for name in case.tools_executed if name not in registered_names]
        assert not missing, (
            f"{case.case_id}: tool(s) {missing} referenced by the prompt "
            f"'{case.prompt}' are not registered on the MCP server. "
            f"Registered tools: {sorted(registered_names)}"
        )


@pytest.mark.unit
class TestVisibilityGating:
    """Tools gated by REQUIRES_MAPDL_TAG must be hidden pre-connect, visible post-connect."""

    @pytest.mark.asyncio
    async def test_gated_tools_hidden_before_any_connection(self):
        """Mirrors launcher()'s default startup: REQUIRES_MAPDL_TAG tools are hidden."""
        app.disable(tags={REQUIRES_MAPDL_TAG})

        gated_tools_in_cases = {
            name
            for case in PROMPT_CASES
            for name in case.tools_executed
            if name
            in {
                "check_mapdl_status",
                "disconnect_from_mapdl",
                "screenshot",
                "run_multiple_mapdl_commands",
            }
        }

        async with Client(app) as client:
            visible = {t.name for t in await client.list_tools()}

        for name in gated_tools_in_cases:
            assert name not in visible, (
                f"'{name}' is tagged {REQUIRES_MAPDL_TAG} and must be hidden "
                "before a MAPDL connection is established."
            )

        # Always-visible session-management tools used to establish a connection
        # must still be present so the agent has a path forward.
        assert "list_mapdl_instances" in visible
        assert "connect_to_mapdl" in visible
        assert "launch_mapdl_session" in visible
        assert "check_mapdl_installed" in visible

    @pytest.mark.asyncio
    async def test_connect_to_mapdl_enables_gated_tools(self, mock_context_no_mapdl):
        """connect_to_mapdl must request REQUIRES_MAPDL_TAG be re-enabled for the session.

        Note: this asserts the *mechanism* (``ctx.enable_components(tags=...)`` is
        called with the right tag) directly against a mocked ``Context``, the same
        pattern ``test_tools.py`` already uses. A round-trip through FastMCP's
        in-memory ``Client`` (connect, then a second ``list_tools()`` call) cannot
        be used here: the installed fastmcp version does not preserve MCP session
        identity across separate in-memory ``Client`` round-trips, so the
        session-scoped visibility rule set by ``enable_components`` would not be
        observed by a subsequent ``list_tools()`` on the same client.
        """
        from ansys.mapdl.mcp.tools import connect_to_mapdl

        mock_mapdl = _mock_mapdl_instance()
        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl):
            result = await connect_to_mapdl(mock_context_no_mapdl)

        assert "Successfully connected to MAPDL" in result.content[0].text
        mock_context_no_mapdl.enable_components.assert_called_once_with(tags={REQUIRES_MAPDL_TAG})

    @pytest.mark.asyncio
    async def test_launch_mapdl_session_enables_gated_tools(self, mock_context_no_mapdl):
        """launch_mapdl_session must request REQUIRES_MAPDL_TAG be re-enabled for the session."""
        from ansys.mapdl.mcp.tools import launch_mapdl_session

        mock_mapdl = _mock_mapdl_instance()
        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl):
            result = await launch_mapdl_session(mock_context_no_mapdl)

        assert "Successfully launched MAPDL" in result.content[0].text
        mock_context_no_mapdl.enable_components.assert_called_once_with(tags={REQUIRES_MAPDL_TAG})


@pytest.mark.unit
@pytest.mark.parametrize(
    "case",
    PROMPT_CASES,
    ids=[c.case_id for c in PROMPT_CASES],
)
def test_case_marked_semantic_only_if_applicable(case: PromptCase):
    """Placeholder acknowledging cases 4/5 require a real LLM to disambiguate.

    This test always passes; it exists purely so the semantic-only cases show
    up (via ``-v``/``-rs``) as a documented, visible gap rather than being
    silently absent from the suite. See module docstring for rationale.
    """
    if case.case_id in _SEMANTIC_ONLY_CASE_IDS:
        pytest.skip(
            f"{case.case_id}: branch disambiguation requires a real tool-calling "
            "LLM (no API key available). See module docstring."
        )
    assert case.tools_executed, f"{case.case_id} must declare at least one expected tool."
