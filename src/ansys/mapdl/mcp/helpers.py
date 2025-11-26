

from asyncio import subprocess
from typing import Any
from .tools import logger
from .context import PyMAPDLContext

def get_mapdl_instances_from_cli() -> list[dict[str, Any]]:
    """
    Get list of running MAPDL instances using the pymapdl CLI command.
    
    This function runs `pymapdl list` command and parses the output to extract
    information about running MAPDL instances.
    
    Returns
    -------
    list[dict[str, Any]]
        List of dictionaries containing information about each MAPDL instance.
        Each dictionary has keys: 'name', 'is_instance', 'status', 'port', 'pid'
        
    Notes
    -----
    This function requires pymapdl to be installed in the environment.
    """
    instances = []
    
    try:
        # Run pymapdl list command
        result = subprocess.run(
            ["pymapdl", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode != 0:
            logger.warning(f"pymapdl list command failed: {result.stderr}")
            return instances
        
        output = result.stdout
        lines = output.strip().split('\n')
        
        # Skip header lines (first 2 lines typically)
        # Expected format:
        # Name          Is Instance    Status      gRPC port    PID
        # ------------  -------------  --------  -----------  -----
        # ANSYS.exe     False          running         50052  28404
        
        data_started = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip header and separator lines
            if "Name" in line and "Status" in line and "gRPC port" in line:
                data_started = True
                continue
            if line.startswith("-"):
                continue
            if not data_started:
                continue
            
            # Parse data line
            # Split by multiple spaces to handle tabular format
            parts = line.split()
            
            if len(parts) >= 5:
                instance = {
                    'name': parts[0],
                    'is_instance': parts[1].lower() in ('true', '1', 'yes'),
                    'status': parts[2],
                    'port': int(parts[3]) if parts[3].isdigit() else None,
                    'pid': int(parts[4]) if parts[4].isdigit() else None,
                }
                instances.append(instance)
                logger.debug(f"Found MAPDL instance: {instance}")
        
        logger.info(f"Found {len(instances)} MAPDL instances via CLI")
        
    except subprocess.TimeoutExpired:
        logger.warning("pymapdl list command timed out")
    except FileNotFoundError:
        logger.warning("pymapdl command not found - ensure pymapdl is installed")
    except Exception as e:
        logger.warning(f"Error running pymapdl list: {str(e)}")
    
    return instances


def check_mapdl_connection(python_session: Any) -> tuple[bool, str]:
    """
    Check if MAPDL is still connected and responsive.
    
    Parameters
    ----------
    python_session : PersistentPythonSession
        The Python session to check.
        
    Returns
    -------
    tuple[bool, str]
        (is_connected, error_message)
    """
    try:
        check_code = """
try:
    if mapdl is None:
        print('MAPDL_CHECK:NOT_CONNECTED')
    else:
        # Try to execute a simple command to verify connection
        mapdl.com('Connection check')
        print('MAPDL_CHECK:CONNECTED')
except Exception as e:
    print(f'MAPDL_CHECK:ERROR:{str(e)}')
"""
        result = python_session.execute(check_code, timeout=5.0)
        
        if not result["success"]:
            return False, f"Failed to check connection: {result.get('error', 'Unknown error')}"
        
        output = result.get("stdout", "")
        
        if "MAPDL_CHECK:CONNECTED" in output:
            return True, ""
        elif "MAPDL_CHECK:NOT_CONNECTED" in output:
            return False, "MAPDL is not connected (mapdl is None)"
        elif "MAPDL_CHECK:ERROR:" in output:
            error = output.split("MAPDL_CHECK:ERROR:", 1)[1].strip()
            return False, f"MAPDL connection error: {error}"
        else:
            return False, "Unable to verify MAPDL connection"
            
    except Exception as e:
        return False, f"Exception during connection check: {str(e)}"


def attempt_reconnect_mapdl(
    python_session: Any,
    context: "PyMAPDLContext"
) -> tuple[bool, str]:
    """
    Attempt to reconnect to MAPDL using stored connection parameters or by discovering
    running instances via the pymapdl CLI.
    
    This function first attempts to reconnect using stored connection parameters if available.
    If no parameters are stored, it uses the `pymapdl list` CLI command to discover running
    MAPDL instances and attempts to connect to them.
    
    Parameters
    ----------
    python_session : PersistentPythonSession
        The Python session to use.
    context : PyMAPDLContext
        The application context containing connection parameters.
        
    Returns
    -------
    tuple[bool, str]
        (success, message)
    """
    params = context.metadata.get("mapdl_connection_params")
    
    # If no connection parameters are stored, try to discover instances via CLI
    if params is None:
        logger.info("No stored connection parameters - discovering instances via pymapdl CLI")
        instances = get_mapdl_instances_from_cli()
        
        if not instances:
            return False, "No stored connection parameters and no running MAPDL instances found via CLI"
        
        # Filter for running instances with valid ports
        running_instances = [
            inst for inst in instances 
            if inst.get('status') == 'running' and inst.get('port') is not None
        ]
        
        if not running_instances:
            return False, f"Found {len(instances)} MAPDL instance(s), but none are running with valid ports"
        
        # Prefer main instances over child processes
        main_instances = [inst for inst in running_instances if inst.get('is_instance')]
        target_instances = main_instances if main_instances else running_instances
        
        # Try to connect to the first available instance
        for instance in target_instances:
            port = instance['port']
            logger.info(f"Attempting to connect to MAPDL instance at port {port} (PID: {instance['pid']})")
            
            reconnect_code = f"""
try:
    from ansys.mapdl.core import Mapdl
    mapdl = Mapdl(
        start_instance=False,
        ip="localhost",
        port={port},
        cleanup_on_exit=False,
        loglevel="INFO",
    )
    print(f"RECONNECT_SUCCESS:Connected to MAPDL at {{mapdl.ip}}:{{mapdl.port}}")
except Exception as e:
    print(f"RECONNECT_FAILED:{{str(e)}}")
"""
            result = python_session.execute(reconnect_code, timeout=30.0)
            
            if result["success"] and "RECONNECT_SUCCESS:" in result.get("stdout", ""):
                logger.info(f"Successfully connected to MAPDL instance at port {port}")
                # Store the connection parameters for future use
                context.mapdl_connection_params = {
                    "type": "connect",
                    "port": port,
                    "ip": "localhost",
                }
                return True, result.get("stdout", "Connected successfully")
        
        # If we get here, all connection attempts failed
        return False, f"Failed to connect to any of {len(target_instances)} available MAPDL instance(s)"
    
    # Use stored connection parameters
    connection_type = params.get("type", "launch")
    
    logger.info(f"Attempting to reconnect using {connection_type}...")
    
    try:
        if connection_type == "connect":
            # Try to reconnect to existing instance
            port = params.get("port", 50052)
            ip = params.get("ip", "localhost")
            
            reconnect_code = f"""
try:
    from ansys.mapdl.core import Mapdl
    mapdl = Mapdl(
        start_instance=False,
        ip="{ip}",
        port={port},
        cleanup_on_exit=False,
        loglevel="INFO",
    )
    print(f"RECONNECT_SUCCESS:Connected to MAPDL at {{mapdl.ip}}:{{mapdl.port}}")
except Exception as e:
    print(f"RECONNECT_FAILED:{{str(e)}}")
"""
            result = python_session.execute(reconnect_code, timeout=30.0)
            
            if result["success"] and "RECONNECT_SUCCESS:" in result.get("stdout", ""):
                logger.info("Successfully reconnected to existing MAPDL instance")
                return True, result.get("stdout", "Reconnected successfully")
            else:
                error = result.get("stdout", "") if "RECONNECT_FAILED:" in result.get("stdout", "") else result.get("error", "Unknown error")
                logger.warning(f"Failed to reconnect: {error}")
                return False, f"Reconnection failed: {error}"
                
        elif connection_type == "launch":
            # Relaunch MAPDL with same parameters
            exec_file = params.get("exec_file")
            run_location = params.get("run_location")
            nproc = params.get("nproc", 2)
            additional_switches = params.get("additional_switches", "")
            
            args = [f"nproc={nproc}"]
            if exec_file is not None:
                args.append(f'exec_file="{exec_file}"')
            if run_location is not None:
                args.append(f'run_location="{run_location}"')
            if additional_switches:
                args.append(f'additional_switches="{additional_switches}"')
            
            relaunch_code = f"""
try:
    from ansys.mapdl.core import launch_mapdl
    mapdl = launch_mapdl({', '.join(args)})
    print(f"RELAUNCH_SUCCESS:Launched new MAPDL at {{mapdl.ip}}:{{mapdl.port}}")
except Exception as e:
    print(f"RELAUNCH_FAILED:{{str(e)}}")
"""
            result = python_session.execute(relaunch_code, timeout=60.0)
            
            if result["success"] and "RELAUNCH_SUCCESS:" in result.get("stdout", ""):
                logger.info("Successfully relaunched MAPDL instance")
                return True, result.get("stdout", "Relaunched successfully")
            else:
                error = result.get("stdout", "") if "RELAUNCH_FAILED:" in result.get("stdout", "") else result.get("error", "Unknown error")
                logger.warning(f"Failed to relaunch: {error}")
                return False, f"Relaunch failed: {error}"
        else:
            return False, f"Unknown connection type: {connection_type}"
            
    except Exception as e:
        logger.error(f"Exception during reconnect: {str(e)}")
        return False, f"Exception during reconnect: {str(e)}"


def replay_command_history(
    python_session: Any,
    command_history: list[str]
) -> tuple[bool, str]:
    """
    Replay all commands from history after reconnecting.
    
    Parameters
    ----------
    python_session : PersistentPythonSession
        The Python session to use.
    command_history : list[str]
        List of commands to replay.
        
    Returns
    -------
    tuple[bool, str]
        (success, message)
    """
    if not command_history:
        return True, "No commands to replay"
    
    logger.info(f"Replaying {len(command_history)} commands from history...")
    
    failed_commands = []
    for i, cmd in enumerate(command_history):
        logger.debug(f"Replaying command {i+1}/{len(command_history)}")
        try:
            result = python_session.execute(cmd, timeout=30.0)
            if not result["success"]:
                error_msg = result.get("error", "Unknown error")
                logger.warning(f"Command {i+1} failed during replay: {error_msg}")
                failed_commands.append((i+1, cmd[:100], error_msg))
        except Exception as e:
            logger.warning(f"Exception replaying command {i+1}: {str(e)}")
            failed_commands.append((i+1, cmd[:100], str(e)))
    
    if failed_commands:
        error_summary = "\n".join([
            f"  Command {num}: {cmd_preview}... - Error: {err}"
            for num, cmd_preview, err in failed_commands
        ])
        return False, f"Some commands failed during replay:\n{error_summary}"
    
    logger.info("All commands replayed successfully")
    return True, f"Successfully replayed {len(command_history)} commands"
