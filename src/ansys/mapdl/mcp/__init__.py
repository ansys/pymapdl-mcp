"""PyMAPDL MCP Server - Model Context Protocol server for Ansys MAPDL.

This package provides a Model Context Protocol (MCP) server that enables
AI assistants to interact with Ansys MAPDL through PyMAPDL.
"""

__version__ = "0.1.0"

from ansys.mapdl.mcp.server import PyMAPDLMCPServer
from ansys.mapdl.mcp.context import PyMAPDLContext
from ansys.mapdl.mcp.tools import register_tools
__all__ = ["PyMAPDLMCPServer", "PyMAPDLContext", "register_tools"]