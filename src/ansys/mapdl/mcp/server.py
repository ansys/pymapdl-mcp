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
        startup_code = """
import matplotlib
# Use non-interactive backend to prevent blocking on plot displays
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import pyvista as pv
import base64
from io import BytesIO
from PIL import Image

# Enable off-screen rendering globally
pv.OFF_SCREEN = True

# Set a clean default theme
pv.set_plot_theme('document')

def save_plot(plotter, filename='plot.png', return_base64=False):
    '''
    Save PyVista plot to file and optionally return as base64.
    
    Parameters
    ----------
    plotter : pv.Plotter
        The PyVista plotter to save
    filename : str
        Output filename
    return_base64 : bool
        If True, return base64-encoded image data
    
    Returns
    -------
    str
        File path or base64 data URI
    '''
    if return_base64:
        img_array = plotter.screenshot(return_img=True, transparent_background=False)
        plotter.close()
        
        img = Image.fromarray(img_array)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
    else:
        plotter.screenshot(filename, transparent_background=False)
        plotter.close()
        return f"Plot saved to {filename}"

def save_matplotlib_plot(filename='plot.png', return_base64=False, dpi=150):
    '''
    Save matplotlib plot to file and optionally return as base64.
    Uses the current matplotlib figure.
    
    Parameters
    ----------
    filename : str
        Output filename
    return_base64 : bool
        If True, return base64-encoded image data
    dpi : int
        Resolution in dots per inch
    
    Returns
    -------
    str
        File path or base64 data URI
    '''
    if return_base64:
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
    else:
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close()
        return f"Plot saved to {filename}"

# Print confirmation
print("Matplotlib configured with non-interactive backend (Agg)")
print("PyVista configured for off-screen rendering")
"""
        python_session=PersistentPythonSession(
            python_executable=self.python_executable,
            working_directory=self.working_directory,
            startup_code=startup_code
        )
        return PyMAPDLContext(
            python_session=python_session,
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
