"""PyMAPDL Application Context for MCP server."""

from ansys.common.mcp.context import PyAnsysBaseAppContext
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class PyMAPDLContext(PyAnsysBaseAppContext):
    """PyMAPDL Application Context for MCP server.
    
    This context extends the base PyAnsys context to provide MAPDL-specific
    functionality. It includes a reference to the MAPDL instance and inherits
    all the base context features like Python session management and command history.
    
    Attributes
    ----------
    mapdl : Optional[Any]
        The connected MAPDL instance. This is the main PyMAPDL object
        that users interact with for finite element analysis.
    
    Examples
    --------
    >>> context = PyMAPDLContext()
    >>> # The mapdl instance will be set when connected
    >>> context.mapdl = launch_mapdl()
    >>> # Set product_instance to reference the same MAPDL instance
    >>> context.product_instance = context.mapdl
    """
    
    mapdl: Optional[Any] = None
