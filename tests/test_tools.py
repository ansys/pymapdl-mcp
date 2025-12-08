"""Unit tests for MCP tools.

These tests directly test the tool implementation logic by simulating
the MCP decorator behavior and mocking the get_context dependency injection.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call


@pytest.mark.unit
class TestExecutePythonCodeTool:
    """Test execute_python_code tool."""

    def test_execute_success(self, mock_context, mock_get_context):
        """Test successful code execution."""
        mock_context.python_session.execute.return_value = {
            "success": True,
            "stdout": "Code executed successfully",
            "stderr": "",
        }
        
        # Import and test the tool function logic directly
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            # Create a mock MCP server to register tools
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            
            # Register tools
            tools.register_tools(mock_mcp)
            
            # Get and call the execute_python_code function
            execute_fn = registered_tools['execute_python_code']
            result = execute_fn(code="print('Hello')", timeout=30.0)
            
            assert "Code executed successfully" in result
            assert len(mock_context.command_history) == 1
            assert mock_context.command_history[0] == "print('Hello')"

    def test_execute_with_stderr(self, mock_context, mock_get_context):
        """Test code execution with stderr output."""
        mock_context.python_session.execute.return_value = {
            "success": True,
            "stdout": "Result: 42",
            "stderr": "Warning: deprecated function",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            execute_fn = registered_tools['execute_python_code']
            result = execute_fn(code="deprecated_fn()", timeout=30.0)
            
            assert "Result: 42" in result
            assert "Warning: deprecated function" in result

    def test_execute_with_error(self, mock_context, mock_get_context):
        """Test code execution with error."""
        mock_context.python_session.execute.return_value = {
            "success": False,
            "stdout": "",
            "stderr": "NameError: name 'undefined_var' is not defined",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            execute_fn = registered_tools['execute_python_code']
            result = execute_fn(code="print(undefined_var)", timeout=30.0)
            
            assert "Error" in result
            assert "NameError" in result

    def test_execute_no_python_session(self, mock_context, mock_get_context):
        """Test execution when Python session is not available."""
        mock_context.python_session = None
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            execute_fn = registered_tools['execute_python_code']
            result = execute_fn(code="print('test')")
            
            assert "No Python session available" in result

    def test_execute_with_connection_error_and_recovery(self, mock_context, mock_get_context):
        """Test code execution with MAPDL crash and successful recovery."""
        # First execution fails with connection error, second succeeds
        mock_context.python_session.execute.side_effect = [
            {"success": False, "error": "grpc connection error", "stderr": ""},
            {"success": True, "stdout": "Success after recovery", "stderr": ""},
        ]
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context), \
             patch('ansys.mapdl.mcp.helpers.check_mapdl_connection') as mock_check, \
             patch('ansys.mapdl.mcp.helpers.attempt_reconnect_mapdl') as mock_reconnect, \
             patch('ansys.mapdl.mcp.helpers.replay_command_history') as mock_replay:
            
            mock_check.return_value = (False, "Connection lost")
            mock_reconnect.return_value = (True, "Reconnected successfully")
            mock_replay.return_value = (True, "Replayed 0 commands")
            
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            execute_fn = registered_tools['execute_python_code']
            result = execute_fn(code="mapdl.prep7()")
            
            assert "recovered" in result.lower() or "Success after recovery" in result
            mock_check.assert_called_once()
            mock_reconnect.assert_called_once()
            mock_replay.assert_called_once()


@pytest.mark.unit
class TestLaunchNewMAPDLTool:
    """Test launch_new_mapdl tool."""

    def test_launch_success(self, mock_context, mock_get_context):
        """Test successful MAPDL launch."""
        mock_context.python_session.execute.return_value = {
            "success": True, 
            "stdout": "Mapdl\n-----\nPyMAPDL Version: 0.71.1", 
            "stderr": ""
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context), \
             patch('ansys.mapdl.mcp.helpers.check_mapdl_connection', return_value=(False, "Not connected")), \
             patch('ansys.mapdl.mcp.helpers.get_mapdl_instances_from_cli', return_value=[]):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            launch_fn = registered_tools['launch_new_mapdl']
            result = launch_fn(nproc=2)
            
            assert "PyMAPDL Version" in result

    def test_launch_with_custom_params(self, mock_context, mock_get_context):
        """Test MAPDL launch with custom parameters."""
        mock_context.python_session.execute.return_value = {
            "success": True, 
            "stdout": "MAPDL launched", 
            "stderr": ""
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context), \
             patch('ansys.mapdl.mcp.helpers.check_mapdl_connection', return_value=(False, "Not connected")), \
             patch('ansys.mapdl.mcp.helpers.get_mapdl_instances_from_cli', return_value=[]):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            launch_fn = registered_tools['launch_new_mapdl']
            result = launch_fn(
                exec_file="/path/to/mapdl",
                run_location="/tmp/mapdl",
                nproc=4,
                additional_switches="-smp"
            )
            
            # Verify parameters were passed to execute
            call_args = mock_context.python_session.execute.call_args[0][0]
            assert 'nproc=4' in call_args
            assert 'exec_file="/path/to/mapdl"' in call_args

    def test_launch_already_connected(self, mock_context, mock_get_context):
        """Test launch when already connected."""
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context), \
             patch('ansys.mapdl.mcp.helpers.check_mapdl_connection', return_value=(True, "")):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            launch_fn = registered_tools['launch_new_mapdl']
            result = launch_fn()
            
            assert "Already connected" in result

    def test_launch_failure(self, mock_context, mock_get_context):
        """Test MAPDL launch failure."""
        mock_context.python_session.execute.return_value = {
            "success": False, 
            "error": "MAPDL not found", 
            "stderr": ""
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context), \
             patch('ansys.mapdl.mcp.helpers.check_mapdl_connection', return_value=(False, "Not connected")), \
             patch('ansys.mapdl.mcp.helpers.get_mapdl_instances_from_cli', return_value=[]):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            launch_fn = registered_tools['launch_new_mapdl']
            result = launch_fn()
            
            assert "Failed to launch MAPDL" in result
            assert "MAPDL not found" in result

    def test_launch_with_running_instances(self, mock_context, mock_get_context):
        """Test launch when running instances exist."""
        running_instances = [
            {"name": "ANSYS.exe", "is_instance": True, "status": "running", "port": 50052, "pid": 12345},
            {"name": "ANSYS.exe", "is_instance": True, "status": "running", "port": 50053, "pid": 12346},
        ]
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context), \
             patch('ansys.mapdl.mcp.helpers.check_mapdl_connection', return_value=(False, "Not connected")), \
             patch('ansys.mapdl.mcp.helpers.get_mapdl_instances_from_cli', return_value=running_instances):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            launch_fn = registered_tools['launch_new_mapdl']
            result = launch_fn()
            
            assert "Found" in result
            assert "running MAPDL instance" in result
            assert "50052" in result
            assert "connect_to_mapdl" in result


@pytest.mark.unit
class TestConnectToMAPDLTool:
    """Test connect_to_mapdl tool."""

    def test_connect_success(self, mock_context, mock_get_context):
        """Test successful connection to existing MAPDL."""
        mock_context.python_session.execute.return_value = {
            "success": True, 
            "stdout": "Connected to MAPDL at localhost:50052", 
            "stderr": ""
        }
        
        running_instances = [
            {"name": "ANSYS.exe", "is_instance": True, "status": "running", "port": 50052, "pid": 12345}
        ]
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context), \
             patch('ansys.mapdl.mcp.helpers.check_mapdl_connection', return_value=(False, "Not connected")), \
             patch('ansys.mapdl.mcp.helpers.get_mapdl_instances_from_cli', return_value=running_instances):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            connect_fn = registered_tools['connect_to_mapdl']
            result = connect_fn(port=50052, ip="localhost")
            
            assert "Connected" in result
            # Verify connection params are stored
            assert "mapdl_connection_params" in mock_context.metadata
            assert mock_context.metadata["mapdl_connection_params"]["port"] == 50052

    def test_connect_custom_port(self, mock_context, mock_get_context):
        """Test connection with custom port."""
        mock_context.python_session.execute.return_value = {
            "success": True, 
            "stdout": "Connected", 
            "stderr": ""
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context), \
             patch('ansys.mapdl.mcp.helpers.check_mapdl_connection', return_value=(False, "Not connected")), \
             patch('ansys.mapdl.mcp.helpers.get_mapdl_instances_from_cli', return_value=[]):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            connect_fn = registered_tools['connect_to_mapdl']
            result = connect_fn(port=50053, ip="192.168.1.100")
            
            call_args = mock_context.python_session.execute.call_args[0][0]
            assert "port=50053" in call_args
            assert "ip='192.168.1.100'" in call_args

    def test_connect_wrong_port(self, mock_context, mock_get_context):
        """Test connection to port with no running instance."""
        running_instances = [
            {"name": "ANSYS.exe", "is_instance": True, "status": "running", "port": 50052, "pid": 12345},
            {"name": "ANSYS.exe", "is_instance": True, "status": "running", "port": 50053, "pid": 12346},
        ]
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context), \
             patch('ansys.mapdl.mcp.helpers.check_mapdl_connection', return_value=(False, "Not connected")), \
             patch('ansys.mapdl.mcp.helpers.get_mapdl_instances_from_cli', return_value=running_instances):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            connect_fn = registered_tools['connect_to_mapdl']
            result = connect_fn(port=50054, ip="localhost")
            
            assert "No MAPDL instance found running on port 50054" in result
            assert "50052" in result
            assert "50053" in result
            assert "Available MAPDL instances" in result

    def test_connect_already_connected(self, mock_context, mock_get_context):
        """Test connection when already connected."""
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context), \
             patch('ansys.mapdl.mcp.helpers.check_mapdl_connection', return_value=(True, "")):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            connect_fn = registered_tools['connect_to_mapdl']
            result = connect_fn(port=50052, ip="localhost")
            
            assert "Already connected" in result


@pytest.mark.unit
class TestDisconnectFromMAPDLTool:
    """Test disconnect_from_mapdl tool."""

    def test_disconnect_success(self, mock_context, mock_get_context):
        """Test successful disconnection."""
        mock_context.metadata["mapdl_connection_params"] = {"type": "connect", "port": 50052}
        mock_context.python_session.execute.return_value = {
            "success": True,
            "stdout": "",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            disconnect_fn = registered_tools['disconnect_from_mapdl']
            result = disconnect_fn()
            
            assert "Disconnected" in result
            # Verify connection params are cleared
            assert "mapdl_connection_params" not in mock_context.metadata


@pytest.mark.unit
class TestCommandHistoryTools:
    """Test command history management tools."""

    def test_get_command_history_empty(self, mock_context, mock_get_context):
        """Test getting empty command history."""
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            get_history_fn = registered_tools['get_command_history']
            result = get_history_fn()
            
            assert "No commands" in result

    def test_get_command_history_with_commands(self, mock_context, mock_get_context, sample_command_history):
        """Test getting command history with commands."""
        mock_context.command_history = sample_command_history
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            get_history_fn = registered_tools['get_command_history']
            result = get_history_fn()
            
            assert "mapdl.prep7()" in result
            assert "mapdl.et(1, 'SOLID186')" in result
            assert "1:" in result  # Check numbering

    def test_clear_command_history(self, mock_context, mock_get_context, sample_command_history):
        """Test clearing command history."""
        mock_context.command_history = sample_command_history.copy()
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            clear_history_fn = registered_tools['clear_command_history']
            result = clear_history_fn()
            
            assert "cleared" in result
            assert len(mock_context.command_history) == 0

    def test_undo_last_command(self, mock_context, mock_get_context, sample_command_history):
        """Test undoing last command."""
        mock_context.command_history = sample_command_history.copy()
        original_length = len(mock_context.command_history)
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            undo_fn = registered_tools['undo_last_command']
            result = undo_fn()
            
            assert "Undid" in result  # Changed from "Removed"
            assert len(mock_context.command_history) == original_length - 1

    def test_undo_empty_history(self, mock_context, mock_get_context):
        """Test undo with empty history."""
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            undo_fn = registered_tools['undo_last_command']
            result = undo_fn()
            
            assert "No commands" in result


@pytest.mark.unit
class TestRenderPlotTool:
    """Test render_plot tool."""

    def test_render_plot_success(self, mock_context, mock_get_context):
        """Test successful plot rendering to file."""
        mock_context.python_session.execute.return_value = {
            "success": True,
            "stdout": "SAVED: C:\\test\\beam_plot.png",
            "stderr": "",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            render_fn = registered_tools['render_plot']
            result = render_fn(
                plot_code="plotter = mapdl.eplot(return_plotter=True, off_screen=True)",
                filename="beam_plot.png"
            )
            
            assert "Plot saved to" in result
            assert "beam_plot.png" in result

    def test_render_plot_with_custom_directory(self, mock_context, mock_get_context):
        """Test plot rendering with custom save directory."""
        mock_context.python_session.execute.return_value = {
            "success": True,
            "stdout": "SAVED: C:\\custom\\path\\test_plot.png",
            "stderr": "",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            render_fn = registered_tools['render_plot']
            result = render_fn(
                plot_code="plotter = mapdl.nplot(return_plotter=True, off_screen=True)",
                filename="test_plot.png",
                save_directory="C:\\custom\\path"
            )
            
            assert "Plot saved to" in result
            assert "custom\\path" in result or "custom/path" in result

    def test_render_plot_no_plotter_error(self, mock_context, mock_get_context):
        """Test plot rendering with no plotter created."""
        mock_context.python_session.execute.return_value = {
            "success": True,
            "stdout": "Error: No plotter or figure found. Use return_plotter=True or create a matplotlib plot.",
            "stderr": "",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            render_fn = registered_tools['render_plot']
            result = render_fn(
                plot_code="mapdl.eplot()",  # Missing return_plotter=True
                filename="test.png"
            )
            
            assert "Error:" in result
            assert "No plotter" in result

    def test_render_plot_execution_error(self, mock_context, mock_get_context):
        """Test plot rendering with execution error."""
        mock_context.python_session.execute.return_value = {
            "success": False,
            "error": "NameError: name 'mapdl' is not defined",
            "stderr": "",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            render_fn = registered_tools['render_plot']
            result = render_fn(
                plot_code="plotter = mapdl.eplot(return_plotter=True)",
                filename="test.png"
            )
            
            assert "Failed to render plot" in result
            assert "NameError" in result

    def test_render_plot_no_python_session(self, mock_context, mock_get_context):
        """Test plot rendering when Python session is not available."""
        mock_context.python_session = None
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            render_fn = registered_tools['render_plot']
            result = render_fn(
                plot_code="plotter = mapdl.eplot(return_plotter=True)",
                filename="test.png"
            )
            
            assert "Python session is not available" in result

    def test_render_plot_matplotlib(self, mock_context, mock_get_context):
        """Test plot rendering with matplotlib."""
        mock_context.python_session.execute.return_value = {
            "success": True,
            "stdout": "SAVED: C:\\test\\matplotlib_plot.png",
            "stderr": "",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            render_fn = registered_tools['render_plot']
            result = render_fn(
                plot_code="plt.plot([1, 2, 3], [1, 4, 9])",
                filename="matplotlib_plot.png"
            )
            
            assert "Plot saved to" in result
            assert "matplotlib_plot.png" in result

    def test_render_plot_mapdl_plotter(self, mock_context, mock_get_context):
        """Test plot rendering with MAPDL MapdlPlotter using show(savefig=...)."""
        mock_context.python_session.execute.return_value = {
            "success": True,
            "stdout": "SAVED: C:\\test\\mapdl_beam.png",
            "stderr": "",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            render_fn = registered_tools['render_plot']
            result = render_fn(
                plot_code="plotter = mapdl.eplot(return_plotter=True)",
                filename="mapdl_beam.png"
            )
            
            assert "Plot saved to" in result
            assert "mapdl_beam.png" in result

    def test_render_plot_pyvista_plotter(self, mock_context, mock_get_context):
        """Test plot rendering with standard PyVista plotter using screenshot()."""
        mock_context.python_session.execute.return_value = {
            "success": True,
            "stdout": "SAVED: C:\\test\\pyvista_mesh.png",
            "stderr": "",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            render_fn = registered_tools['render_plot']
            result = render_fn(
                plot_code="import pyvista as pv\nplotter = pv.Plotter(off_screen=True)\nplotter.add_mesh(pv.Sphere())",
                filename="pyvista_mesh.png"
            )
            
            assert "Plot saved to" in result
            assert "pyvista_mesh.png" in result

    def test_render_plot_unsupported_plotter_type(self, mock_context, mock_get_context):
        """Test plot rendering with unsupported plotter type showing available methods."""
        mock_context.python_session.execute.return_value = {
            "success": True,
            "stdout": "Error: Plotter type 'CustomPlotter' doesn't have a recognized save method.\nAvailable methods: ['export', 'render']",
            "stderr": "",
        }
        
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            from ansys.mapdl.mcp import tools
            
            mock_mcp = Mock()
            registered_tools = {}
            
            def mock_tool_decorator():
                def decorator(fn):
                    registered_tools[fn.__name__] = fn
                    return fn
                return decorator
            
            mock_mcp.tool = mock_tool_decorator
            tools.register_tools(mock_mcp)
            
            render_fn = registered_tools['render_plot']
            result = render_fn(
                plot_code="plotter = CustomPlotter()",
                filename="test.png"
            )
            
            assert "Error:" in result
            assert "doesn't have a recognized save method" in result
