from .server import PyMAPDLMCPServer
from fastmcp.server.dependencies import get_context
from ansys.common.mcp.helpers import logger


def register_tools(mcp: PyMAPDLMCPServer):
    """Register PyMAPDL-specific tools with the MCP server.

    Parameters
    ----------
    server : PyMAPDLMCPServer
        The MCP server instance to register tools with.
    """

    @mcp.tool()
    def execute_python_code(
        code: str,
        timeout: float = 30.0,
    ) -> str:
        """Execute Python code in the persistent Python session.

        This tool executes Python code using PyMAPDL in a persistent Python session.
        The code should use PyMAPDL methods (e.g., mapdl.prep7(), mapdl.et(), etc.)
        and assume that the 'mapdl' object is already available and connected.

        No need to import PyMAPDL, launch MAPDL or create the 'mapdl' object;
        these should already be handled before calling this tool.

        If the MAPDL session crashes during execution, this tool will automatically:
        1. Attempt to reconnect to the existing MAPDL instance
        2. If reconnection fails, launch a new MAPDL instance
        3. Replay all previous commands from history
        4. Execute the current command

        Parameters
        ----------
        code : str
            Python code to execute. The code should use PyMAPDL methods.
        timeout : float, optional
            Maximum execution time in seconds. Default is 30.0.

        Returns
        -------
        str
            Execution result containing stdout, stderr, and any error messages.
            If recovery was needed, includes recovery status information.
        """
        from ansys.mapdl.mcp.helpers import (
            check_mapdl_connection,
            attempt_reconnect_mapdl,
            replay_command_history,
        )

        # Get context via dependency injection
        ctx = get_context()
        app_context = ctx.fastmcp._lifespan_result
        python_session = app_context.python_session

        if python_session is None:
            return "No Python session available. Python session should be initialized automatically."

        if not python_session.is_running():
            return "Python session is not running. Please restart the server."

        logger.info(f"Executing Python code in persistent session...")
        logger.debug(f"Code to execute:\n{code}")

        try:
            # Execute the code in the persistent Python session
            result = python_session.execute(code, timeout=timeout)

            # Check if execution was successful
            if result["success"]:
                # Add to command history only if successful
                app_context.command_history.append(code)
                
                output_parts = []
                if result.get("stdout"):
                    output_parts.append(f"Output:\n{result['stdout']}")
                if result.get("stderr"):
                    output_parts.append(f"Warnings/Info:\n{result['stderr']}")
                
                if output_parts:
                    return "\n\n".join(output_parts)
                else:
                    return "Code executed successfully (no output)"
            else:
                # Check if this might be a connection error
                error_msg = result.get('error', 'Unknown error')
                stderr = result.get('stderr', '')
                
                # Common indicators of MAPDL crash/connection loss
                connection_errors = [
                    'connection', 'grpc', 'channel', 'unavailable',
                    'broken pipe', 'closed', 'timeout', 'refused'
                ]
                
                is_connection_error = any(
                    err_keyword in error_msg.lower() or err_keyword in stderr.lower()
                    for err_keyword in connection_errors
                )
                
                if is_connection_error:
                    logger.warning("Detected potential MAPDL connection failure. Attempting recovery...")
                    
                    # Check connection status
                    is_connected, conn_error = check_mapdl_connection(python_session)
                    
                    if not is_connected:
                        logger.warning(f"MAPDL connection lost: {conn_error}")
                        logger.info("Initiating recovery process...")
                        
                        # Step 1: Attempt reconnection
                        reconnect_success, reconnect_msg = attempt_reconnect_mapdl(
                            python_session, app_context
                        )
                        
                        if not reconnect_success:
                            logger.warning(f"Reconnection failed: {reconnect_msg}")
                            logger.info("Reconnection will be attempted when next MAPDL command is executed")
                            return (
                                f"MAPDL session crashed and reconnection failed.\n\n"
                                f"Original error: {error_msg}\n"
                                f"Reconnection error: {reconnect_msg}\n\n"
                                f"Please use 'launch_new_mapdl' or 'connect_to_mapdl' tool to establish a new connection.\n"
                                f"The system has stored {len(app_context.command_history)} previous commands "
                                f"that will be automatically replayed after reconnection."
                            )
                        
                        logger.info("Reconnection successful. Replaying command history...")
                        
                        # Step 2: Replay command history
                        replay_success, replay_msg = replay_command_history(
                            python_session, app_context.command_history
                        )
                        
                        if not replay_success:
                            logger.warning(f"History replay had issues: {replay_msg}")
                            return (
                                f"MAPDL session recovered but history replay encountered errors.\n\n"
                                f"Reconnection: {reconnect_msg}\n"
                                f"History replay: {replay_msg}\n\n"
                                f"You may need to manually verify the MAPDL state."
                            )
                        
                        # Step 3: Retry the current command
                        logger.info("Retrying original command after recovery...")
                        retry_result = python_session.execute(code, timeout=timeout)
                        
                        if retry_result["success"]:
                            # Add to history after successful retry
                            app_context.command_history.append(code)
                            
                            output_parts = [
                                "⚠️  MAPDL session was recovered after a crash",
                                f"Reconnection: {reconnect_msg}",
                                f"Replayed: {len(app_context.command_history)-1} previous commands",
                                "",
                                "Command Output:"
                            ]
                            
                            if retry_result.get("stdout"):
                                output_parts.append(retry_result['stdout'])
                            if retry_result.get("stderr"):
                                output_parts.append(f"Warnings/Info:\n{retry_result['stderr']}")
                            
                            return "\n".join(output_parts)
                        else:
                            return (
                                f"MAPDL session recovered but command still failed.\n\n"
                                f"Recovery: {reconnect_msg}\n"
                                f"History replay: {replay_msg}\n"
                                f"Retry error: {retry_result.get('error', 'Unknown error')}"
                            )
                
                # Not a connection error, return original error
                error_msg = f"Error executing Python code:\n{error_msg}"
                if stderr:
                    error_msg += f"\n\nStderr:\n{stderr}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"Exception while executing Python code: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    @mcp.tool()
    def launch_new_mapdl(
        exec_file: str | None = None,
        run_location: str | None = None,
        nproc: int = 2,
        additional_switches: str = "",
    ) -> str:
        """Launch a new MAPDL instance.

        This tool starts a new MAPDL instance using PyMAPDL's launch_mapdl function.
        The launched instance will be automatically connected and stored in the context
        for subsequent operations. The instance can be closed using the disconnect_from_mapdl tool.

        Before launching, this tool checks:
        1. If there's already an active MAPDL connection in the session
        2. If there are running MAPDL instances that could be reused

        Parameters
        ----------
        exec_file : str, optional
            The path to the MAPDL executable. If None, PyMAPDL will attempt to find
            the MAPDL executable automatically.
        run_location : str, optional
            The directory where MAPDL will run and store files. If None, a temporary
            directory will be created.
        nproc : int, optional
            Number of processors to use. Default is 2.
        additional_switches : str, optional
            Additional command line switches to pass to MAPDL. Default is empty string.

        Returns
        -------
        str
            Launch status message with MAPDL version and connection information.
        """
        from ansys.mapdl.mcp.helpers import (
            check_mapdl_connection,
            get_mapdl_instances_from_cli,
        )

        logger.info("Launching new MAPDL instance...")

        # Get context via dependency injection
        ctx = get_context()
        app_context = ctx.fastmcp._lifespan_result
        python_session = app_context.python_session

        if python_session is None or not python_session.is_running():
            return "Python session is not available. Please restart the server."

        try:
            # Check if there's already an active and responsive connection
            is_connected, conn_msg = check_mapdl_connection(python_session)
            
            if is_connected:
                return (
                    "Already connected to an active MAPDL session. "
                    "Use the connect_to_mapdl tool to connect to it."
                )
            
            # Check for running MAPDL instances that could be reused
            logger.info("Checking for running MAPDL instances...")
            running_instances = get_mapdl_instances_from_cli(python_session)
            
            if running_instances:
                instance_details = []
                for inst in running_instances:
                    if inst.get('status') == 'running' and inst.get('port'):
                        instance_details.append(
                            f"  - Port {inst['port']}, PID {inst['pid']} ({inst['name']})"
                        )
                
                if instance_details:
                    instances_str = "\n".join(instance_details)
                    return (
                        f"Found {len(instance_details)} running MAPDL instance(s):\n"
                        f"{instances_str}\n\n"
                        f"Consider using connect_to_mapdl tool to connect to an existing instance "
                        f"instead of launching a new one. This saves resources and startup time.\n\n"
                        f"If you still want to launch a new instance, please disconnect any existing "
                        f"connections first, or stop the running instances."
                    )

            # Build the launch command
            args = [f"nproc={nproc}"]
            if exec_file is not None:
                args.append(f'exec_file="{exec_file}"')
            if run_location is not None:
                args.append(f'run_location="{run_location}"')
            if additional_switches:
                args.append(f'additional_switches="{additional_switches}"')
            
            launch_code = f"from ansys.mapdl.core import launch_mapdl\nmapdl = launch_mapdl({', '.join(args)})\nprint(mapdl)"
            
            logger.info(f"Executing launch command in Python session")
            result = python_session.execute(launch_code, timeout=60.0)

            if result["success"]:
                # Store launch parameters for potential recovery
                app_context.metadata["mapdl_connection_params"] = {
                    "type": "launch",
                    "exec_file": exec_file,
                    "run_location": run_location,
                    "nproc": nproc,
                    "additional_switches": additional_switches,
                }
                logger.info("Stored launch parameters for crash recovery")
                
                output = result.get("stdout", "MAPDL launched successfully")
                logger.info(f"MAPDL launched successfully")
                return output

            else:
                error_msg = f"Failed to launch MAPDL: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"Failed to launch MAPDL: {str(e)}"
            logger.error(error_msg)
            return error_msg


    @mcp.tool()
    def connect_to_mapdl(
        port: int = 50052,
        ip: str = "localhost",
    ) -> str:
        """Connect to an existing MAPDL instance.

        This tool establishes a connection to a running MAPDL instance using the
        provided port and IP address. The connection is stored for subsequent
        operations and can be closed using the disconnect_from_mapdl tool.

        Before connecting, this tool checks if there's already an active connection.
        It also verifies that a MAPDL instance is actually running on the specified port.

        Parameters
        ----------
        port : int, optional
            The gRPC port where MAPDL is listening. Default is 50052.
        ip : str, optional
            The IP address where MAPDL is running. Default is "localhost".

        Returns
        -------
        str
            Connection status message with MAPDL version information.
        """
        from ansys.mapdl.mcp.helpers import (
            check_mapdl_connection,
            get_mapdl_instances_from_cli,
        )

        logger.info(f"Connecting to MAPDL instance at {ip}:{port}...")

        # Get context via dependency injection
        ctx = get_context()
        app_context = ctx.fastmcp._lifespan_result
        python_session = app_context.python_session

        if python_session is None or not python_session.is_running():
            return "Python session is not available. Please restart the server."

        try:
            # Check if there's already an active and responsive connection
            is_connected, conn_msg = check_mapdl_connection(python_session)
            
            if is_connected:
                return (
                    "Already connected to an active MAPDL session. "
                    "Please disconnect first using disconnect_from_mapdl tool if you want to connect to a different instance."
                )
            
            # If connecting to localhost, verify the instance is actually running on that port
            if ip in ("localhost", "127.0.0.1"):
                logger.info("Verifying MAPDL instance is running on specified port...")
                running_instances = get_mapdl_instances_from_cli(python_session)
                
                if running_instances:
                    # Check if there's an instance on the specified port
                    target_instance = next(
                        (inst for inst in running_instances if inst.get('port') == port),
                        None
                    )
                    
                    if not target_instance:
                        available_ports = [
                            inst['port'] for inst in running_instances 
                            if inst.get('status') == 'running' and inst.get('port')
                        ]
                        if available_ports:
                            ports_str = ", ".join(str(p) for p in available_ports)
                            return (
                                f"No MAPDL instance found running on port {port}.\n"
                                f"Available MAPDL instances are running on ports: {ports_str}\n\n"
                                f"Please use one of these ports or launch a new MAPDL instance."
                            )
                        else:
                            return (
                                f"No MAPDL instance found running on port {port}.\n"
                                f"Please launch a MAPDL instance first or verify the port number."
                            )
                    else:
                        logger.info(f"Verified MAPDL instance running on port {port} (PID: {target_instance.get('pid')})")

            connect_code = f"from ansys.mapdl.core import launch_mapdl\nmapdl = launch_mapdl(ip='{ip}', port={port})\nprint(mapdl)"
            
            logger.info(f"Executing command to connect to the MAPDL instance in Python session")
            result = python_session.execute(connect_code, timeout=60.0)

            if result["success"]:
                # Store connection parameters for recovery
                app_context.metadata["mapdl_connection_params"] = {
                    "type": "connect",
                    "port": port,
                    "ip": ip,
                }
                logger.info("Stored connection parameters for crash recovery")
                
                output = result.get("stdout", "MAPDL connected successfully")
                logger.info(f"MAPDL connected successfully")
                return output

            else:
                error_msg = f"Failed to launch MAPDL: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"Failed to launch MAPDL: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    @mcp.tool()
    def disconnect_from_mapdl() -> str:
        """Disconnect from the current MAPDL instance.

        This tool disconnects from the currently connected MAPDL instance
        and cleans up the connection in the persistent Python session.

        Returns
        -------
        str
            Disconnection status message.
        """
        logger.info("Disconnecting from MAPDL instance...")

        # Get context via dependency injection
        ctx = get_context()
        app_context = ctx.fastmcp._lifespan_result
        python_session = app_context.python_session

        if python_session is None or not python_session.is_running():
            return "Python session is not available. Please restart the server."

        try:
            disconnect_code = "mapdl.exit()\nmapdl = None"
            result = python_session.execute(disconnect_code, timeout=10.0)

            if result["success"]:
                # Clear stored connection parameters
                if "mapdl_connection_params" in app_context.metadata:
                    del app_context.metadata["mapdl_connection_params"]
                
                logger.info("Disconnected from MAPDL successfully")
                return "Disconnected from MAPDL successfully."

            else:
                error_msg = f"Failed to disconnect from MAPDL: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"Failed to disconnect from MAPDL: {str(e)}"
            logger.error(error_msg)
            return error_msg

    @mcp.tool()
    def get_command_history() -> str:
        """Retrieve the command history executed in the current MAPDL session.

        Returns
        -------
        str
            A formatted string of the command history.
        """
        logger.info("Retrieving MAPDL command history...")

        # Get context via dependency injection
        ctx = get_context()
        app_context = ctx.fastmcp._lifespan_result
        command_history = app_context.command_history

        if not command_history:
            return "No commands have been executed in this session."

        history_str = "\n".join(f"{idx + 1}: {cmd}" for idx, cmd in enumerate(command_history))
        logger.info("Command history retrieved successfully")
        return history_str


    @mcp.tool()
    def clear_command_history() -> str:
        """Clear the command history executed in the current MAPDL session.

        Returns
        -------
        str
            Confirmation message indicating the command history has been cleared.
        """
        logger.info("Clearing MAPDL command history...")

        # Get context via dependency injection
        ctx = get_context()
        app_context = ctx.fastmcp._lifespan_result
        app_context.command_history.clear()

        logger.info("Command history cleared successfully")
        return "Command history cleared successfully."

    @mcp.tool()
    def undo_last_command() -> str:
        """Undo the last command executed in the current MAPDL session.

        Returns
        -------
        str
            Confirmation message indicating the last command has been undone.
        """
        logger.info("Undoing last MAPDL command...")

        # Get context via dependency injection
        ctx = get_context()
        app_context = ctx.fastmcp._lifespan_result
        command_history = app_context.command_history

        if not command_history:
            return "No commands to undo in this session."

        last_command = command_history.pop()
        logger.info(f"Undid last command: {last_command}")
        return f"Undid last command: {last_command}"

    @mcp.tool()
    def restart_python_session(replay_history: bool = True) -> str:
        """Restart Python session and optionally replay command history.
        
        Parameters
        ----------
        replay_history : bool
            If True, replay all previous commands from history
        
        Returns
        -------
        str
            Restart status
        """
        ctx = get_context()
        app_context = ctx.fastmcp._lifespan_result
        
        # Restart the session
        result = app_context.python_session.restart()
        
        if not result["success"]:
            return f"Failed to restart: {result.get('error')}"
        
        # Optionally replay command history
        if replay_history and app_context.command_history:
            logger.info(f"Replaying {len(app_context.command_history)} commands...")
            
            for i, cmd in enumerate(app_context.command_history):
                replay_result = app_context.python_session.execute(cmd)
                if not replay_result["success"]:
                    return (
                        f"Session restarted but replay failed at command {i+1}/{len(app_context.command_history)}: "
                        f"{replay_result.get('error')}"
                    )
            
            return f"Session restarted and {len(app_context.command_history)} commands replayed successfully"
        
        return "Session restarted successfully"
