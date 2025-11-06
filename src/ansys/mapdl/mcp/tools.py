"""List of tools in PyMAPDL-MCP."""

import logging

from ansys.mapdl.core import Mapdl
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ansys.mapdl.mcp.mpc import AppContext, mcp

logger = logging.getLogger(__name__)


# Access type-safe lifespan context in tools
@mcp.tool()
def check_mapdl_status(ctx: Context[ServerSession, AppContext]) -> str:
    """Check the status of MAPDL initialization.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.

    Returns
    -------
    str
        Status message with MAPDL version information.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."

    return f"MAPDL is available. Version: {mapdl.version}"  # type: ignore[union-attr]


@mcp.tool()
def write_comment(ctx: Context[ServerSession, AppContext], comment: str) -> str:
    """Write a comment in the MAPDL session.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    comment : str
        The comment text to write in MAPDL.

    Returns
    -------
    str
        Confirmation message with the comment execution result.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."

    logger.info(f"Writing comment: {comment}")
    result = mapdl.com(f"{comment}", mute=True)  # type: ignore[union-attr]
    return f"Comment written successfully: {result}"


@mcp.tool()
def run_mapdl_command(ctx: Context[ServerSession, AppContext], cmd: str) -> str:
    """Execute an arbitrary MAPDL command.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    cmd : str
        The MAPDL command to execute.

    Returns
    -------
    str
        Command execution result.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."

    result = mapdl.run(cmd)  # type: ignore[union-attr]
    return f"MAPDL command executed successfully: {result}"


@mcp.tool()
def connect_to_mapdl(
    ctx: Context[ServerSession, AppContext], port: int = 50052, ip: str = "localhost"
) -> str:
    """Connect to an existing MAPDL instance.

    This tool establishes a connection to a running MAPDL instance using the
    provided port and IP address. The connection is stored for subsequent
    operations and can be closed using the disconnect_from_mapdl tool.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    port : int, optional
        The gRPC port where MAPDL is listening. Default is 50052.
    ip : str, optional
        The IP address where MAPDL is running. Default is "localhost".

    Returns
    -------
    str
        Connection status message with MAPDL version information.
    """
    logger.info(f"Connecting to MAPDL instance at {ip}:{port}...")

    try:
        # Check if there's already a connection
        if ctx.request_context.lifespan_context.mapdl is not None:
            return (
                f"Already connected to MAPDL at "
                f"{ctx.request_context.lifespan_context.mapdl._ip}:"
                f"{ctx.request_context.lifespan_context.mapdl._port}. "
                f"Please disconnect first using disconnect_from_mapdl tool."
            )

        # Connect to existing MAPDL instance
        mapdl = Mapdl(
            start_instance=False,
            ip=ip,
            port=port,
            cleanup_on_exit=False,  # Don't clean up since we didn't launch it
            loglevel="INFO",
        )

        # Store in context for later use
        ctx.request_context.lifespan_context.mapdl = mapdl

        logger.info(f"Connected to MAPDL successfully at {ip}:{port}!")
        return (
            f"Successfully connected to MAPDL at {ip}:{port}\n" f"MAPDL Version: {mapdl.version}\n"
        )

    except Exception as e:
        error_msg = f"Failed to connect to MAPDL at {ip}:{port}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def disconnect_from_mapdl(ctx: Context[ServerSession, AppContext]) -> str:
    """Disconnect from the dynamically connected MAPDL instance.

    This tool closes the connection to the MAPDL instance that was established
    using the connect_to_mapdl tool and releases the associated resources.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.

    Returns
    -------
    str
        Disconnection status message.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return "No MAPDL connection to disconnect."

    try:
        ip = mapdl._ip
        port = mapdl._port
        logger.info(f"Disconnecting from MAPDL at {ip}:{port}...")

        # Exit the MAPDL connection
        # Just disconnect the client
        mapdl.exit()
        del mapdl

        # Clear from context
        ctx.request_context.lifespan_context.mapdl = None

        logger.info("Disconnected successfully!")
        return f"Successfully disconnected from MAPDL at {ip}:{port}"

    except Exception as e:
        error_msg = f"Error during disconnect: {str(e)}"
        logger.error(error_msg)
        # Still clear the reference even if disconnect failed
        ctx.request_context.lifespan_context.mapdl = None
        return error_msg


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
