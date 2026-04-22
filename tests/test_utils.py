# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: ANSYS MCP SERVER TECHNOLOGY PREVIEW LICENSE AGREEMENT

#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Utility functions for MAPDL code generation tests."""

import ast
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_executable_code(response: str) -> str:
    """Extract executable Python code from LLM response.

    This function attempts to extract Python code from an LLM response,
    handling various formats including markdown code blocks and raw code.
    It performs sanity checks to ensure the extracted code is valid.

    Parameters
    ----------
    response : str
        The LLM response text potentially containing Python code.

    Returns
    -------
    str
        The extracted Python code.

    Raises
    ------
    ValueError
        If no valid Python code can be extracted from the response.
    """
    original_response = response
    code = response

    # Try to extract from markdown code block first
    code_block_match = re.search(r"```(?:python)?\s*\n(.*?)\n```", response, re.DOTALL)
    if code_block_match:
        code = code_block_match.group(1)
        logger.debug(f"Extracted code from markdown block:\n{code}")
    else:
        # Try to find Python code block by looking for common patterns
        lines = response.split("\n")
        code_lines = []
        in_code = False

        for line in lines:
            # Look for lines that start with common Python patterns
            if re.match(r"^\s*(from|import|class|def|if|for|while|try)", line):
                in_code = True
            if in_code:
                code_lines.append(line)

        if code_lines:
            code = "\n".join(code_lines)
            logger.debug(f"Extracted code from pattern matching:\n{code}")

    # Validate that extracted code is syntactically correct Python
    try:
        ast.parse(code)
    except SyntaxError as e:
        logger.error(f"Extracted code is not valid Python:\n{code}\nError: {e}")
        raise ValueError(
            f"Could not extract valid Python code from LLM response. "
            f"Syntax error: {e}\nResponse:\n{original_response}"
        ) from e

    return code


def adapt_code_for_execution(code: str) -> str:
    """Adapt generated code for safe execution in tests.

    Removes or comments out lines that should not be executed in test context:
    - MAPDL launch/initialization (we provide our own instance)
    - Process exit calls
    - Ansys module imports (we provide imports)

    Parameters
    ----------
    code : str
        The generated code to adapt.

    Returns
    -------
    str
        The adapted code safe for test execution.
    """
    lines = []
    for line in code.splitlines():
        stripped = line.strip()

        # Skip or comment out imports from ansys packages
        if stripped.startswith("from ansys.mapdl"):
            lines.append(f"# {line}")
            continue

        if stripped.startswith("import ansys.mapdl"):
            lines.append(f"# {line}")
            continue

        # Skip MAPDL launch commands
        if "launch_mapdl(" in stripped:
            lines.append(f"# {line}")
            continue

        # Skip MAPDL exit commands
        if "mapdl.exit()" in stripped:
            lines.append(f"# {line}")
            continue

        # Keep everything else
        lines.append(line)

    adapted = "\n".join(lines)
    logger.debug(f"Adapted code for execution:\n{adapted}")
    return adapted


def get_llm_context() -> tuple[str, list[dict[str, Any]]]:
    """Get the LLM system prompt and MCP tool descriptions.

    Returns the exact context that would be sent to an LLM when using
    the PyMAPDL MCP server.

    Returns
    -------
    tuple[str, list[dict[str, Any]]]
        A tuple of (system_prompt, tool_descriptions) where:
        - system_prompt: The PYMAPDL_SYSTEM_PROMPT from prompts.py
        - tool_descriptions: List of tool definitions as dicts with
                            name, description, inputSchema, etc.

    Notes
    -----
    This function imports from the actual MCP server implementation
    to ensure test context matches production context.
    """
    try:
        from ansys.mapdl.mcp.prompts import system_prompt

        # Get the system prompt
        prompt = system_prompt()
    except ImportError:
        # Fallback for when running tests without full package installed
        logger.warning("Could not import system_prompt from ansys.mapdl.mcp.prompts")
        prompt = _get_fallback_prompt()

    # TODO(#000): Implement dynamic tool description gathering from MCP server
    # For now, we'll return just the prompt; tools will be added when
    # MCP server integration is clearer

    tool_descriptions = []

    return prompt, tool_descriptions


def _get_fallback_prompt() -> str:
    """Return fallback system prompt when imports fail.

    This is used for testing in isolation without the full package installed.
    """
    return """\
You are an expert Ansys MAPDL simulation assistant powered by PyMAPDL. \
You help engineers build, solve, and post-process finite element models \
covering structural, thermal, electromagnetic, and coupled-field simulations.

## Simulation Workflow

When generating PyMAPDL or MAPDL workflows, ALWAYS follow this process in \
order, regardless of analysis type (static, modal, thermal, nonlinear, etc.). \
MAPDL is structured within processors — each step MUST be executed in \
sequence:

1. **Preprocessing — /PREP7**: Geometry → Element types → Materials → \
Mesh → Boundary conditions & loads.
2. **Solution — /SOLU**: Analysis type, solver options, solve.
3. **Postprocessing — /POST1 or /POST26**: Extract results, visualize, \
verify convergence.

## Disambiguation Defaults

When the user query is ambiguous or lacks details, apply these defaults:
- **Geometry**: Assume 3D and simple shapes (boxes, cylinders, spheres) \
unless the user specifies 2D or mentions PLANE elements.
- **Materials**: Assume linear elastic isotropic (steel for structural, \
aluminum for thermal).
- **Units**: Always use SI unless otherwise specified.
- **BEAM elements**: Assume rectangular cross-section unless specified.

## Operational Rules

1. **Connection first** — Verify MAPDL connection before any operation.
2. **Call get_guidelines_for_* tools before writing code** — These \
tools provide APDL command references, element type tables, and code \
examples. Call the relevant ones before generating any simulation workflow.
3. **Prefer PyMAPDL methods** — Use mapdl.method() over \
mapdl.run("COMMAND") unless the user requests raw APDL.
4. **Comment every section** — Use mapdl.com("description") to \
document each workflow step.
5. **DO NOT invent** methods, function calls, or commands that do not \
exist in PyMAPDL or MAPDL.
6. **Error recovery** — On failure, check MAPDL status, verify the \
current processor, and review output messages.
7. **Best practices** — Use parameters for adjustable values, save the \
database regularly, check mesh quality before solving, verify BCs \
prevent rigid body motion, and compare with analytical solutions \
when possible.
"""
