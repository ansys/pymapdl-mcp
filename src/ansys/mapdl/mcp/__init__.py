"""PyMAPDL MCP Server - Model Context Protocol server for Ansys MAPDL.

This package provides a Model Context Protocol (MCP) server that enables
AI assistants to interact with Ansys MAPDL through PyMAPDL. By default,
it is configured to use PyMAPDL code unless a clear statement is made to
use APDL code or for plotting MAPDL/PyMAPDL plots.

"""

__version__ = "0.1.0"

# Import contexts module to register context tools with the MCP server
from ansys.mapdl.mcp.server import (
    app,
    main,
)

__all__ = [
    "app",
    "main",
    "__version__",
]
