"""Unit tests for PyMAPDLContext."""

import pytest
from ansys.mapdl.mcp.context import PyMAPDLContext
from ansys.common.mcp.context import PyAnsysBaseAppContext


@pytest.mark.unit
class TestPyMAPDLContext:
    """Test PyMAPDLContext functionality."""

    def test_context_initialization(self, mock_python_session):
        """Test that PyMAPDLContext can be initialized properly."""
        context = PyMAPDLContext(
            python_session=mock_python_session,
            command_history=[],
        )
        
        assert context.python_session == mock_python_session
        assert context.command_history == []
        assert isinstance(context, PyAnsysBaseAppContext)

    def test_context_with_command_history(self, mock_python_session, sample_command_history):
        """Test that PyMAPDLContext properly stores command history."""
        context = PyMAPDLContext(
            python_session=mock_python_session,
            command_history=sample_command_history.copy(),
        )
        
        assert len(context.command_history) == 3
        assert context.command_history == sample_command_history

    def test_context_command_history_mutation(self, mock_python_session):
        """Test that command history can be modified."""
        context = PyMAPDLContext(
            python_session=mock_python_session,
            command_history=[],
        )
        
        # Add commands
        context.command_history.append("mapdl.prep7()")
        context.command_history.append("mapdl.et(1, 'SOLID186')")
        
        assert len(context.command_history) == 2
        assert context.command_history[0] == "mapdl.prep7()"
        
        # Clear commands
        context.command_history.clear()
        assert len(context.command_history) == 0

    def test_context_metadata(self, mock_python_session):
        """Test that context can store metadata."""
        context = PyMAPDLContext(
            python_session=mock_python_session,
            command_history=[],
        )
        
        # Add metadata
        context.metadata["mapdl_connection_params"] = {
            "type": "connect",
            "port": 50052,
            "ip": "localhost"
        }
        
        assert "mapdl_connection_params" in context.metadata
        assert context.metadata["mapdl_connection_params"]["port"] == 50052
        
        # Remove metadata
        del context.metadata["mapdl_connection_params"]
        assert "mapdl_connection_params" not in context.metadata

    def test_context_is_dataclass(self):
        """Test that PyMAPDLContext is a dataclass."""
        from dataclasses import is_dataclass
        assert is_dataclass(PyMAPDLContext)

    def test_context_inheritance(self, mock_python_session):
        """Test that PyMAPDLContext inherits from PyAnsysBaseAppContext."""
        context = PyMAPDLContext(
            python_session=mock_python_session,
            command_history=[],
        )
        
        assert isinstance(context, PyAnsysBaseAppContext)
        assert hasattr(context, 'python_session')
        assert hasattr(context, 'command_history')
        assert hasattr(context, 'metadata')
