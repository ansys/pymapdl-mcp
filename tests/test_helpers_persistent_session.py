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

"""Tests for helpers related to the persistent Python session."""

from unittest.mock import MagicMock, patch

import pytest

from ansys.mapdl.mcp.helpers import connect_to_mapdl_in_persistent_python


@pytest.mark.unit
class TestConnectToMapdlInPersistentPython:
    def test_no_python_session(self, mock_context):
        setattr(mock_context.request_context.lifespan_context, "python_session", None)
        out = connect_to_mapdl_in_persistent_python(mock_context)
        assert isinstance(out, str)
        assert "persistent Python session was not initialized" in out

    def test_already_connected_returns_message(self, mock_context):
        # Prepare python_session and existing mapdl
        session = MagicMock()
        session.metadata = {"mapdl": MagicMock(_ip="127.0.0.1", _port=50052)}
        mock_context.request_context.lifespan_context.python_session = session

        msg = connect_to_mapdl_in_persistent_python(mock_context)
        assert "Already connected to persistent PyMAPDL session" in msg

    def test_no_mapdl_in_lifespan_context(self, mock_context_no_mapdl):
        session = MagicMock()
        session.metadata = {}
        mock_context_no_mapdl.request_context.lifespan_context.python_session = session

        msg = connect_to_mapdl_in_persistent_python(mock_context_no_mapdl)
        assert "No MAPDL instance available in lifespan context" in msg

    def test_successful_connection_stores_metadata(self, mock_context, mock_mapdl):
        # mock_mapdl fixture gives a MagicMock with _ip and _port via attributes set in conftest
        session = MagicMock()
        session.metadata = {}
        mock_context.request_context.lifespan_context.python_session = session

        with patch("ansys.mapdl.mcp.helpers.logger"):
            out = connect_to_mapdl_in_persistent_python(mock_context)

        # Should return the stored mapdl instance
        assert out is mock_context.request_context.lifespan_context.mapdl
        assert session.metadata["mapdl"] is mock_context.request_context.lifespan_context.mapdl
        # Verify execute was invoked to create connection inside the session
        session.execute.assert_called_once()

    def test_execute_failure_logs_and_falls_back(self, mock_context):
        session = MagicMock()
        session.metadata = {}
        session.execute.side_effect = RuntimeError("boom")
        mock_context.request_context.lifespan_context.python_session = session

        with patch("ansys.mapdl.mcp.helpers.logger"):
            out = connect_to_mapdl_in_persistent_python(mock_context)

        # On failure, function returns whatever is in metadata (likely None)
        assert out is None
