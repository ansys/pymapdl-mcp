"""Unit tests for helper functions."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ansys.mapdl.mcp.helpers import (
    check_mapdl_connection,
    attempt_reconnect_mapdl,
    replay_command_history,
    get_mapdl_instances_from_cli,
)


@pytest.mark.unit
class TestCheckMAPDLConnection:
    """Test check_mapdl_connection function."""

    def test_check_connection_success(self, mock_python_session):
        """Test successful connection check."""
        mock_python_session.execute.return_value = {
            "success": True,
            "stdout": "MAPDL_CHECK:CONNECTED",
            "stderr": "",
        }
        
        is_connected, error = check_mapdl_connection(mock_python_session)
        
        assert is_connected is True
        assert error == ""

    def test_check_connection_not_connected(self, mock_python_session):
        """Test when MAPDL is not connected."""
        mock_python_session.execute.return_value = {
            "success": True,
            "stdout": "MAPDL_CHECK:NOT_CONNECTED",
            "stderr": "",
        }
        
        is_connected, error = check_mapdl_connection(mock_python_session)
        
        assert is_connected is False
        assert "not connected" in error.lower()

    def test_check_connection_error(self, mock_python_session):
        """Test when connection check encounters an error."""
        mock_python_session.execute.return_value = {
            "success": True,
            "stdout": "MAPDL_CHECK:ERROR:Connection refused",
            "stderr": "",
        }
        
        is_connected, error = check_mapdl_connection(mock_python_session)
        
        assert is_connected is False
        assert "Connection refused" in error

    def test_check_connection_execution_failed(self, mock_python_session):
        """Test when execution itself fails."""
        mock_python_session.execute.return_value = {
            "success": False,
            "error": "Python session timeout",
            "stderr": "",
        }
        
        is_connected, error = check_mapdl_connection(mock_python_session)
        
        assert is_connected is False
        assert "Python session timeout" in error

    def test_check_connection_exception(self, mock_python_session):
        """Test when an exception is raised."""
        mock_python_session.execute.side_effect = Exception("Unexpected error")
        
        is_connected, error = check_mapdl_connection(mock_python_session)
        
        assert is_connected is False
        assert "Exception" in error
        assert "Unexpected error" in error


@pytest.mark.unit
class TestGetMAPDLInstancesFromCLI:
    """Test get_mapdl_instances_from_cli function."""

    @patch('subprocess.run')
    def test_parse_valid_output(self, mock_run):
        """Test parsing valid pymapdl list output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="""Name          Is Instance    Status      gRPC port    PID
------------  -------------  --------  -----------  -----
ANSYS.exe     False          running         50052  28404
MAPDL.exe     True           running         50053  28500
""",
            stderr=""
        )
        
        instances = get_mapdl_instances_from_cli()
        
        assert len(instances) == 2
        assert instances[0]['name'] == 'ANSYS.exe'
        assert instances[0]['is_instance'] is False
        assert instances[0]['status'] == 'running'
        assert instances[0]['port'] == 50052
        assert instances[0]['pid'] == 28404
        
        assert instances[1]['name'] == 'MAPDL.exe'
        assert instances[1]['is_instance'] is True

    @patch('subprocess.run')
    def test_no_instances_found(self, mock_run):
        """Test when no instances are running."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="""Name          Is Instance    Status      gRPC port    PID
