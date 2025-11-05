"""Unit tests for list_mapdl_instances tool."""
from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
def test_list_mapdl_instances_success():
    """Test list_mapdl_instances with successful instance discovery."""
    from ansys.mapdl.mcp.mpc import list_mapdl_instances
    
    # Mock the list_instances function to return sample instances
    mock_output = """Name      Status      gRPC Port      IP            PID
--------  --------  -----------  ----------  -----
MAPDL_1   Running         50052  127.0.0.1   12345
MAPDL_2   Running         50053  127.0.0.1   12346"""
    
    with patch("ansys.mapdl.mcp.mpc.list_instances", return_value=mock_output):
        result = list_mapdl_instances()
        
        # Verify the function returns the output from list_instances
        assert result == mock_output
        assert "MAPDL_1" in result
        assert "50052" in result


@pytest.mark.unit
def test_list_mapdl_instances_no_instances():
    """Test list_mapdl_instances when no instances are found."""
    from ansys.mapdl.mcp.mpc import list_mapdl_instances
    
    # Mock the list_instances function to return empty/no instances message
    mock_output = "No MAPDL instances found."
    
    with patch("ansys.mapdl.mcp.mpc.list_instances", return_value=mock_output):
        result = list_mapdl_instances()
        
        # Verify appropriate message is returned
        assert result == mock_output


@pytest.mark.unit
def test_list_mapdl_instances_exception():
    """Test list_mapdl_instances handles exceptions gracefully."""
    from ansys.mapdl.mcp.mpc import list_mapdl_instances
    
    # Mock the list_instances function to raise an exception
    with patch(
        "ansys.mapdl.mcp.mpc.list_instances",
        side_effect=Exception("Connection error")
    ):
        result = list_mapdl_instances()
        
        # Verify error is caught and returned as string
        assert "Error" in result or "error" in result.lower()
        assert isinstance(result, str)


@pytest.mark.unit
def test_list_mapdl_instances_import_error():
    """Test list_mapdl_instances handles import errors gracefully."""
    from ansys.mapdl.mcp.mpc import list_mapdl_instances
    
    # Mock the import to fail
    with patch("ansys.mapdl.mcp.mpc.list_instances", side_effect=ImportError("Module not found")):
        result = list_mapdl_instances()
        
        # Verify error is caught and returned as string
        assert "Error" in result or "error" in result.lower()
        assert isinstance(result, str)


@pytest.mark.unit
def test_list_mapdl_instances_calls_with_long_flag():
    """Test that list_mapdl_instances calls list_instances with long=True."""
    from ansys.mapdl.mcp.mpc import list_mapdl_instances
    
    mock_list_instances = Mock(return_value="Sample output")
    
    with patch("ansys.mapdl.mcp.mpc.list_instances", mock_list_instances):
        result = list_mapdl_instances()
        
        # Verify list_instances was called with long=True
        mock_list_instances.assert_called_once_with(long=True)
        assert result == "Sample output"


@pytest.mark.unit
def test_list_mapdl_instances_multiple_instances():
    """Test list_mapdl_instances with multiple running instances."""
    from ansys.mapdl.mcp.mpc import list_mapdl_instances
    
    # Mock the list_instances function with multiple instances
    mock_output = """Name          Status      gRPC Port      IP            PID      Working Directory
------------  --------  -----------  ----------  -----  ------------------------------------
MAPDL_50052   Running         50052  127.0.0.1   12345  /tmp/ansys_workdir1
MAPDL_50053   Running         50053  127.0.0.1   12346  /tmp/ansys_workdir2
MAPDL_50054   Running         50054  127.0.0.1   12347  /tmp/ansys_workdir3"""
    
    with patch("ansys.mapdl.mcp.mpc.list_instances", return_value=mock_output):
        result = list_mapdl_instances()
        
        # Verify all instances are included in output
        assert "MAPDL_50052" in result
        assert "MAPDL_50053" in result
        assert "MAPDL_50054" in result
        assert "50052" in result
        assert "50053" in result
        assert "50054" in result


@pytest.mark.unit
def test_list_mapdl_instances_stderr_logging(capsys):
    """Test that list_mapdl_instances logs to stderr."""
    from ansys.mapdl.mcp.mpc import list_mapdl_instances
    
    mock_output = "Sample output"
    
    with patch("ansys.mapdl.mcp.mpc.list_instances", return_value=mock_output):
        result = list_mapdl_instances()
        
        # Capture stderr output
        captured = capsys.readouterr()
        
        # Verify logging message is written to stderr
        assert "Searching for MAPDL instances" in captured.err


@pytest.mark.unit  
def test_list_mapdl_instances_return_type():
    """Test that list_mapdl_instances always returns a string."""
    from ansys.mapdl.mcp.mpc import list_mapdl_instances
    
    # Test with normal output
    with patch("ansys.mapdl.mcp.mpc.list_instances", return_value="Normal output"):
        result = list_mapdl_instances()
        assert isinstance(result, str)
    
    # Test with empty string
    with patch("ansys.mapdl.mcp.mpc.list_instances", return_value=""):
        result = list_mapdl_instances()
        assert isinstance(result, str)
    
    # Test with exception
    with patch("ansys.mapdl.mcp.mpc.list_instances", side_effect=Exception("Error")):
        result = list_mapdl_instances()
        assert isinstance(result, str)
