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

"""Tests for error handling in PyMAPDL MCP Server."""

from unittest.mock import MagicMock

from fastmcp.tools.base import ToolResult
import pytest

from ansys.mapdl.mcp.tools import check_mapdl_status, run_mapdl_command


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling in various scenarios."""

    def test_mapdl_command_failure(self, mock_context):
        """Test handling of MAPDL command failures."""
        # Make the run method raise an exception
        mock_context.request_context.lifespan_context.mapdl.run.side_effect = RuntimeError(
            "MAPDL command failed"
        )

        with pytest.raises(RuntimeError) as exc_info:
            run_mapdl_command(mock_context, "INVALID_COMMAND")

        assert "MAPDL command failed" in str(exc_info.value)

    def test_none_mapdl_instance(self, mock_context_no_mapdl):
        """Test handling when MAPDL instance is None."""
        # Should return helpful error message instead of raising exception
        result = check_mapdl_status(mock_context_no_mapdl)
        assert isinstance(result, ToolResult)
        assert "No MAPDL connection available" in result.content[0].text

    def test_invalid_context_structure(self):
        """Test handling of invalid context structure."""
        # Create a context with missing mapdl attribute
        invalid_context = MagicMock()
        invalid_context.request_context = MagicMock()
        invalid_context.request_context.lifespan_context = MagicMock()
        invalid_context.request_context.lifespan_context.mapdl = None

        result = check_mapdl_status(invalid_context)
        assert "No MAPDL connection available" in result.content[0].text

    def test_mapdl_timeout(self, mock_context):
        """Test handling of MAPDL timeout scenarios."""
        # Simulate a timeout
        mock_context.request_context.lifespan_context.mapdl.run.side_effect = TimeoutError(
            "MAPDL command timed out"
        )

        with pytest.raises(TimeoutError) as exc_info:
            run_mapdl_command(mock_context, "/SOLVE")

        assert "timed out" in str(exc_info.value)

    def test_empty_command_string(self, mock_context):
        """Test handling of empty command string."""
        # This should not raise an error, but pass empty string to MAPDL
        result = run_mapdl_command(mock_context, "")

        assert "executed successfully" in result.content[0].text
        mock_context.request_context.lifespan_context.mapdl.run.assert_called_once_with("")

    def test_very_long_command(self, mock_context):
        """Test handling of very long commands."""
        # MAPDL has line length limits, but our code should pass it through
        long_command = "COMMENT" + "X" * 1000
        result = run_mapdl_command(mock_context, long_command)

        assert "executed successfully" in result.content[0].text
