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

"""Tests for test utility functions."""

import pytest
from test_utils import adapt_code_for_execution, extract_executable_code, get_llm_context


@pytest.mark.unit
class TestCodeExtraction:
    """Tests for code extraction from LLM responses."""

    def test_extract_markdown_code_block(self):
        """Test extraction from markdown code block."""
        response = """Here's the Python code you need:

```python
from ansys.mapdl.core import launch_mapdl
mapdl = launch_mapdl()
mapdl.k(1, 0, 0, 0)
```

This creates a keypoint at the origin."""

        code = extract_executable_code(response)
        assert "mapdl.k(1, 0, 0, 0)" in code
        assert "from ansys.mapdl.core import launch_mapdl" in code

    def test_extract_plain_code_block(self):
        """Test extraction from plain code block (no markdown markers)."""
        response = """```
mapdl.k(1, 0, 0, 0)
mapdl.k(2, 1, 0, 0)
```"""

        code = extract_executable_code(response)
        assert "mapdl.k(1, 0, 0, 0)" in code
        assert "mapdl.k(2, 1, 0, 0)" in code

    def test_extract_invalid_code_raises_error(self):
        """Test that invalid Python code raises ValueError."""
        response = """
```python
this is not valid python )))
```
"""

        with pytest.raises(ValueError, match="Could not extract valid Python code"):
            extract_executable_code(response)

    def test_extract_from_preamble_with_code(self):
        """Test extraction when code follows descriptive text."""
        response = """To create keypoints, use:

from ansys.mapdl.core import launch_mapdl
mapdl = launch_mapdl()
mapdl.prep7()
mapdl.k(1, 0, 0, 0)
"""

        code = extract_executable_code(response)
        assert "mapdl.k(1, 0, 0, 0)" in code

    def test_extract_empty_response_raises_error(self):
        """Test that empty response raises ValueError."""
        with pytest.raises(ValueError):
            extract_executable_code("")

    def test_extract_no_code_raises_error(self):
        """Test that response with no code raises ValueError."""
        with pytest.raises(ValueError):
            extract_executable_code("This response has no code in it.")


@pytest.mark.unit
class TestCodeAdaptation:
    """Tests for code adaptation for test execution."""

    def test_remove_mapdl_launch(self):
        """Test that MAPDL launch is commented out."""
        code = """
from ansys.mapdl.core import launch_mapdl
mapdl = launch_mapdl()
mapdl.k(1, 0, 0, 0)
"""

        adapted = adapt_code_for_execution(code)
        assert "# from ansys.mapdl.core" in adapted
        assert "# mapdl = launch_mapdl" in adapted
        assert "mapdl.k(1, 0, 0, 0)" in adapted

    def test_remove_mapdl_exit(self):
        """Test that MAPDL exit is commented out."""
        code = """
mapdl.k(1, 0, 0, 0)
mapdl.exit()
"""

        adapted = adapt_code_for_execution(code)
        assert "# mapdl.exit()" in adapted
        assert "mapdl.k(1, 0, 0, 0)" in adapted

    def test_remove_ansys_imports(self):
        """Test that ansys package imports are commented out."""
        code = """
from ansys.mapdl.core import launch_mapdl
import ansys.mapdl.core as mapdl_core
from ansys.mapdl.core.launcher import launch_mapdl as lm
mapdl.k(1, 0, 0, 0)
"""

        adapted = adapt_code_for_execution(code)
        assert "# from ansys.mapdl.core import" in adapted
        assert "# import ansys.mapdl.core" in adapted
        assert "# from ansys.mapdl.core.launcher import" in adapted
        assert "mapdl.k(1, 0, 0, 0)" in adapted

    def test_keep_other_imports(self):
        """Test that non-ansys imports are preserved."""
        code = """
import numpy as np
from matplotlib import pyplot as plt
mapdl.k(1, 0, 0, 0)
"""

        adapted = adapt_code_for_execution(code)
        assert "import numpy as np" in adapted
        assert "from matplotlib import pyplot as plt" in adapted

    def test_preserve_actual_code(self):
        """Test that actual MAPDL commands are preserved."""
        code = """
mapdl.prep7()
mapdl.k(1, 0, 0, 0)
mapdl.k(2, 1, 0, 0)
mapdl.l(1, 2)
mapdl.mesh.esize(0.1)
"""

        adapted = adapt_code_for_execution(code)
        assert "mapdl.prep7()" in adapted
        assert "mapdl.k(1, 0, 0, 0)" in adapted
        assert "mapdl.k(2, 1, 0, 0)" in adapted
        assert "mapdl.l(1, 2)" in adapted
        assert "mapdl.mesh.esize(0.1)" in adapted


@pytest.mark.unit
class TestLLMContext:
    """Tests for LLM context generation."""

    def test_get_llm_context_returns_tuple(self):
        """Test that get_llm_context returns correct structure."""
        prompt, tools = get_llm_context()
        assert isinstance(prompt, str)
        assert isinstance(tools, list)
        assert len(prompt) > 0

    def test_get_llm_context_contains_simulation_workflow(self):
        """Test that prompt contains simulation workflow guidance."""
        prompt, _ = get_llm_context()
        assert "Simulation Workflow" in prompt
        assert "PREP7" in prompt or "/PREP7" in prompt
        assert "SOLU" in prompt or "/SOLU" in prompt
