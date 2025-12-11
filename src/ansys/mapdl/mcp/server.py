"""Lifespan and CLI entry for the MCP server with startup options."""

import argparse
import sys
from dataclasses import dataclass
from typing import Any, Optional

from ansys.common.mcp import (
    PyAnsysBaseMCP,
    get_logger,
)
from ansys.common.mcp.context import PyAnsysBaseAppContext
from ansys.common.mcp.helpers import PersistentPythonSession

logger = get_logger(__name__)


def _initialize_python_session_encoding(session: PersistentPythonSession) -> None:
    """Initialize the Python session with UTF-8 encoding to prevent charmap issues.

    This ensures that Unicode characters are properly handled in the persistent
    Python session, especially on Windows systems where charmap encoding might
    be the default.

    Parameters
    ----------
    session : PersistentPythonSession
        The persistent Python session to initialize.
    """
    # Set UTF-8 encoding for stdout/stderr
    encoding_setup = """
import sys
import io

# Set UTF-8 encoding for stdout and stderr to handle Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""

    try:
        session.execute(encoding_setup, timeout=5)
        logger.info("Python session encoding initialized to UTF-8")
    except Exception as e:
        logger.warning(f"Could not initialize UTF-8 encoding in Python session: {e}")


@dataclass
class PyMAPDLAppContext(PyAnsysBaseAppContext):
    """Application context with typed dependencies and CLI options.

    Attributes
    ----------
    mapdl : Optional[Any]
        MAPDL instance connection. Using Any to avoid type issues with MAPDL variants.
    transport_type : str
        Transport type for MCP server ('stdio' or 'http').
    mapdl_ip : Optional[str]
        IP address or hostname for MAPDL connection.
    mapdl_port : Optional[int]
        Port number for MAPDL connection.
    connect_on_startup : bool
        Whether to attempt MAPDL connection on MCP startup.
    http_host : str
        Host address for HTTP transport.
    http_port : int
        Port number for HTTP transport.
    cors_origins : Optional[list[str]]
        List of allowed CORS origins for HTTP transport.
    """

    mapdl: Any | None = None  # Using Any to avoid type issues with MAPDL variants
    transport_type: str = "stdio"
    mapdl_ip: str | None = None
    mapdl_port: int | None = None
    connect_on_startup: bool = False
    http_host: str = "127.0.0.1"
    http_port: int = 8080
    cors_origins: list[str] | None = None

    @property
    def product_instance(self) -> Optional[Any]:
        """Returns the default MAPDL instance for backward compatibility.

        Returns
        -------
        Optional[Any]
            The default MAPDL instance from the pool, or None if no pool exists.
        """
        return self.mapdl

    @product_instance.setter
    def product_instance(self, value: Any) -> None:
        """Setter for product_instance (no-op, use pool directly)."""
        pass


class PyMAPDLMCP(PyAnsysBaseMCP):
    """FastMCP server for managing MAPDL instances."""

    def __init__(self, name: str = "PyMAPDL MCP Server", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def create_context(self) -> PyMAPDLAppContext:
        """
        Create a new application context.

        Returns
        -------
        PyMAPDLAppContext
            The application context for managing MAPDL instances.
        """
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
        python_session = PersistentPythonSession(
            python_executable=self.python_executable,
            working_directory=self.working_directory,
            startup_code=startup_code,
        )

        # Initialize Python session with UTF-8 encoding to prevent charmap issues on Windows
        _initialize_python_session_encoding(python_session)

        context = PyMAPDLAppContext(
            python_session=python_session,
            command_history=[],
        )

        # Populate context from CLI config on server if available
        cli_cfg = getattr(self.server, "_cli_config", None)

        if cli_cfg is not None:
            context.transport_type = cli_cfg.get("transport_type", context.transport_type)
            context.mapdl_ip = cli_cfg.get("mapdl_ip", context.mapdl_ip)
            context.mapdl_port = cli_cfg.get("mapdl_port", context.mapdl_port)
            context.connect_on_startup = cli_cfg.get(
                "connect_on_startup", context.connect_on_startup
            )
            context.http_host = cli_cfg.get("http_host", context.http_host)
            context.http_port = cli_cfg.get("http_port", context.http_port)
            context.cors_origins = cli_cfg.get("cors_origins", context.cors_origins)

        self.context = context
        return context

    def product_startup(self):
        """Allow PyMAPDL-MCP specific startup actions."""
        logger.info("PyMAPDL MCP server starting up...")

        context = self.context

        if context.connect_on_startup:
            from ansys.mapdl.core import launch_mapdl

            try:
                logger.info(
                    f"Attempting to connect to MAPDL at {context.mapdl_ip}:{context.mapdl_port}..."
                )
                context.mapdl = launch_mapdl(
                    start_instance=False,
                    ip=context.mapdl_ip,
                    port=context.mapdl_port,
                )
                logger.info("Successfully connected to MAPDL on startup.")

            except Exception as e:
                logger.error(f"Failed to connect to MAPDL on startup: {e}")
        else:
            logger.info("MCP Server initialized. Use connect_to_mapdl to establish a connection.")

    def product_cleanup(self):
        """Perform cleanup actions for MAPDL instances on shutdown."""
        context = self.context
        # Cleanup on shutdown
        if context.mapdl is not None:
            try:
                logger.info("Disconnecting from MAPDL...")
                context.mapdl.exit()
                logger.info("MAPDL disconnect complete")
            except Exception as e:
                logger.error(f"Error during MAPDL disconnect: {e}")


# Pass lifespan to server
app = PyMAPDLMCP(name="PyMAPDL MCP Server")


def add_tool(func):
    """Wrap functions to register them as MCP tools.

    It does return the original function unchanged.
    """
    app.tool(func)

    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapped


def _validate_port(port: int) -> int:
    if port < 1 or port > 65535:
        raise argparse.ArgumentTypeError("Port must be in range 1-65535")
    return port


def main(argv: list[str] | None = None) -> None:
    """Entry point for the MCP server.

    Parameters
    ----------
    argv : list[str] | None
        Optional list of arguments for testing. Defaults to `sys.argv[1:]`.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="ansys.mapdl.mcp")
    parser.add_argument(
        "--transport",
        dest="transport_type",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport type. Allowed: stdio, http",
    )
    parser.add_argument("--ip", dest="mapdl_ip", default="127.0.0.1", help="MAPDL IP or hostname")
    parser.add_argument(
        "--port",
        dest="mapdl_port",
        type=lambda v: _validate_port(int(v)),
        default=50052,
        help="MAPDL gRPC port (1-65535)",
    )
    parser.add_argument(
        "--connect-on-startup",
        dest="connect_on_startup",
        action="store_true",
        help="Attempt to connect to MAPDL during MCP startup",
    )
    parser.add_argument(
        "--http-host",
        dest="http_host",
        default="127.0.0.1",
        help="HTTP server host address (for http transport, default: 127.0.0.1)",
    )
    parser.add_argument(
        "--http-port",
        dest="http_port",
        type=lambda v: _validate_port(int(v)),
        default=8080,
        help="HTTP server port (for http transport, default: 8080, range: 1-65535)",
    )
    parser.add_argument(
        "--cors-origins",
        dest="cors_origins",
        default=None,
        help="Allowed CORS origins (comma-separated URLs, for http transport)",
    )

    args = parser.parse_args(argv)

    # Parse CORS origins if provided
    cors_origins = None
    if args.cors_origins:
        cors_origins = [origin.strip() for origin in args.cors_origins.split(",")]

    # Attach CLI config to server so lifespan can read it
    setattr(
        app,
        "_cli_config",
        {
            "transport_type": args.transport_type,
            "mapdl_ip": args.mapdl_ip,
            "mapdl_port": args.mapdl_port,
            "connect_on_startup": bool(args.connect_on_startup),
            "http_host": args.http_host,
            "http_port": args.http_port,
            "cors_origins": cors_origins,
        },
    )

    # Run server using selected transport
    import asyncio

    if args.transport_type == "stdio":
        asyncio.run(app.run_stdio_async())
    elif args.transport_type == "http":
        asyncio.run(
            app.run_http_async(
                transport="http",  # Use streamable HTTP (default)
                host=args.http_host,
                port=args.http_port,
            )
        )
