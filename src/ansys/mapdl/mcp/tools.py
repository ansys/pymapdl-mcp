"""List of tools in PyMAPDL-MCP."""

import base64
import json
import logging
import os
import tempfile
from pathlib import Path

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from mcp.types import ImageContent, TextContent

from ansys.mapdl.mcp.mcp import AppContext, mcp

logger = logging.getLogger(__name__)


# Access type-safe lifespan context in tools
@mcp.tool()
def check_mapdl_status(
    ctx: Context[ServerSession, AppContext], instance: str | int | None = None
) -> str:
    """Check the status of MAPDL initialization for a specific instance.

    This tool executes the /STATUS command in MAPDL and extracts comprehensive
    information from PyMAPDL's Information, Geometry, and Post_processing classes.
    It also checks whether the MAPDL instance has exited or is exiting.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    instance : str | int | None
        Instance identifier (index, nickname, or None for default).

    Returns
    -------
    str
        JSON string containing comprehensive MAPDL status information including:
        - connection: Basic connection info (version, port, ip, directory, is_alive)
        - information: Data from Information class (title, jobname, routine, units, etc.)
        - geometry: Geometry statistics (number of keypoints, lines, areas, volumes)
        - post_processing: Post-processing availability and result sets
        - mesh: Mesh statistics (number of nodes and elements)

        Returns an error message if MAPDL is not available or has exited.
    """
    from ansys.mapdl.mcp.helpers import get_info, get_mapdl_instance

    mapdl, desc = get_mapdl_instance(ctx, instance)

    if mapdl is None:
        return desc

    try:
        info = get_info(mapdl)

        # Return as formatted JSON
        return json.dumps(info, indent=2)

    except Exception as e:
        error_msg = f"Error checking MAPDL status on {desc}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def check_mapdl_installed() -> str:
    """Check if MAPDL is installed on the system.

    This tool uses PyMAPDL's check_valid_ansys function to verify if a valid
    ANSYS/MAPDL installation is available on the system.

    Returns
    -------
    str
        Status message indicating whether MAPDL is installed or not.
    """
    logger.info("Checking if MAPDL is installed...")

    try:
        from ansys.mapdl.core.launcher import (  # type: ignore
            check_valid_ansys,
            get_default_ansys_path,
        )

        is_installed = check_valid_ansys()

        if is_installed:
            logger.info("MAPDL installation found")
            return f"MAPDL is installed on this system in: {get_default_ansys_path()}"
        else:
            logger.info("MAPDL installation not found")
            return (
                "MAPDL is not installed on this system or cannot be found in the "
                "standard locations. Please ensure ANSYS/MAPDL is properly installed "
                "and the installation path is correct."
            )

    except Exception as e:
        error_msg = f"Error checking MAPDL installation: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def write_comment(
    ctx: Context[ServerSession, AppContext],
    comment: str,
    instance: str | int | None = None,
) -> str:
    """Write a comment in the MAPDL session for a specific instance.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    comment : str
        The comment text to write in MAPDL.
    instance : str | int | None
        Instance identifier (index, nickname, or None for default).

    Returns
    -------
    str
        Confirmation message with the comment execution result.
    """
    from ansys.mapdl.mcp.helpers import get_mapdl_instance

    mapdl, desc = get_mapdl_instance(ctx, instance)

    if mapdl is None:
        return desc

    logger.info(f"Writing comment on {desc}: {comment}")
    result = mapdl.com(f"{comment}", mute=True)  # type: ignore[union-attr]
    return f"Comment written successfully on {desc}: {result}"


@mcp.tool()
def run_mapdl_command(
    ctx: Context[ServerSession, AppContext],
    cmd: str,
    instance: str | int | None = None,
) -> str:
    """Execute an arbitrary MAPDL command on a specific instance.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    cmd : str
        The MAPDL command to execute.
    instance : str | int | None
        Instance identifier (index, nickname, or None for default).

    Returns
    -------
    str
        Command execution result.
    """
    from ansys.mapdl.mcp.helpers import get_mapdl_instance

    mapdl, desc = get_mapdl_instance(ctx, instance)

    if mapdl is None:
        return desc

    result = mapdl.run(cmd)  # type: ignore[union-attr]
    return f"MAPDL command executed successfully on {desc}: {result}"


