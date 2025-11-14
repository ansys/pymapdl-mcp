"""PyMAPDL MCP Server - Model Context Protocol server for Ansys MAPDL.

This package provides a Model Context Protocol (MCP) server that enables
AI assistants to interact with Ansys MAPDL through PyMAPDL.
"""

__version__ = "0.1.0"

# Import contexts module to register context tools with the MCP server
from ansys.mapdl.mcp import contexts  # noqa: F401
from ansys.mapdl.mcp.mcp import (
    AppContext,
    app_lifespan,
    mcp,
)
from ansys.mapdl.mcp.tools import (
    check_mapdl_installed,
    check_mapdl_status,
    connect_to_mapdl,
    disconnect_from_mapdl,
    launch_mapdl,
    list_mapdl_instances,
    run_mapdl_command,
    run_multiple_commands,
    write_comment,
)

__all__ = [
    "AppContext",
    "app_lifespan",
    "check_mapdl_installed",
    "check_mapdl_status",
    "connect_to_mapdl",
    "disconnect_from_mapdl",
    "launch_mapdl",
    "list_mapdl_instances",
    "mcp",
    "run_mapdl_command",
    "run_multiple_commands",
    "write_comment",
    "__version__",
]
