Quick Start
===========

Launching PyMAPDL-MCP
---------------------

The simplest way to start the MCP server is:

.. code-block:: bash

   ansys-mapdl-mcp

This will launch the server using the default STDIO transport and wait for connections from MCP clients.

Configuring Your IDE or Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyMAPDL-MCP works with multiple MCP-compatible clients. See :doc:`ide_configuration` for detailed setup instructions for:

- **Claude Code** (recommended for AI-assisted development)
- **VS Code with Copilot** (for VS Code users)
- **Claude Desktop** (macOS application)
- Other MCP-compatible clients

Transport Options
-----------------

PyMAPDL-MCP supports two transport protocols.

STDIO Transport (Default)
~~~~~~~~~~~~~~~~~~~~~~~~~

STDIO transport is the default and recommended for local MCP client integration.
It communicates via standard input/output streams, so the MCP client manages the
server process automatically.

Start with STDIO explicitly:

.. code-block:: bash

   python -m ansys.mapdl.mcp --transport stdio

HTTP Transport
~~~~~~~~~~~~~~

HTTP transport enables remote access over HTTP with Server-Sent Events (SSE), allowing
web-based clients and remote integrations.

.. note::
   With HTTP transport, you must start the MCP server separately **before** configuring
   your client. Unlike STDIO, the client does not auto-start the server.

Start the HTTP server:

.. code-block:: bash

   # Basic HTTP server (localhost:8080)
   python -m ansys.mapdl.mcp --transport http

   # Custom host and port
   python -m ansys.mapdl.mcp --transport http --http-host 0.0.0.0 --http-port 9000

   # With CORS origins for web clients
   python -m ansys.mapdl.mcp --transport http --cors-origins "http://localhost:3000,https://example.com"

Then configure your MCP client to connect to the HTTP URL, for example in
``.vscode/mcp.json``:

.. code-block:: json

   {
     "servers": {
       "pymapdl": {
         "type": "http",
         "url": "http://127.0.0.1:8080"
       }
     }
   }

.. warning::
   HTTP transport is not encrypted. Use only in trusted networks or behind a
   reverse proxy (for example, Nginx or HAProxy) that provides TLS/SSL.

Command-Line Reference
----------------------

Transport Options
~~~~~~~~~~~~~~~~~

- ``--transport {stdio,http}``: Transport type. Default: ``stdio``

MAPDL Connection Options
~~~~~~~~~~~~~~~~~~~~~~~~~

These options work with both STDIO and HTTP transports.

- ``--ip``: MAPDL IP address or hostname. Default: ``127.0.0.1``
- ``--port``: MAPDL gRPC port. Default: ``50052`` (range: 1-65535)
- ``--connect-on-startup``: Automatically connect to MAPDL when the server starts

.. code-block:: bash

   # Connect to MAPDL on startup
   python -m ansys.mapdl.mcp --connect-on-startup --ip 192.168.1.100 --port 50053

.. warning::
   When ``--connect-on-startup`` is used, the connection is locked. The
   ``launch_mapdl_session``, ``connect_to_mapdl``, and ``disconnect_from_mapdl``
   tools are disabled.

HTTP-Specific Options
~~~~~~~~~~~~~~~~~~~~~

- ``--http-host``: HTTP server host address. Default: ``127.0.0.1``
- ``--http-port``: HTTP server port. Default: ``8080`` (range: 1-65535)
- ``--cors-origins``: Comma-separated list of allowed CORS origins (optional)

Special Environment Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``--on-aali``: Specifies that the server is running on an AALI environment.
  This disables tools that are not compatible with AALI.

Basic Workflow
--------------

Starting a MAPDL Instance
~~~~~~~~~~~~~~~~~~~~~~~~~~

There are three ways to connect to MAPDL once the MCP server is running.

**Option 1 — Launch a new MAPDL instance (recommended)**

Ask your AI assistant to use the ``launch_mapdl_session`` tool:

   *"Launch a new MAPDL instance"*

   *"Launch MAPDL with 4 processors in /tmp/mapdl_work"*

This starts a new MAPDL process and connects to it automatically. It lets you
specify custom settings (number of processors, working directory, etc.) without
any manual setup.

**Option 2 — Connect to an existing instance**

Ask your AI assistant to use the ``connect_to_mapdl`` tool:

   *"Connect to MAPDL on localhost port 50052"*

   *"Connect to MAPDL on 192.168.1.100 port 50053"*

You can first ask it to run ``list_mapdl_instances`` to discover what is running.
This option is useful for connecting to different instances during a session or
when MAPDL is already running on a remote machine.

**Option 3 — Auto-connect on server startup**

Pass ``--connect-on-startup`` when starting the MCP server:

.. code-block:: bash

   python -m ansys.mapdl.mcp --connect-on-startup --ip 127.0.0.1 --port 50052

.. warning::
   When ``--connect-on-startup`` is used, the connection is locked. The
   ``launch_mapdl_session``, ``connect_to_mapdl``, and ``disconnect_from_mapdl``
   tools are disabled.

Running Commands and Extracting Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once MAPDL is connected, you can use MCP tools to:

1. **Run commands**: Execute MAPDL commands through PyMAPDL
2. **Extract data**: Retrieve results and analysis data
3. **Visualize**: Generate plots and screenshots
4. **Control**: Manage the MAPDL session lifecycle

Example Use Cases
~~~~~~~~~~~~~~~~~

- Running parametric studies with AI guidance
- Analyzing FEA results automatically
- Generating documentation from simulations
- Debugging MAPDL scripts with AI assistance

Next Steps
----------

For more detailed information:

- See :doc:`../user_guide/overview` for an overview of available tools
- Check :doc:`../api/tools` for the complete API reference
- Browse :doc:`../examples/index` for practical examples
- See :doc:`../user_guide/docker` for containerized deployment
