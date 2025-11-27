"""Integration tests for PyMAPDL MCP - requires actual MAPDL installation.

These tests are marked with @pytest.mark.integration and will be skipped
unless explicitly run with: pytest -m integration

To run these tests, you need:
1. MAPDL installed and accessible
2. PyMAPDL properly configured
3. Run with: pytest -m integration
"""

import pytest
import os


# Skip all integration tests by default unless MAPDL is available
# Set environment variable RUN_INTEGRATION_TESTS=1 to enable
pytestmark = pytest.mark.integration


def check_mapdl_available():
    """Check if MAPDL is available for testing."""
    try:
        from ansys.mapdl.core import launch_mapdl
        # Try to detect MAPDL installation
        import subprocess
        result = subprocess.run(
            ["pymapdl", "list"],
            capture_output=True,
            timeout=5
        )
        return True
    except:
        return False


@pytest.fixture(scope="module")
def real_mapdl():
    """Launch a real MAPDL instance for testing."""
    if not check_mapdl_available():
        pytest.skip("MAPDL not available")
    
    from ansys.mapdl.core import launch_mapdl
    
    mapdl = launch_mapdl(nproc=2)
    yield mapdl
    
    # Cleanup
    try:
        mapdl.exit()
    except:
        pass


@pytest.fixture
async def mcp_server_with_mapdl():
    """Create MCP server with real MAPDL connection."""
    from ansys.mapdl.mcp.server import PyMAPDLMCPServer
    from ansys.mapdl.mcp.tools import register_tools
    from unittest.mock import Mock, patch
    
    server = PyMAPDLMCPServer(name="test-integration-server")
    register_tools(server)
    
    # Initialize context
    context = server.create_context()
    
    # Start the Python session
    if context.python_session and not context.python_session.is_running():
        context.python_session.start()
    
    # Mock get_context to return our app context
    def mock_get_context():
        mock_ctx = Mock()
        mock_ctx.fastmcp._lifespan_result = context
        return mock_ctx
    
    # Get tools once - get_tools() returns a dict with tool names as keys
    # Each value is a FunctionTool object with a .fn attribute
    tools = await server.get_tools()
    tools_dict = {name: tool.fn for name, tool in tools.items()}
    
    # Patch get_context for all tool calls
    with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
        yield server, context, tools_dict
    
    # Cleanup
    try:
        if context.python_session:
            context.python_session.stop()
    except:
        pass


class TestIntegrationBasicWorkflow:
    """Test basic MAPDL workflow through MCP."""

    @pytest.mark.asyncio
    async def test_launch_and_execute_simple_command(self, mcp_server_with_mapdl):
        """Test launching MAPDL and executing a simple command."""
        server, context, tools_dict = mcp_server_with_mapdl
        
        # Launch MAPDL
        launch_tool = tools_dict["launch_new_mapdl"]
        result = launch_tool(nproc=2)
        assert "PyMAPDL Version" in result or "MAPDL" in result
        
        # Execute simple command
        execute_tool = tools_dict["execute_python_code"]
        result = execute_tool(code="print(mapdl)", timeout=10.0)
        assert "success" in result.lower() or "Mapdl" in result

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, mcp_server_with_mapdl):
        """Test a complete FEA workflow."""
        server, context, tools_dict = mcp_server_with_mapdl
        
        # Get tools
        execute_tool = tools_dict["execute_python_code"]
        history_tool = tools_dict["get_command_history"]
        
        # Clear and start preprocessor
        result = execute_tool(code="mapdl.clear()\nmapdl.prep7()")
        assert "success" in result.lower() or "PREP7" in result
        
        # Define material
        result = execute_tool(code="mapdl.mp('EX', 1, 2e11)")
        assert "error" not in result.lower()
        
        # Define element type
        result = execute_tool(code="mapdl.et(1, 'SOLID186')")
        assert "error" not in result.lower()
        
        # Verify command history
        history = history_tool()
        assert "mapdl.clear()" in history or "mapdl.prep7()" in history

    @pytest.mark.asyncio
    async def test_disconnect_and_reconnect(self, real_mapdl):
        """Test disconnecting and reconnecting to MAPDL."""
        from ansys.mapdl.mcp.server import PyMAPDLMCPServer
        from ansys.mapdl.mcp.tools import register_tools
        from unittest.mock import Mock, patch
        
        server = PyMAPDLMCPServer(name="test-reconnect")
        register_tools(server)
        context = server.create_context()
        
        # Start the Python session
        if context.python_session and not context.python_session.is_running():
            context.python_session.start()
        
        # Mock get_context to return our app context
        def mock_get_context():
            mock_ctx = Mock()
            mock_ctx.fastmcp._lifespan_result = context
            return mock_ctx
        
        # Get tools - get_tools() returns a dict with tool names as keys
        # Each value is a FunctionTool object with a .fn attribute
        tools = await server.get_tools()
        tools_dict = {name: tool.fn for name, tool in tools.items()}
        
        # Patch get_context for all tool calls
        with patch('ansys.mapdl.mcp.tools.get_context', mock_get_context):
            # Connect to existing MAPDL
            connect_tool = tools_dict["connect_to_mapdl"]
            result = connect_tool(port=real_mapdl.port, ip=real_mapdl.ip)
            assert "Mapdl" in result or "MAPDL" in result
            
            # Disconnect
            disconnect_tool = tools_dict["disconnect_from_mapdl"]
            result = disconnect_tool()
            assert "Disconnected" in result or "successfully" in result.lower()


