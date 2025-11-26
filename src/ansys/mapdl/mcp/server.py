from ansys.common.mcp.server import PyAnsysBaseMCP
from ansys.common.mcp.helpers import PersistentPythonSession
from typing import Any, Optional
from .context import PyMAPDLContext

class PyMAPDLMCPServer(PyAnsysBaseMCP):
    """PyMAPDL MCP Server - Model Context Protocol server for Ansys MAPDL.

    This class implements a Model Context Protocol (MCP) server that enables
    AI assistants to interact with Ansys MAPDL through PyMAPDL.
    """
    def create_context(self) -> PyMAPDLContext:
        """Create and return a new PyMAPDL application context."""
        return PyMAPDLContext(
            python_session=PersistentPythonSession(
                python_executable=self.python_executable,
                working_directory=self.working_directory,
            ),
            command_history=[],
        )

    def product_startup(self):
        """Perform any necessary startup operations when the server starts."""
        # Add any PyMAPDL-specific startup operations here
        pass

    def product_cleanup(self):
        """Perform any necessary cleanup operations before shutting down the server."""
        # Add any PyMAPDL-specific cleanup operations here
        if hasattr(self, 'context') and self.context and self.context.mapdl:
            try:
                self.context.mapdl.exit()
            except:
                pass  # Ignore errors during cleanup

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the PyMAPDL MCP server."""
        super().__init__(*args, **kwargs)