@mcp.tool()
def run_multiple_commands(
    ctx: Context[ServerSession, AppContext],
    commands: list[str],
    instance: str | int | None = None,
) -> str:
    """Execute multiple MAPDL commands in sequence on a specific instance.

    This tool is optimized for running multiple commands efficiently by using
    MAPDL's input_strings method, which processes commands in batch mode.
    This is significantly faster than executing commands one by one.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    commands : list[str]
        List of MAPDL commands to execute in sequence.
    instance : str | int | None
        Instance identifier (index, nickname, or None for default).

    Returns
    -------
    str
        Execution result with summary of commands executed.
    """
    from ansys.mapdl.mcp.helpers import get_mapdl_instance

    mapdl, desc = get_mapdl_instance(ctx, instance)

    if mapdl is None:
        return desc

    if not commands:
        return "No commands provided. Please provide a list of commands to execute."

    if not isinstance(commands, list):  # type: ignore
        return "Commands must be provided as a list of strings."

    # Filter out empty commands
    valid_commands = [cmd.strip() for cmd in commands if cmd and cmd.strip()]

    if not valid_commands:
        return "No valid commands found after filtering empty entries."

    try:
        logger.info(f"Executing {len(valid_commands)} MAPDL commands on {desc} using input_strings")

        # Use input_strings for batch command execution
        result = mapdl.input_strings(valid_commands)  # type: ignore[union-attr]

        success_msg = (
            f"Successfully executed {len(valid_commands)} MAPDL commands on {desc}:\n"
            f"Commands:\n" + "\n".join(f"  {i+1}. {cmd}" for i, cmd in enumerate(valid_commands))
        )

        if result:
            success_msg += f"\n\nOutput:\n{result}"

        return success_msg

    except Exception as e:
        error_msg = (
            f"Error executing commands on {desc}. Executed {len(valid_commands)} commands "
            f"but encountered error: {str(e)}\n"
            f"Commands that were attempted:\n"
            + "\n".join(f"  {i+1}. {cmd}" for i, cmd in enumerate(valid_commands))
        )
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def launch_mapdl(
    ctx: Context[ServerSession, AppContext],
    exec_file: str | None = None,
    run_location: str | None = None,
    jobname: str = "file",
    nproc: int = 2,
    ram: int | None = None,
    override: bool = False,
    additional_switches: str = "",
    clear_on_connect: bool = True,
    remove_temp_dir_on_exit: bool = False,
    start_timeout: int = 45,
    n_instances: int = 1,
    nicknames: list[str] | None = None,
) -> str:
    """Launch a new MAPDL instance or pool of instances.

    This tool starts new MAPDL instance(s) using PyMAPDL's MapdlPool infrastructure.
    For a single instance (n_instances=1, default), the behavior is nearly identical
    to the previous version. For multiple instances, a pool is created that can be
    managed through instance indices or nicknames.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    exec_file : str, optional
        The path to the MAPDL executable. If None, PyMAPDL will attempt to find
        the MAPDL executable automatically.
    run_location : str, optional
        The directory where MAPDL will run and store files. If None, a temporary
        directory will be created.
    jobname : str
        The jobname for MAPDL instances. Default is "file".
    nproc : int
        Number of processors to use. Default is 2.
    ram : int, optional
        Amount of RAM to allocate in MB.
    override : bool
        Whether to override existing files. Default is False.
    additional_switches : str
        Additional command line switches to pass to MAPDL. Default is empty string.
    clear_on_connect : bool
        Whether to clear on connect. Default is True.
    remove_temp_dir_on_exit : bool
        Whether to remove temp directory on exit. Default is False.
    start_timeout : int
        Timeout for starting instances in seconds. Default is 45.
    n_instances : int
        Number of MAPDL instances to launch. Default is 1.
    nicknames : list[str], optional
        List of nicknames for instances. Must match n_instances if provided.

    Returns
    -------
    str
        Launch status message with pool information.
    """
    from ansys.mapdl.mcp.helpers import create_pool

    logger.info(f"Launching {n_instances} MAPDL instance(s)...")

    return create_pool(
        ctx=ctx,
        n_instances=n_instances,
        exec_file=exec_file,
        run_location=run_location,
        jobname=jobname,
        nproc=nproc,
        ram=ram,
        override=override,
        additional_switches=additional_switches,
        clear_on_connect=clear_on_connect,
        remove_temp_dir_on_exit=remove_temp_dir_on_exit,
        start_timeout=start_timeout,
        start_instance=True,
        cleanup_on_exit=True,
        nicknames=nicknames,
    )


