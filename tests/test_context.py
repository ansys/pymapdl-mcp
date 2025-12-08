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

    def test_context_dataclass_fields(self, mock_python_session):
        """Test that PyMAPDLContext has all expected dataclass fields."""
        from dataclasses import fields
        
        context = PyMAPDLContext(
            python_session=mock_python_session,
            command_history=[],
        )
        
        field_names = {f.name for f in fields(context)}
        
        # Check inherited fields from PyAnsysBaseAppContext
        assert 'python_session' in field_names
        assert 'command_history' in field_names
        assert 'metadata' in field_names

    def test_context_with_all_parameters(self, mock_python_session):
        """Test creating context with all parameters."""
        context = PyMAPDLContext(
            python_session=mock_python_session,
            command_history=["mapdl.prep7()"],
            metadata={"test_key": "test_value"}
        )
        
        assert context.python_session == mock_python_session
        assert len(context.command_history) == 1
        assert context.command_history[0] == "mapdl.prep7()"
        assert context.metadata["test_key"] == "test_value"

    def test_context_default_values(self, mock_python_session):
        """Test that context has proper default values."""
        context = PyMAPDLContext(
            python_session=mock_python_session,
        )
        
        # Should have default empty list for command_history
        assert hasattr(context, 'command_history')
        # Should have default empty dict for metadata
        assert hasattr(context, 'metadata')

    def test_context_python_session_property(self, mock_python_session):
        """Test that python_session is properly stored and accessible."""
        context = PyMAPDLContext(
            python_session=mock_python_session,
            command_history=[],
        )
        
        assert context.python_session is not None
        assert context.python_session == mock_python_session
        
        # Test that we can interact with the session
        mock_python_session.is_running.return_value = True
        assert context.python_session.is_running()

    def test_context_immutability_after_creation(self, mock_python_session):
        """Test context behavior after creation."""
        context = PyMAPDLContext(
            python_session=mock_python_session,
            command_history=[],
        )
        
        # Command history should be mutable (it's a list)
        original_history = context.command_history
        context.command_history.append("new_command")
        assert len(context.command_history) == 1
        assert context.command_history is original_history

    def test_context_repr(self, mock_python_session):
        """Test that context has a proper string representation."""
        context = PyMAPDLContext(
            python_session=mock_python_session,
            command_history=["test_command"],
        )
        
        repr_str = repr(context)
        assert "PyMAPDLContext" in repr_str

    def test_context_equality(self, mock_python_session):
        """Test context equality comparison."""
        from unittest.mock import Mock
        
        session1 = Mock()
        session2 = Mock()
        
        context1 = PyMAPDLContext(
            python_session=session1,
            command_history=["cmd1"],
        )
        
        context2 = PyMAPDLContext(
            python_session=session1,
            command_history=["cmd1"],
        )
        
        context3 = PyMAPDLContext(
            python_session=session2,
            command_history=["cmd1"],
        )
        
        # Same session and history should be equal
        assert context1 == context2
        # Different session should not be equal
        assert context1 != context3
