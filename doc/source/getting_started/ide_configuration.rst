IDE and Client Configuration
=============================

PyMAPDL-MCP can be integrated with multiple MCP-compatible tools. This guide covers configuration for the most popular clients.

Claude Code
-----------

Claude Code is Anthropic's code editor with built-in MCP support. You can add PyMAPDL-MCP using the CLI.

Project-Level Setup (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure PyMAPDL-MCP for a specific project:

.. code-block:: bash

   cd my-project
   claude mcp add --transport stdio pymapdl -- uvx --from git+https://github.com/ansys/pymapdl-mcp ansys-mapdl-mcp

**Advantages**:
- Configuration is project-specific
- Shareable with team members via version control
- Easy to maintain different configurations per project
- Recommended for collaborative teams

Global User Setup
~~~~~~~~~~~~~~~~~

Configure PyMAPDL-MCP for all your Claude Code projects:

.. code-block:: bash

   claude mcp add --transport stdio --scope user pymapdl -- uvx --from git+https://github.com/ansys/pymapdl-mcp ansys-mapdl-mcp

**Advantages**:
- Available across all your Claude projects
- No per-project configuration needed
- Persistent across different workspaces
- Better for personal development workflows

**Key Features**:
- STDIO transport by default (local integration)
- Automatic fetching from GitHub using `uvx`
- No manual configuration files to manage
- Full MCP protocol support

**Documentation**: `Claude Code MCP Installation <https://code.claude.com/docs/en/mcp#installing-mcp-servers>`_

VS Code
-------

VS Code integrates MCP servers through the Copilot extension using a JSON configuration file.

Quick Start from GitHub
~~~~~~~~~~~~~~~~~~~~~~~

Add this to `.vscode/mcp.json` in your project directory:

.. code-block:: json

   {
     "servers": {
       "pymapdl": {
         "type": "stdio",
         "command": "uvx",
         "args": [
           "--from",
           "git+https://github.com/ansys/pymapdl-mcp",
           "ansys-mapdl-mcp"
         ]
       }
     }
   }

This configuration:
- Uses STDIO transport (recommended for local development)
- Fetches the latest version from GitHub
- Requires `uvx` to be installed on your system

Local Development Setup
~~~~~~~~~~~~~~~~~~~~~~~

For development or testing with local source code:

.. code-block:: json

   {
     "servers": {
       "pymapdl": {
         "type": "stdio",
         "command": "./.venv/bin/python",
         "args": ["-m", "ansys.mapdl.mcp"],
         "env": {
           "FASTMCP_LOG_LEVEL": "DEBUG"
         }
       }
     }
   }

**Features**:
- Uses local Python virtual environment
- Debug logging enabled for troubleshooting
- Ideal for development and testing
- Requires `pip install -e .` in your `.venv`

Alternative: Using `uv`
^^^^^^^^^^^^^^^^^^^^^^^

If you prefer using the `uv` package manager:

.. code-block:: json

   {
     "servers": {
       "pymapdl": {
         "type": "stdio",
         "command": "uv",
         "args": ["run", "python", "-m", "ansys.mapdl.mcp"]
       }
     }
   }

HTTP Transport Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For remote access or web-based clients:

.. code-block:: json

   {
     "servers": {
       "pymapdl": {
         "type": "http",
         "url": "http://127.0.0.1:8080"
       }
     }
   }

**Important**: With HTTP transport, you must start the server separately in a terminal:

.. code-block:: bash

   # Basic HTTP server
   python -m ansys.mapdl.mcp --transport http

   # Custom host and port
   python -m ansys.mapdl.mcp --transport http --http-host 0.0.0.0 --http-port 9000

   # With CORS for web clients
   python -m ansys.mapdl.mcp --transport http --cors-origins "http://localhost:3000"

Enabling MCP in VS Code
~~~~~~~~~~~~~~~~~~~~~~~

1. Open VS Code settings (``Ctrl+,`` or ``Cmd+,``)
2. Search for "MCP" or "Copilot MCP"
3. Enable the setting to allow Copilot to use MCP servers
4. Restart VS Code for changes to take effect

.. image:: ../_static/enable_mcp.png
   :alt: VS Code setting to enable MCP servers
   :align: center

Configuration Locations
^^^^^^^^^^^^^^^^^^^^^^^

- **Project-level**: `.vscode/mcp.json` (repository root)
- **Global**: VS Code user settings (auto-discovered)
- **Workspace**: `.vscode/mcp.json` (workspace-specific)

**Documentation**: `VS Code MCP Servers <https://code.visualstudio.com/docs/copilot/customization/mcp-servers>`_

Claude Desktop
--------------

Claude Desktop is Anthropic's macOS desktop application with full MCP support.

Configuration
~~~~~~~~~~~~~

Edit the file `~/Library/Application Support/Claude/claude_desktop_config.json`:

.. code-block:: json

   {
     "mcpServers": {
       "pymapdl": {
         "command": "uvx",
         "args": [
           "--from",
           "git+https://github.com/ansys/pymapdl-mcp",
           "ansys-mapdl-mcp"
         ],
         "description": "MCP server for Ansys MAPDL through PyMAPDL",
         "version": "0.0.1",
         "language": "python"
       }
     }
   }

**Features**:
- Automatic server detection and initialization
- STDIO transport (default)
- Full MCP tool discovery

**Documentation**: `Claude Desktop MCP Configuration <https://modelcontextprotocol.io/docs/develop/build-server#testing-your-server-with-claude-for-desktop>`_

General MCP Clients
-------------------

Any MCP-compatible client can use PyMAPDL-MCP. The basic requirement is STDIO or HTTP transport support.

STDIO Transport (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For local clients on the same machine:

.. code-block:: bash

   # Start the server
   python -m ansys.mapdl.mcp --transport stdio

Or using `uvx`:

.. code-block:: bash

   uvx --from git+https://github.com/ansys/pymapdl-mcp ansys-mapdl-mcp

HTTP Transport
~~~~~~~~~~~~~~

For remote clients or web-based clients:

.. code-block:: bash

   # Start the server with HTTP
   python -m ansys.mapdl.mcp --transport http --http-host 0.0.0.0 --http-port 8080

   # Configure your client to connect to
   # http://[server-ip]:8080

Comparison: Claude Code vs VS Code
-----------------------------------

.. list-table::
   :header-rows: 1

   * - Feature
     - Claude Code
     - VS Code
   * - Configuration Method
     - CLI command (``claude mcp add``)
     - JSON file (``.vscode/mcp.json``)
   * - Setup Level
     - Project or global (``--scope user``)
     - Project-level only
   * - Manual Config
     - None (auto-managed by CLI)
     - Manual JSON editing required
   * - Transport Support
     - STDIO (default)
     - STDIO or HTTP
   * - Integration
     - Built-in MCP support
     - Requires Copilot extension
   * - Team Sharing
     - Via project config files
     - Via ``.vscode/mcp.json`` in repo
   * - Learning Curve
     - Low (CLI-based)
     - Medium (JSON configuration)

Advanced Configuration
----------------------

Remote MAPDL Connection
~~~~~~~~~~~~~~~~~~~~~~~

Both VS Code and Claude Code support connecting to remote MAPDL instances.

**VS Code (STDIO)**:

.. code-block:: json

   {
     "servers": {
       "pymapdl": {
         "type": "stdio",
         "command": "./.venv/bin/python",
         "args": [
           "-m", "ansys.mapdl.mcp",
           "--connect-on-startup",
           "--ip", "192.168.1.100",
           "--port", "50053"
         ]
       }
     }
   }

**Claude Code**:

.. code-block:: bash

   claude mcp add --transport stdio pymapdl -- \
     python -m ansys.mapdl.mcp \
     --connect-on-startup \
     --ip 192.168.1.100 \
     --port 50053

Debug Logging
~~~~~~~~~~~~~

Enable debug output for troubleshooting:

**VS Code**:

.. code-block:: json

   {
     "servers": {
       "pymapdl": {
         "type": "stdio",
         "command": "./.venv/bin/python",
         "args": ["-m", "ansys.mapdl.mcp"],
         "env": {
           "FASTMCP_LOG_LEVEL": "DEBUG"
         }
       }
     }
   }

**Command line**:

.. code-block:: bash

   FASTMCP_LOG_LEVEL=DEBUG python -m ansys.mapdl.mcp

Docker Integration
~~~~~~~~~~~~~~~~~~

For containerized deployments with HTTP transport:

**VS Code**:

.. code-block:: json

   {
     "servers": {
       "pymapdl": {
         "type": "http",
         "url": "http://localhost:8080"
       }
     }
   }

**Start the container**:

.. code-block:: bash

   docker run -p 8080:8080 \
     -e PYMAPDL_IP=host.docker.internal \
     pymapdl-mcp

See :doc:`../user_guide/overview` for more information about deployment options.

Next Steps
----------

- Review :doc:`../user_guide/tools_and_capabilities` to learn about available tools
- Check :doc:`../api/tools` for complete API reference
- Explore :doc:`../examples/index` for practical usage examples
