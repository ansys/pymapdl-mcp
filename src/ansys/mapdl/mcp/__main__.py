"""Entry point for running the MCP server as a module."""

import sys

from ansys.mapdl.mcp.tools import register_tools

def main():
    # Import here to avoid the RuntimeWarning about module loading
    from ansys.mapdl.mcp.server import PyMAPDLMCPServer
    
    # Initialize your MCP server (tools are registered in __init__)
    mcp = PyMAPDLMCPServer(
        name="PyMAPDL"
    )
    register_tools(mcp)
    
    # Run the server
    mcp.run()
    return 0

if __name__ == "__main__":
    sys.exit(main())