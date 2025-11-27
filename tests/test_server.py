"""Unit tests for PyMAPDLMCPServer."""

import pytest
from unittest.mock import Mock, patch
from ansys.mapdl.mcp.server import PyMAPDLMCPServer
from ansys.mapdl.mcp.context import PyMAPDLContext
from ansys.common.mcp.helpers import PersistentPythonSession


@pytest.mark.unit
class TestPyMAPDLMCPServer:
    """Test PyMAPDLMCPServer functionality."""

    def test_server_initialization(self):
        """Test that PyMAPDLMCPServer can be initialized."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        assert server is not None
        assert hasattr(server, 'create_context')
        assert hasattr(server, 'product_startup')
        assert hasattr(server, 'product_cleanup')

    def test_create_context_returns_pymapdl_context(self):
        """Test that create_context returns a PyMAPDLContext instance."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        with patch.object(PersistentPythonSession, '__init__', return_value=None):
            with patch.object(PersistentPythonSession, 'is_running', return_value=True):
                context = server.create_context()
        
        assert isinstance(context, PyMAPDLContext)
        assert hasattr(context, 'python_session')
        assert hasattr(context, 'command_history')
        assert context.command_history == []

    def test_create_context_initializes_python_session(self):
        """Test that create_context initializes PersistentPythonSession with startup code."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        with patch.object(PersistentPythonSession, '__init__', return_value=None) as mock_init:
            with patch.object(PersistentPythonSession, 'is_running', return_value=True):
                context = server.create_context()
            
            # Verify PersistentPythonSession was initialized with startup code
            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args.kwargs
            
            assert 'startup_code' in call_kwargs
            startup_code = call_kwargs['startup_code']
            
            # Verify startup code contains expected configurations
            assert 'matplotlib' in startup_code
            assert 'Agg' in startup_code
            assert 'pyvista' in startup_code
            assert 'OFF_SCREEN' in startup_code
            assert 'save_plot' in startup_code
            assert 'save_matplotlib_plot' in startup_code

    def test_startup_code_contains_matplotlib_configuration(self):
        """Test that startup code properly configures matplotlib."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        with patch.object(PersistentPythonSession, '__init__', return_value=None) as mock_init:
            with patch.object(PersistentPythonSession, 'is_running', return_value=True):
                server.create_context()
            
            startup_code = mock_init.call_args.kwargs['startup_code']
            
            # Check for matplotlib Agg backend
            assert "matplotlib.use('Agg')" in startup_code
            assert 'import matplotlib.pyplot as plt' in startup_code

    def test_startup_code_contains_pyvista_configuration(self):
        """Test that startup code properly configures PyVista."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        with patch.object(PersistentPythonSession, '__init__', return_value=None) as mock_init:
            with patch.object(PersistentPythonSession, 'is_running', return_value=True):
                server.create_context()
            
            startup_code = mock_init.call_args.kwargs['startup_code']
            
            # Check for PyVista configuration
            assert 'import pyvista as pv' in startup_code
            assert 'pv.OFF_SCREEN = True' in startup_code
            assert "pv.set_plot_theme('document')" in startup_code

    def test_startup_code_contains_helper_functions(self):
        """Test that startup code includes helper plotting functions."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        with patch.object(PersistentPythonSession, '__init__', return_value=None) as mock_init:
            with patch.object(PersistentPythonSession, 'is_running', return_value=True):
                server.create_context()
            
            startup_code = mock_init.call_args.kwargs['startup_code']
            
            # Check for helper functions
            assert 'def save_plot(' in startup_code
            assert 'def save_matplotlib_plot(' in startup_code
            assert 'import base64' in startup_code
            assert 'from io import BytesIO' in startup_code
            assert 'from PIL import Image' in startup_code

    def test_product_startup_exists(self):
        """Test that product_startup method exists and is callable."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        # Should not raise any exceptions
        server.product_startup()

    def test_product_cleanup_exists(self):
        """Test that product_cleanup method exists and is callable."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        # Should not raise any exceptions
        server.product_cleanup()

    def test_product_cleanup_handles_no_context(self):
        """Test that product_cleanup handles missing context gracefully."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        # Should not raise any exceptions even without context
        server.product_cleanup()

    def test_product_cleanup_exits_mapdl_if_present(self):
        """Test that product_cleanup exits MAPDL if it exists."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        # Create a mock context with a MAPDL instance
        mock_mapdl = Mock()
        mock_mapdl.exit = Mock()
        
        server.context = Mock()
        server.context.mapdl = mock_mapdl
        
        # Call cleanup
        server.product_cleanup()
        
        # Verify exit was called
        mock_mapdl.exit.assert_called_once()

    def test_product_cleanup_handles_mapdl_exit_error(self):
        """Test that product_cleanup handles errors during MAPDL exit gracefully."""
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        
        # Create a mock context with a MAPDL that raises on exit
        mock_mapdl = Mock()
        mock_mapdl.exit.side_effect = Exception("Connection lost")
        
        server.context = Mock()
        server.context.mapdl = mock_mapdl
        
        # Should not raise - should handle exception gracefully
        server.product_cleanup()

    def test_server_inherits_from_base(self):
        """Test that PyMAPDLMCPServer inherits from PyAnsysBaseMCP."""
        from ansys.common.mcp.server import PyAnsysBaseMCP
        
        server = PyMAPDLMCPServer(name="test-pymapdl-mcp")
        assert isinstance(server, PyAnsysBaseMCP)
