"""Tests for MAPDL connection management tools."""

from unittest.mock import MagicMock, patch

import pytest

from ansys.mapdl.mcp import connect_to_mapdl, disconnect_from_mapdl


@pytest.mark.unit
class TestConnectToMapdl:
    """Tests for connect_to_mapdl tool."""

    def test_connect_default_parameters(self, mock_context_no_mapdl):
        """Test connecting to MAPDL with default parameters."""
        # Create a mock MAPDL instance
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50052

        with patch("ansys.mapdl.mcp.tools.Mapdl", return_value=mock_mapdl):
            result = connect_to_mapdl(mock_context_no_mapdl)

            # Verify successful connection
            assert isinstance(result, str)
            assert "Successfully connected to MAPDL" in result
            assert "localhost:50052" in result
            assert "2024 R2" in result

            # Verify MAPDL was stored in context
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl == mock_mapdl

    def test_connect_custom_port(self, mock_context_no_mapdl):
        """Test connecting to MAPDL with custom port."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R1"
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50053

        with patch("ansys.mapdl.mcp.tools.Mapdl", return_value=mock_mapdl) as mock_mapdl_class:
            result = connect_to_mapdl(mock_context_no_mapdl, port=50053)

            # Verify connection with custom port
            assert "Successfully connected to MAPDL" in result
            assert "localhost:50053" in result

            # Verify Mapdl was called with correct parameters
            mock_mapdl_class.assert_called_once_with(
                start_instance=False,
                ip="localhost",
                port=50053,
                cleanup_on_exit=False,
                loglevel="INFO",
            )

    def test_connect_custom_ip(self, mock_context_no_mapdl):
        """Test connecting to MAPDL with custom IP address."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "192.168.1.100"
        mock_mapdl._port = 50052

        with patch("ansys.mapdl.mcp.tools.Mapdl", return_value=mock_mapdl) as mock_mapdl_class:
            result = connect_to_mapdl(mock_context_no_mapdl, ip="192.168.1.100")

            # Verify connection with custom IP
            assert "Successfully connected to MAPDL" in result
            assert "192.168.1.100:50052" in result

            # Verify Mapdl was called with correct parameters
            mock_mapdl_class.assert_called_once_with(
                start_instance=False,
                ip="192.168.1.100",
                port=50052,
                cleanup_on_exit=False,
                loglevel="INFO",
            )

    def test_connect_custom_ip_and_port(self, mock_context_no_mapdl):
        """Test connecting to MAPDL with both custom IP and port."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "10.0.0.50"
        mock_mapdl._port = 50099

        with patch("ansys.mapdl.mcp.tools.Mapdl", return_value=mock_mapdl) as mock_mapdl_class:
            result = connect_to_mapdl(mock_context_no_mapdl, port=50099, ip="10.0.0.50")

            # Verify connection with custom parameters
            assert "Successfully connected to MAPDL" in result
            assert "10.0.0.50:50099" in result

            # Verify Mapdl was called with correct parameters
            mock_mapdl_class.assert_called_once_with(
                start_instance=False,
                ip="10.0.0.50",
                port=50099,
                cleanup_on_exit=False,
                loglevel="INFO",
            )

    def test_connect_already_connected(self, mock_context):
        """Test connecting when already connected."""
        # Context already has a MAPDL connection
        result = connect_to_mapdl(mock_context)

        # Verify appropriate error message
        assert "Already connected to MAPDL" in result
        assert "disconnect first" in result

    def test_connect_connection_error(self, mock_context_no_mapdl):
        """Test handling connection errors."""
        with patch("ansys.mapdl.mcp.tools.Mapdl", side_effect=Exception("Connection refused")):
            result = connect_to_mapdl(mock_context_no_mapdl, port=50052, ip="localhost")

            # Verify error message is returned
            assert "Failed to connect to MAPDL" in result
            assert "Connection refused" in result

            # Verify context remains empty
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl is None

    def test_connect_network_error(self, mock_context_no_mapdl):
        """Test handling network errors during connection."""
        with patch(
            "ansys.mapdl.mcp.tools.Mapdl", side_effect=ConnectionError("Network unreachable")
        ):
            result = connect_to_mapdl(mock_context_no_mapdl, port=50052, ip="192.168.1.999")

            # Verify error message
            assert "Failed to connect to MAPDL" in result
            assert "Network unreachable" in result

    def test_connect_timeout_error(self, mock_context_no_mapdl):
        """Test handling timeout errors during connection."""
        with patch("ansys.mapdl.mcp.tools.Mapdl", side_effect=TimeoutError("Connection timed out")):
            result = connect_to_mapdl(mock_context_no_mapdl)

            # Verify timeout error is handled
            assert "Failed to connect to MAPDL" in result
            assert "Connection timed out" in result

    def test_connect_stores_mapdl_in_context(self, mock_context_no_mapdl):
        """Test that connected MAPDL instance is properly stored in context."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50052

        # Verify context starts with no MAPDL
        assert mock_context_no_mapdl.request_context.lifespan_context.mapdl is None

        with patch("ansys.mapdl.mcp.tools.Mapdl", return_value=mock_mapdl):
            result = connect_to_mapdl(mock_context_no_mapdl)

            # Verify successful connection
            assert "Successfully connected" in result

            # Verify MAPDL is stored in context
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl is not None
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl == mock_mapdl

    def test_connect_stderr_logging(self, mock_context_no_mapdl, capsys):
        """Test that connect_to_mapdl logs to stderr."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50052

        with patch("ansys.mapdl.mcp.tools.Mapdl", return_value=mock_mapdl):
            connect_to_mapdl(mock_context_no_mapdl)

            # Capture stderr output
            captured = capsys.readouterr()

            # Verify logging messages
            assert "Connecting to MAPDL instance at localhost:50052" in captured.err
            assert "Connected to MAPDL successfully" in captured.err


@pytest.mark.unit
class TestDisconnectFromMapdl:
    """Tests for disconnect_from_mapdl tool."""

    def test_disconnect_success(self, mock_context):
        """Test disconnecting from MAPDL successfully."""
        # Set up IP and port attributes on mock MAPDL
        mock_context.request_context.lifespan_context.mapdl._ip = "localhost"
        mock_context.request_context.lifespan_context.mapdl._port = 50052

        # Store reference to check exit was called
        mapdl_ref = mock_context.request_context.lifespan_context.mapdl

        result = disconnect_from_mapdl(mock_context)

        # Verify successful disconnection
        assert isinstance(result, str)
        assert "Successfully disconnected from MAPDL" in result
        assert "localhost:50052" in result

        # Verify exit was called on the original object
        mapdl_ref.exit.assert_called_once()

        # Verify MAPDL was removed from context
        assert mock_context.request_context.lifespan_context.mapdl is None

    def test_disconnect_no_connection(self, mock_context_no_mapdl):
        """Test disconnecting when no connection exists."""
        result = disconnect_from_mapdl(mock_context_no_mapdl)

        # Verify appropriate message
        assert "No MAPDL connection to disconnect" in result

    def test_disconnect_clears_context(self, mock_context):
        """Test that disconnect properly clears the context."""
        mock_context.request_context.lifespan_context.mapdl._ip = "localhost"
        mock_context.request_context.lifespan_context.mapdl._port = 50052

        # Verify MAPDL exists before disconnect
        assert mock_context.request_context.lifespan_context.mapdl is not None

        disconnect_from_mapdl(mock_context)

        # Verify MAPDL is cleared after disconnect
        assert mock_context.request_context.lifespan_context.mapdl is None

    def test_disconnect_error_during_exit(self, mock_context):
        """Test handling errors during disconnection."""
        mock_context.request_context.lifespan_context.mapdl._ip = "localhost"
        mock_context.request_context.lifespan_context.mapdl._port = 50052
        mock_context.request_context.lifespan_context.mapdl.exit.side_effect = Exception(
            "Disconnection error"
        )

        result = disconnect_from_mapdl(mock_context)

        # Verify error message is returned
        assert "Error during disconnect" in result
        assert "Disconnection error" in result

        # Verify context is still cleared even on error
        assert mock_context.request_context.lifespan_context.mapdl is None

    def test_disconnect_connection_lost(self, mock_context):
        """Test disconnecting when connection is already lost."""
        mock_context.request_context.lifespan_context.mapdl._ip = "localhost"
        mock_context.request_context.lifespan_context.mapdl._port = 50052
        mock_context.request_context.lifespan_context.mapdl.exit.side_effect = ConnectionError(
            "Connection already closed"
        )

        result = disconnect_from_mapdl(mock_context)

        # Verify error is handled gracefully
        assert "Error during disconnect" in result
        assert "Connection already closed" in result

        # Context should still be cleared
        assert mock_context.request_context.lifespan_context.mapdl is None

    def test_disconnect_stderr_logging(self, mock_context, capsys):
        """Test that disconnect_from_mapdl logs to stderr."""
        mock_context.request_context.lifespan_context.mapdl._ip = "localhost"
        mock_context.request_context.lifespan_context.mapdl._port = 50052

        disconnect_from_mapdl(mock_context)

        # Capture stderr output
        captured = capsys.readouterr()

        # Verify logging messages
        assert "Disconnecting from MAPDL at localhost:50052" in captured.err
        assert "Disconnected successfully" in captured.err

    def test_disconnect_custom_ip_port(self, mock_context):
        """Test disconnecting from MAPDL with custom IP and port."""
        mock_context.request_context.lifespan_context.mapdl._ip = "192.168.1.100"
        mock_context.request_context.lifespan_context.mapdl._port = 50053

        result = disconnect_from_mapdl(mock_context)

        # Verify disconnection message includes custom IP and port
        assert "Successfully disconnected from MAPDL at 192.168.1.100:50053" in result


@pytest.mark.unit
class TestConnectionLifecycle:
    """Tests for the full connection lifecycle."""

    def test_connect_use_disconnect_workflow(self, mock_context_no_mapdl):
        """Test complete workflow: connect, use, disconnect."""
        from ansys.mapdl.mcp import check_mapdl_status, run_mapdl_command, write_comment

        # Create mock MAPDL
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50052
        mock_mapdl.com = MagicMock(return_value="Comment written")
        mock_mapdl.run = MagicMock(return_value="Command executed")

        # Step 1: Connect
        with patch("ansys.mapdl.mcp.tools.Mapdl", return_value=mock_mapdl):
            result = connect_to_mapdl(mock_context_no_mapdl)
            assert "Successfully connected" in result

        # Step 2: Use MAPDL
        status = check_mapdl_status(mock_context_no_mapdl)
        assert "MAPDL is available" in status

        comment_result = write_comment(mock_context_no_mapdl, "Test comment")
        assert "Comment written successfully" in comment_result

        command_result = run_mapdl_command(mock_context_no_mapdl, "/PREP7")
        assert "MAPDL command executed successfully" in command_result

        # Step 3: Disconnect
        result = disconnect_from_mapdl(mock_context_no_mapdl)
        assert "Successfully disconnected" in result

        # Step 4: Verify connection is cleared
        status_after = check_mapdl_status(mock_context_no_mapdl)
        assert "No MAPDL connection available" in status_after

    def test_reconnect_after_disconnect(self, mock_context_no_mapdl):
        """Test that we can reconnect after disconnecting."""
        mock_mapdl1 = MagicMock()
        mock_mapdl1.version = "2024 R2"
        mock_mapdl1._ip = "localhost"
        mock_mapdl1._port = 50052

        mock_mapdl2 = MagicMock()
        mock_mapdl2.version = "2024 R1"
        mock_mapdl2._ip = "localhost"
        mock_mapdl2._port = 50053

        # First connection
        with patch("ansys.mapdl.mcp.tools.Mapdl", return_value=mock_mapdl1):
            result = connect_to_mapdl(mock_context_no_mapdl, port=50052)
            assert "Successfully connected" in result
            assert "50052" in result

        # Disconnect
        disconnect_from_mapdl(mock_context_no_mapdl)

        # Second connection with different parameters
        with patch("ansys.mapdl.mcp.tools.Mapdl", return_value=mock_mapdl2):
            result = connect_to_mapdl(mock_context_no_mapdl, port=50053)
            assert "Successfully connected" in result
            assert "50053" in result

    def test_tools_without_connection(self, mock_context_no_mapdl):
        """Test that tools return appropriate messages without connection."""
        from ansys.mapdl.mcp import check_mapdl_status, run_mapdl_command, write_comment

        # Check status without connection
        status = check_mapdl_status(mock_context_no_mapdl)
        assert "No MAPDL connection available" in status

        # Try to write comment without connection
        comment_result = write_comment(mock_context_no_mapdl, "Test")
        assert "No MAPDL connection available" in comment_result

        # Try to run command without connection
        command_result = run_mapdl_command(mock_context_no_mapdl, "/PREP7")
        assert "No MAPDL connection available" in command_result