class TestIntegrationCommandHistory:
    """Test command history functionality with real MAPDL."""

    @pytest.mark.asyncio
    async def test_command_history_tracking(self, mcp_server_with_mapdl):
        """Test that commands are properly tracked in history."""
        server, context, tools_dict = mcp_server_with_mapdl
        
        execute_tool = tools_dict["execute_python_code"]
        history_tool = tools_dict["get_command_history"]
        
        # Execute several commands
        execute_tool(code="mapdl.clear()")
        execute_tool(code="mapdl.prep7()")
        execute_tool(code="mapdl.et(1, 'SOLID186')")
        
        # Check history
        history = history_tool()
        assert "mapdl.clear()" in history
        assert "mapdl.prep7()" in history
        assert "mapdl.et(1, 'SOLID186')" in history

    @pytest.mark.asyncio
    async def test_undo_command(self, mcp_server_with_mapdl):
        """Test undoing commands."""
        server, context, tools_dict = mcp_server_with_mapdl
        
        execute_tool = tools_dict["execute_python_code"]
        undo_tool = tools_dict["undo_last_command"]
        history_tool = tools_dict["get_command_history"]
        
        # Execute commands
        execute_tool(code="mapdl.prep7()")
        execute_tool(code="mapdl.et(1, 'SOLID186')")
        
        # Undo last
        result = undo_tool()
        assert "SOLID186" in result
        
        # Verify history
        history = history_tool()
        assert "mapdl.prep7()" in history
        assert "SOLID186" not in history or history.count("SOLID186") == 1

    @pytest.mark.asyncio
    async def test_clear_history(self, mcp_server_with_mapdl):
        """Test clearing command history."""
        server, context, tools_dict = mcp_server_with_mapdl
        
        execute_tool = tools_dict["execute_python_code"]
        clear_tool = tools_dict["clear_command_history"]
        history_tool = tools_dict["get_command_history"]
        
        # Execute commands
        execute_tool(code="mapdl.prep7()")
        execute_tool(code="mapdl.et(1, 'SOLID186')")
        
        # Clear history
        result = clear_tool()
        assert "cleared" in result.lower()
        
        # Verify empty
        history = history_tool()
        assert "No commands" in history


@pytest.mark.slow
class TestIntegrationCrashRecovery:
    """Test MAPDL crash recovery mechanisms.
    
    Note: These tests are marked as slow because they involve
    simulating crashes and recovery, which takes time.
    """

    @pytest.mark.asyncio
    async def test_simulated_connection_loss(self, mcp_server_with_mapdl):
        """Test recovery from simulated connection loss.
        
        This is a placeholder test. Real crash testing would require
        deliberately terminating MAPDL processes, which is complex
        and potentially dangerous in CI environments.
        """
        pytest.skip("Crash recovery testing requires manual setup")


# Run this test only if explicitly requested
@pytest.mark.skipif(
    os.environ.get("RUN_INTEGRATION_TESTS") != "1",
    reason="Integration tests require RUN_INTEGRATION_TESTS=1"
)
class TestIntegrationRealWorld:
    """Real-world integration tests."""

    def test_beam_modal_analysis(self, real_mapdl):
        """Test a complete beam modal analysis workflow."""
        # This would replicate the beam analysis you did earlier
        pytest.skip("Implement if needed for CI/CD validation")