@mcp.tool()
def connect_to_mapdl(
    ctx: Context[ServerSession, AppContext],
    port: int | list[int] = 50052,
    ip: str | list[str] = "localhost",
    nicknames: list[str] | None = None,
) -> str:
    """Connect to existing MAPDL instance(s).

    This tool establishes connection(s) to running MAPDL instance(s) using the
    provided port(s) and IP address(es). For multiple instances, provide lists
    of IPs and ports. The connection(s) are stored in a pool for subsequent
    operations and can be closed using the disconnect_from_mapdl tool.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    port : int | list[int]
        The gRPC port(s) where MAPDL is listening. Default is 50052.
        For multiple instances, provide a list of ports.
    ip : str | list[str]
        The IP address(es) where MAPDL is running. Default is "localhost".
        For multiple instances, provide a list of IPs.
    nicknames : list[str], optional
        List of nicknames for instances. Must match number of instances if provided.

    Returns
    -------
    str
        Connection status message with pool information.
    """
    from ansys.mapdl.mcp.helpers import create_pool

    # Determine number of instances
    n_instances = 1
    if isinstance(ip, list):
        n_instances = len(ip)
    elif isinstance(port, list):
        n_instances = len(port)

    logger.info(f"Connecting to {n_instances} MAPDL instance(s)...")

    return create_pool(
        ctx=ctx,
        n_instances=n_instances,
        ip=ip,
        port=port,
        start_instance=False,
        cleanup_on_exit=False,
        nicknames=nicknames,
    )


@mcp.tool()
def disconnect_from_mapdl(ctx: Context[ServerSession, AppContext]) -> str:
    """Disconnect from the default MAPDL instance.

    This tool closes the connection to the default MAPDL instance (instance 0)
    and releases the associated resources. To disconnect from a specific instance
    or the entire pool, the internal exit_instance helper can be used.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.

    Returns
    -------
    str
        Disconnection status message.
    """
    from ansys.mapdl.mcp.helpers import exit_instance

    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return "No MAPDL pool available. Nothing to disconnect."

    # Disconnect from default instance
    default_idx = ctx.request_context.lifespan_context.default_instance_index
    return exit_instance(ctx, instance=default_idx)


@mcp.tool()
def list_mapdl_instances() -> str:
    """List all MAPDL instances running on the local machine.

    This tool uses PyMAPDL CLI's list_instances function to discover
    MAPDL instances running on the machine by scanning for active gRPC
    servers and their associated metadata.

    Returns
    -------
    str
        Formatted table containing information about all running MAPDL instances
        including their names, status, gRPC ports, IP addresses, PIDs, and
        working directories.
    """
    logger.info("Searching for MAPDL instances using PyMAPDL CLI...")

    from ansys.mapdl.mcp.helpers import list_instances

    # Use PyMAPDL CLI's list_instances function with long=True for detailed output
    return list_instances(long=True)


