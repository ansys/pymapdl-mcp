"""PyMAPDL MCP Server - Model Context Protocol server for Ansys MAPDL.

This package provides a Model Context Protocol (MCP) server that enables
AI assistants to interact with Ansys MAPDL through PyMAPDL.
"""

__version__ = "0.1.0"

from ansys.mapdl.mcp.mpc import (
    AppContext,
    app_lifespan,
    mcp,
)
from ansys.mapdl.mcp.tools import (
    check_mapdl_status,
    connect_to_mapdl,
    disconnect_from_mapdl,
    list_mapdl_instances,
    run_mapdl_command,
    write_comment,
)

__all__ = [
    "AppContext",
    "app_lifespan",
    "check_mapdl_status",
    "connect_to_mapdl",
    "disconnect_from_mapdl",
    "list_mapdl_instances",
    "mcp",
    "run_mapdl_command",
    "write_comment",
    "__version__",
]
