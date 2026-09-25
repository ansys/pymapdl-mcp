Docker deployment
=================

PyMAPDL-MCP can be deployed as a containerized app using Docker with HTTP
transport for remote access. The server can connect to either a containerized MAPDL
instance or a local MAPDL installation.

.. warning::
   The HTTP transport has **no authentication or encryption**. Any client that can
   reach the port can call every tool with no credential, including
   ``run_python_code`` (arbitrary Python execution) and ``run_mapdl_command``
   (arbitrary APDL, including ``/SYS`` which shells out to the OS). Never publish
   this port on an untrusted network or the public internet. Only expose it beyond
   ``localhost`` if it is placed behind a reverse proxy (such as Nginx or HAProxy)
   that provides both TLS/SSL **and** its own authentication (for example mutual
   TLS or an authenticating gateway). The examples on this page publish the port
   on ``127.0.0.1`` only, so it is not reachable from other machines by default.

Quick start with Docker Compose
-------------------------------

The easiest way to run both MAPDL and the MCP server together is using Docker Compose.

1. Configure the environment:

   .. code-block:: bash

      cp docker/env.example docker/.env

   Edit the ``docker/.env`` file with your settings:

   - ``PYMAPDL_IP``: Set to ``mapdl`` (container), ``host.docker.internal``
     (local Windows/Mac), or the IP address of a remote MAPDL instance.
   - ``ANSYSLMD_LICENSE_FILE``: Your ANSYS license server (format: ``port@server``).

2. Start services:

   .. code-block:: bash

      docker compose -f docker/docker-compose.yml up

   Or run in detached mode:

   .. code-block:: bash

      docker compose -f docker/docker-compose.yml up -d

   The MCP server is available at ``http://localhost:8080``.

Docker Compose services
------------------------

The ``docker-compose.yml`` file defines two services:

- **pymapdl-mcp**: The MCP server with HTTP transport enabled
- **mapdl**: An ANSYS MAPDL container (optional as you can connect to a local instance
  instead)

To connect to a *local* MAPDL instance instead of the container:

#. Remove or comment out the ``mapdl`` service and ``depends_on`` in the ``docker-compose.yml`` file.
#. Set ``PYMAPDL_IP=host.docker.internal`` (Windows/Mac) or the appropriate IP address.
#. Start MAPDL locally: ``pymapdl start --port 50052``.

Build a standalone image
------------------------

To build the MCP server image without Docker Compose, run from the repository root.

On Linux:

.. code-block:: bash

   export GITHUB_TOKEN="your_token_here"
   DOCKER_BUILDKIT=1 docker build --secret id=github_token,env=GITHUB_TOKEN \
     -f docker/Dockerfile -t pymapdl-mcp .

On Windows (PowerShell):

.. code-block:: powershell

   $env:GITHUB_TOKEN = "your_token_here"
   $env:DOCKER_BUILDKIT = "1"
   docker build --secret id=github_token,env=GITHUB_TOKEN `
     -f docker\Dockerfile -t pymapdl-mcp .

Run the standalone container
----------------------------

Connect to a local MAPDL instance:

.. code-block:: bash

   # Windows/Mac
   docker run -p 127.0.0.1:8080:8080 -e PYMAPDL_IP=host.docker.internal pymapdl-mcp

   # Linux
   docker run --network host -e PYMAPDL_IP=localhost pymapdl-mcp

Connect to a remote MAPDL instance:

.. code-block:: bash

   docker run -p 127.0.0.1:8080:8080 \
     -e PYMAPDL_IP=192.168.1.100 \
     -e PYMAPDL_PORT=50053 \
     pymapdl-mcp

.. note::
   ``-p 127.0.0.1:8080:8080`` publishes the port on the loopback interface only,
   so it is reachable from the host machine but not from the network. Do not
   replace this with ``-p 8080:8080`` (equivalent to binding ``0.0.0.0``) unless
   the port is protected as described in the warning above.

   ``--network host`` on Linux exposes the port on every network interface of the
   host, so use it only on trusted, isolated hosts.

Environment variables
---------------------

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Variable
     - Default
     - Description
   * - ``PYMAPDL_IP``
     - ``host.docker.internal``
     - MAPDL IP address or hostname
   * - ``PYMAPDL_PORT``
     - ``50052``
     - MAPDL gRPC port
   * - ``HTTP_HOST``
     - ``0.0.0.0``
     - Bind address *inside* the container. Leave this as ``0.0.0.0`` for Docker's
       port publishing to work; actual network exposure is controlled by the
       ``ports`` mapping in ``docker-compose.yml`` (defaults to ``127.0.0.1`` only)
       or the ``-p`` flag of ``docker run``.
   * - ``HTTP_PORT``
     - ``8080``
     - HTTP server port
   * - ``ANSYSLMD_LICENSE_FILE``
     - *(required)*
     - License server in ``port@server`` format

MCP client configuration
------------------------

Once the container is running, configure your MCP client to connect to the HTTP server.

Visual Studio Code (``.vscode/mcp.json``):

.. code-block:: json

   {
     "servers": {
       "pymapdl": {
         "type": "http",
         "url": "http://localhost:8080"
       }
     }
   }