@mcp.tool()
def screenshot(
    ctx: Context[ServerSession, AppContext],
    instance: str | int | None = None,
) -> list[TextContent | ImageContent]:
    """Capture a screenshot of the MAPDL graphics window for a specific instance.

    This tool captures the current state of the MAPDL graphics window and returns
    both the file path and the image data encoded in base64 format for display
    in the MCP client.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    instance : str | int | None
        Instance identifier (index, nickname, or None for default).

    Returns
    -------
    list[TextContent | ImageContent]
        A list containing:
        - TextContent with the screenshot file path
        - ImageContent with the base64-encoded image data
    """
    from ansys.mapdl.mcp.helpers import get_mapdl_instance

    mapdl, desc = get_mapdl_instance(ctx, instance)

    if mapdl is None:
        return [TextContent(type="text", text=desc)]

    try:
        logger.info(f"Capturing MAPDL screenshot from {desc}...")

        # Create a temporary file with .png extension
        temp_fd, temp_path = tempfile.mkstemp(suffix=".png", prefix="mapdl_screenshot_")

        # Close the file descriptor as MAPDL will write to the path
        os.close(temp_fd)

        # Capture screenshot directly to the temporary location
        screenshot_path = mapdl.screenshot(savefig=temp_path)  # type: ignore[union-attr]

        # Verify file was created
        image_path = Path(screenshot_path)
        if not image_path.exists():
            error_msg = f"Screenshot file not found: {screenshot_path}"
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]

        # Read image data
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Encode to base64
        base64_data = base64.b64encode(image_data).decode("utf-8")

        # Determine mime type based on file extension
        mime_type = "image/png"  # Default to PNG
        if image_path.suffix.lower() in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif image_path.suffix.lower() == ".bmp":
            mime_type = "image/bmp"
        elif image_path.suffix.lower() == ".gif":
            mime_type = "image/gif"

        logger.info(f"Screenshot captured successfully from {desc}: {screenshot_path}")

        # Return both text (file path) and image content
        return [
            TextContent(type="text", text=f"Screenshot from {desc} saved to: {screenshot_path}"),
            ImageContent(type="image", data=base64_data, mimeType=mime_type),
        ]

    except Exception as e:
        if "temp_path" in locals() and Path(temp_path).exists():  # type: ignore
            Path(temp_path).unlink()  # pyright: ignore[reportPossiblyUnboundVariable]

        error_msg = f"Failed to capture screenshot from {desc}: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]


@mcp.tool()
def list_pool_instances(ctx: Context[ServerSession, AppContext]) -> str:
    """List all MAPDL instances in the pool with their status and nicknames.

    This tool displays comprehensive information about all instances in the pool,
    including their indices, nicknames, status, IP addresses, ports, and working
    directories. It also indicates which instance is set as the default.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.

    Returns
    -------
    str
        Formatted table of pool instances with their details.
    """
    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return "No MAPDL pool available. Use launch_mapdl or connect_to_mapdl to initialize."

    from ansys.mapdl.mcp.helpers import find_nickname

    lines = [
        f"MAPDL Pool: {len(pool._instances)} instance(s)",
        f"Default instance: {ctx.request_context.lifespan_context.default_instance_index}",
        "-" * 80,
    ]

    for idx in range(len(pool._instances)):
        instance = pool._instances[idx]
        nickname = find_nickname(ctx, idx)

        if instance is None:
            lines.append(f"Instance {idx}: DISCONNECTED")
        else:
            try:
                # Determine status
                if hasattr(instance, "_exited") and instance._exited:
                    status = "EXITED"
                elif hasattr(instance, "_exiting") and instance._exiting:
                    status = "EXITING"
                else:
                    status = "ACTIVE"

                nickname_str = f' ("{nickname}")' if nickname else ""
                lines.append(f"Instance {idx}{nickname_str}: {status}")
                lines.append(f"  IP: {instance.ip}")
                lines.append(f"  Port: {instance.port}")
                lines.append(f"  Version: {instance.version}")
                lines.append(f"  Directory: {instance.directory}")

            except Exception as e:
                lines.append(f"Instance {idx}: ERROR - {str(e)}")

    return "\n".join(lines)