------------  -------------  --------  -----------  -----
""",
            stderr=""
        )
        
        instances = get_mapdl_instances_from_cli()
        
        assert len(instances) == 0

    @patch('subprocess.run')
    def test_cli_command_failed(self, mock_run):
        """Test when pymapdl list command fails."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Command not found"
        )
        
        instances = get_mapdl_instances_from_cli()
        
        assert len(instances) == 0

    @patch('subprocess.run')
    def test_cli_timeout(self, mock_run):
        """Test when CLI command times out."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("pymapdl", 10)
        
        instances = get_mapdl_instances_from_cli()
        
        assert len(instances) == 0

    @patch('subprocess.run')
    def test_cli_not_found(self, mock_run):
        """Test when pymapdl CLI is not installed."""
        mock_run.side_effect = FileNotFoundError()
        
        instances = get_mapdl_instances_from_cli()
        
        assert len(instances) == 0


@pytest.mark.unit
class TestAttemptReconnectMAPDL:
    """Test attempt_reconnect_mapdl function."""

    def test_reconnect_with_stored_connect_params_success(self, mock_python_session, mock_context):
        """Test successful reconnection with stored connect parameters."""
        mock_context.metadata["mapdl_connection_params"] = {
            "type": "connect",
            "port": 50052,
            "ip": "localhost"
        }
        
        mock_python_session.execute.return_value = {
            "success": True,
            "stdout": "RECONNECT_SUCCESS:Connected to MAPDL at localhost:50052",
            "stderr": "",
        }
        
        success, message = attempt_reconnect_mapdl(mock_python_session, mock_context)
        
        assert success is True
        assert "RECONNECT_SUCCESS" in message

    def test_reconnect_with_stored_connect_params_failure(self, mock_python_session, mock_context):
        """Test failed reconnection with stored connect parameters."""
        mock_context.metadata["mapdl_connection_params"] = {
            "type": "connect",
            "port": 50052,
            "ip": "localhost"
        }
        
        mock_python_session.execute.return_value = {
            "success": True,
            "stdout": "RECONNECT_FAILED:Connection refused",
            "stderr": "",
        }
        
        success, message = attempt_reconnect_mapdl(mock_python_session, mock_context)
        
        assert success is False
        assert "Connection refused" in message

    def test_reconnect_with_stored_launch_params_success(self, mock_python_session, mock_context):
        """Test successful relaunch with stored launch parameters."""
        mock_context.metadata["mapdl_connection_params"] = {
            "type": "launch",
            "nproc": 2,
            "exec_file": None,
            "run_location": None,
            "additional_switches": ""
        }
        
        mock_python_session.execute.return_value = {
            "success": True,
            "stdout": "RELAUNCH_SUCCESS:Launched new MAPDL at localhost:50052",
            "stderr": "",
        }
        
        success, message = attempt_reconnect_mapdl(mock_python_session, mock_context)
        
        assert success is True
        assert "RELAUNCH_SUCCESS" in message

    @patch('ansys.mapdl.mcp.helpers.get_mapdl_instances_from_cli')
    def test_reconnect_via_cli_discovery_success(self, mock_cli, mock_python_session, mock_context):
        """Test successful reconnection via CLI discovery."""
        # No stored params
        mock_context.metadata = {}
        
        # CLI finds running instances
        mock_cli.return_value = [
            {
                'name': 'ANSYS.exe',
                'is_instance': True,
                'status': 'running',
                'port': 50052,
                'pid': 28404
            }
        ]
        
        mock_python_session.execute.return_value = {
            "success": True,
            "stdout": "RECONNECT_SUCCESS:Connected to MAPDL at localhost:50052",
            "stderr": "",
        }
        
        success, message = attempt_reconnect_mapdl(mock_python_session, mock_context)
        
        assert success is True
        assert "Connected" in message

    @patch('ansys.mapdl.mcp.helpers.get_mapdl_instances_from_cli')
    def test_reconnect_via_cli_discovery_no_instances(self, mock_cli, mock_python_session, mock_context):
        """Test reconnection fails when no instances found via CLI."""
        mock_context.metadata = {}
        mock_cli.return_value = []
        
        success, message = attempt_reconnect_mapdl(mock_python_session, mock_context)
        
        assert success is False
        assert "no running mapdl instances" in message.lower()

    @patch('ansys.mapdl.mcp.helpers.get_mapdl_instances_from_cli')
    def test_reconnect_via_cli_prefers_main_instances(self, mock_cli, mock_python_session, mock_context):
        """Test that CLI discovery prefers main instances over child processes."""
        mock_context.metadata = {}
        
        # CLI finds multiple instances
        mock_cli.return_value = [
            {
                'name': 'child.exe',
                'is_instance': False,
                'status': 'running',
                'port': 50053,
                'pid': 28500
            },
            {
                'name': 'MAPDL.exe',
                'is_instance': True,
                'status': 'running',
                'port': 50052,
                'pid': 28404
            }
        ]
        
        mock_python_session.execute.return_value = {
            "success": True,
            "stdout": "RECONNECT_SUCCESS:Connected to MAPDL at localhost:50052",
            "stderr": "",
        }
        
        success, message = attempt_reconnect_mapdl(mock_python_session, mock_context)
        
        assert success is True
        # Should try main instance (port 50052) not child (port 50053)
        assert mock_python_session.execute.called


@pytest.mark.unit
class TestReplayCommandHistory:
    """Test replay_command_history function."""

    def test_replay_empty_history(self, mock_python_session):
        """Test replaying empty command history."""
        success, message = replay_command_history(mock_python_session, [])
        
        assert success is True
        assert "No commands to replay" in message

    def test_replay_successful(self, mock_python_session, sample_command_history):
        """Test successful replay of command history."""
        mock_python_session.execute.return_value = {
            "success": True,
            "stdout": "",
            "stderr": "",
        }
        
        success, message = replay_command_history(mock_python_session, sample_command_history)
        
        assert success is True
        assert "3 commands" in message
        assert mock_python_session.execute.call_count == 3

    def test_replay_with_failures(self, mock_python_session, sample_command_history):
        """Test replay with some command failures."""
        # First command succeeds, second fails, third succeeds
        mock_python_session.execute.side_effect = [
            {"success": True, "stdout": "", "stderr": ""},
            {"success": False, "error": "Invalid element type", "stderr": ""},
            {"success": True, "stdout": "", "stderr": ""},
        ]
        
        success, message = replay_command_history(mock_python_session, sample_command_history)
        
        assert success is False
        assert "failed during replay" in message.lower()
        assert "Invalid element type" in message

    def test_replay_with_exception(self, mock_python_session, sample_command_history):
        """Test replay when an exception occurs."""
        # First command succeeds, second raises exception
        mock_python_session.execute.side_effect = [
            {"success": True, "stdout": "", "stderr": ""},
            Exception("Connection lost"),
            {"success": True, "stdout": "", "stderr": ""},
        ]
        
        success, message = replay_command_history(mock_python_session, sample_command_history)
        
        assert success is False
        assert "Connection lost" in message

    def test_replay_command_count_accurate(self, mock_python_session):
        """Test that all commands in history are replayed."""
        commands = [f"command_{i}" for i in range(10)]
        
        mock_python_session.execute.return_value = {
            "success": True,
            "stdout": "",
            "stderr": "",
        }
        
        success, message = replay_command_history(mock_python_session, commands)
        
        assert success is True
        assert mock_python_session.execute.call_count == 10
        assert "10 commands" in message