@mcp.tool()
def set_default_instance(
    ctx: Context[ServerSession, AppContext],
    instance: str | int,
) -> str:
    """Set the default instance for operations without explicit instance specification.

    This tool changes which instance is used when no instance parameter is
    provided to other tools. The default can be set by index or nickname.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    instance : str | int
        Instance identifier (index or nickname).

    Returns
    -------
    str
        Confirmation message with the new default instance.
    """
    from ansys.mapdl.mcp.helpers import find_nickname, resolve_instance_index

    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return "No MAPDL pool available. Use launch_mapdl or connect_to_mapdl to initialize."

    # Resolve to index
    idx = resolve_instance_index(ctx, instance)

    if idx is None:
        from ansys.mapdl.mcp.helpers import list_available_instances

        available = list_available_instances(ctx)
        return f"Instance '{instance}' not found. Available instances:\n{available}"

    # Verify instance exists and is active
    if idx >= len(pool._instances) or pool._instances[idx] is None:
        return f"Instance {idx} is not available. Use list_pool_instances to see status."

    # Set as default
    ctx.request_context.lifespan_context.default_instance_index = idx

    nickname = find_nickname(ctx, idx)
    nickname_str = f' ("{nickname}")' if nickname else ""

    logger.info(f"Default instance set to {idx}{nickname_str}")
    return f"Default instance set to {idx}{nickname_str}"


@mcp.tool()
def assign_nickname(
    ctx: Context[ServerSession, AppContext],
    instance: str | int,
    nickname: str,
) -> str:
    """Assign or update a nickname for an instance.

    This tool creates or updates a nickname for a specific instance, allowing
    you to refer to instances by memorable names instead of indices. Each
    instance can have at most one nickname, and nicknames must be unique.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    instance : str | int
        Instance identifier (index or existing nickname).
    nickname : str
        New nickname to assign.

    Returns
    -------
    str
        Confirmation message with the nickname assignment.
    """
    from ansys.mapdl.mcp.helpers import find_nickname, resolve_instance_index

    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return "No MAPDL pool available. Use launch_mapdl or connect_to_mapdl to initialize."

    # Resolve to index
    idx = resolve_instance_index(ctx, instance)

    if idx is None:
        from ansys.mapdl.mcp.helpers import list_available_instances

        available = list_available_instances(ctx)
        return f"Instance '{instance}' not found. Available instances:\n{available}"

    # Verify instance exists
    if idx >= len(pool._instances) or pool._instances[idx] is None:
        return f"Instance {idx} is not available. Use list_pool_instances to see status."

    # Check if nickname already exists for a different instance
    existing_idx = ctx.request_context.lifespan_context.instance_nicknames.get(nickname)
    if existing_idx is not None and existing_idx != idx:
        return (
            f"Nickname '{nickname}' already assigned to instance {existing_idx}. "
            f"Choose a different nickname or remove the existing one first."
        )

    # Remove old nickname for this instance if it exists
    old_nickname = find_nickname(ctx, idx)
    if old_nickname and old_nickname != nickname:
        del ctx.request_context.lifespan_context.instance_nicknames[old_nickname]

    # Assign new nickname
    ctx.request_context.lifespan_context.instance_nicknames[nickname] = idx

    msg = f"Assigned nickname '{nickname}' to instance {idx}"
    if old_nickname and old_nickname != nickname:
        msg += f" (replaced old nickname '{old_nickname}')"

    logger.info(msg)
    return msg


@mcp.tool()
def remove_nickname(
    ctx: Context[ServerSession, AppContext],
    nickname: str,
) -> str:
    """Remove a nickname from an instance.

    This tool removes a previously assigned nickname, making the instance
    accessible only by its index until a new nickname is assigned.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    nickname : str
        Nickname to remove.

    Returns
    -------
    str
        Confirmation message with the removal status.
    """
    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return "No MAPDL pool available."

    instance_idx = ctx.request_context.lifespan_context.instance_nicknames.get(nickname)

    if instance_idx is None:
        return f"Nickname '{nickname}' not found. No changes made."

    del ctx.request_context.lifespan_context.instance_nicknames[nickname]

    logger.info(f"Removed nickname '{nickname}' from instance {instance_idx}")
    return f"Removed nickname '{nickname}' from instance {instance_idx}"
