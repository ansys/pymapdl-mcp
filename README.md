# PyMAPDL MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with the ability to interact with Ansys MAPDL (Mechanical APDL) through PyMAPDL. This server enables natural language interaction with MAPDL for finite element analysis tasks.

## Overview

This MCP server bridges the gap between AI assistants and Ansys MAPDL, allowing you to:

- Discover and list running MAPDL instances on your system
- Dynamically connect to and disconnect from MAPDL instances
- Execute MAPDL commands through natural language
- Check MAPDL instance status, version information, and connection details
- Write comments and run custom commands

## Features

- **Dynamic Connection Management**: Connect to and disconnect from MAPDL instances on demand
- **Instance Discovery**: Automatically discover running MAPDL instances on your system
- **Flexible Deployment**: Supports MAPDL running locally, remotely, or in Docker containers
- **Type-Safe Context**: Strongly typed application context for reliable operations
- **Comprehensive Tools**: Specialized tools for MAPDL interaction, including enhanced error handling

## Prerequisites

- Python 3.10 or higher
- Ansys MAPDL installation (optional - can connect to remote instances)
- PyMAPDL library (ansys-mapdl-core >= 0.68.0)
- MCP library (mcp >= 0.1.0)

## Quick Start

The quickest way to run the MCP server is to use [`uv`](https://docs.astral.sh/uv/) in your desired software:

### VS Code integration

You should add the following to your `.vscode/mcp.json` file in your project directory:

```json
{
	"servers": {
		"pymapdl": {
			"type": "stdio",
			"command": "uvx",
      		"args": [
				"--from", "git+https://github.com/ansys/pymapdl-mcp", "ansys-mapdl-mcp"
			]
		}
	}
}
```

For more information visit [Use MCP servers in VS Code](https://code.visualstudio.com/docs/copilot/customization/mcp-servers). In this page, you can find information about adding an MCP server globaly to the user.

Make sure you enabled the access to MCPs in your VS Code settings as presented here:
![VS Code settings](enable_mcp.png)

### Claude Desktop

Edit the file `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pymapdl": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/ansys/pymapdl-mcp", "ansys-mapdl-mcp"],
      "description": "A simple MCP server to talk to MAPDL",
      "version": "0.1.0",
      "language": "python"
    }
  }
}
```

For more information, visit [Testing your server with Claude for Desktop](https://modelcontextprotocol.io/docs/develop/build-server#testing-your-server-with-claude-for-desktop).

### Claude Code

You can add PyMAPDL-MCP server to the project in an specific directory with the following commands:

```bash
cd my-project
claude mcp add --transport stdio pymapdl -- uvx --from git+https://github.com/ansys/pymapdl-mcp ansys-mapdl-mcp
```

If you want to add the MCP-server globally on your user, use the following command:

```bash
claude mcp add --transport stdio --scope user pymapdl -- uvx --from git+https://github.com/ansys/pymapdl-mcp ansys-mapdl-mcp
```

For more information, visit [Claude Code Docs-Installing MCP servers](https://code.claude.com/docs/en/mcp#installing-mcp-servers)

### As a standalone Application

You can start the PyMAPDL MCP server as a standalone Python application using `uvx`:

```console
uvx --from git+https://github.com/ansys/pymapdl-mcp ansys-mapdl-mcp			]
```
You can also use your python virtual environment if you have pip installed PyMAPDL MCP server:

```console
./.venv/bin/python -m ansys.mapdl.mcp
```

## Transport Options

PyMAPDL MCP server supports two transport protocols:

### STDIO Transport (Default)

STDIO transport is the default and recommended for local MCP client integration. It communicates via standard input/output streams.

**VS Code Configuration** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "pymapdl": {
      "type": "stdio",
      "command": ".venv\\Scripts\\python.exe",
      "args": ["-m", "ansys.mapdl.mcp"],
      "env": {
        "FASTMCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

**Command Line**:
```console
python -m ansys.mapdl.mcp --transport stdio
```

### HTTP Transport (Streamable HTTP with SSE)

HTTP transport enables remote access to the MCP server over HTTP with Server-Sent Events (SSE), allowing web-based clients and remote integrations.

> [!NOTE]
> **Note**: When using HTTP transport, you must start the MCP server separately before configuring your client. Unlike STDIO transport (which auto-starts the server), HTTP transport requires the server to be running independently.

**VS Code Configuration** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "pymapdl": {
      "type": "http",
      "url": "http://127.0.0.1:8080"
    }
  }
}
```

**Starting the Server**:

First, start the MCP server in a separate terminal:

```console
# Basic HTTP server (localhost:8080)
python -m ansys.mapdl.mcp --transport http

# Custom host and port
python -m ansys.mapdl.mcp --transport http --http-host 0.0.0.0 --http-port 9000

# With CORS origins for web clients
python -m ansys.mapdl.mcp --transport http --cors-origins "http://localhost:3000,https://example.com"
```

**Command Line Options**:
- `--http-host`: HTTP server host address (default: `127.0.0.1`)
- `--http-port`: HTTP server port (default: `8080`, range: 1-65535)
- `--cors-origins`: Comma-separated list of allowed CORS origins (optional)

After starting the server, configure your MCP client to connect to the specified URL (e.g., `http://127.0.0.1:8080`).

### MAPDL Connection Arguments (Works with Both Transports)

The following MAPDL connection arguments work with both STDIO and HTTP transports:

```console
# Connect to MAPDL on startup
python -m ansys.mapdl.mcp --connect-on-startup --ip 192.168.1.100 --port 50053

# With HTTP transport
python -m ansys.mapdl.mcp --transport http --connect-on-startup --ip 192.168.1.100 --port 50053
```

**MAPDL Connection Options**:
- `--ip`: MAPDL IP address or hostname (default: `127.0.0.1`)
- `--port`: MAPDL gRPC port (default: `50052`, range: 1-65535)
- `--connect-on-startup`: Automatically connect to MAPDL when the server starts

## Usage

### Connect to an MAPDL instance

Use the `connect_to_mapdl` tool to establish connections dynamically:

Through your AI assistant:

> "Connect to MAPDL on localhost port 50052"

or

> "Connect to MAPDL on 192.168.1.100 port 50053"

This flexible approach allows you to:

- Connect to different MAPDL instances during a session
- Discover available instances using `list_mapdl_instances` before connecting
- Work with multiple MAPDL servers without restarting the MCP server.

By default, the server connects to MAPDL on `localhost:50052`.

## Run commands

Use `run_mapdl_command` tool to run single MAPDL commands. For instance:

> Run `VPLOT` on the MAPDL instance.

For running multiple commands efficiently, use `run_multiple_commands` tool:

> Run these commands: /PREP7, ET,1,SOLID185, MP,EX,1,200E9

This tool uses MAPDL's `input_strings` method for batch command execution, which is significantly faster than running commands one by one.


## Available Tools

### `check_mapdl_installed`

Check if MAPDL is installed on the system.

**Returns**: Status message indicating whether MAPDL is installed, and if so, the installation path

### `list_mapdl_instances`

Discover all MAPDL instances running on the local machine.

**Returns**: Formatted table with instance information including names, status, gRPC ports, IP addresses, PIDs, and working directories

### `connect_to_mapdl`

Connect to an existing MAPDL instance.

**Parameters**:

- `ip` (string, optional): IP address where MAPDL is running. Default: "localhost"
- `port` (int, optional): gRPC port where MAPDL is listening. Default: 50052

**Returns**: Connection status with MAPDL version information

### `disconnect_from_mapdl`

Disconnect from the currently connected MAPDL instance.

**Returns**: Disconnection status message

### `check_mapdl_status`

Check the status and version of the connected MAPDL instance.

**Returns**: Confirmation of comment execution

### `run_mapdl_command`

Execute arbitrary MAPDL commands.

**Parameters**:

- `cmd` (string): The MAPDL command to execute

**Returns**: Command execution result

### `run_multiple_commands`

Execute multiple MAPDL commands in sequence efficiently.

**Parameters**:

- `commands` (list of strings): List of MAPDL commands to execute

**Returns**: Execution result with summary of commands executed

> [!NOTE]
> **Note**: This tool uses MAPDL's `input_strings` method for batch processing, which is significantly faster than executing commands individually. Perfect for running multiple setup commands or creating complex geometries.

## Development

### Installation From Source

1. Clone the repository:

```bash
git clone https://github.com/ansys/pymapdl-mcp.git
cd pymapdl-mcp
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

3. Install the package:

```bash
pip install -e .
```

This will install the package in editable mode along with all dependencies defined in `pyproject.toml`.

### Development Installation

For development with additional tools (pytest, black, mypy, pre-commit, etc.):

```bash
pip install -e ".[dev]"
```

After installing development dependencies, set up pre-commit hooks:

```bash
pre-commit install
```

This will automatically run code quality checks (black, isort, flake8, mypy, etc.) before each commit.

### Integrating with AI Assistants

This MCP server can be integrated with MCP-compatible AI assistants (like Claude Desktop, etc.). Add the server configuration to your MCP settings file:


#### From PyPI (Coming Soon)

> **⚠️ Note:** The PyPI installation method described below is not yet available. This package has not been published to PyPI. For now, use the development installation methods shown in the sections below.

Once published to PyPI, you'll be able to run the server directly using `uvx`:

<details>
<summary><b>VS Code integration</b></summary>

```json
{
  "servers": {
    "pymapdl": {
      "type": "stdio",
      "command": "uvx",
      "args": ["ansys-mapdl-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>Other tools like Claude Code</b></summary>

```json
{
  "mcpServers": {
    "pymapdl": {
      "command": "uvx",
      "args": ["ansys-mapdl-mcp"]
    }
  }
}
```

</details>

#### From local installation

If you are doing development, you can use the server as it is in the GitHub repository.
To do that, you should clone to a directory.

<details>
<summary><b>VS Code integration</b></summary>

You should add the following to your `.vscode/mcp.json` file:

```json
{
  "servers": {
    "pymapdl": {
      "type": "stdio",
      "command": "./.venv/bin/python",
      "args": ["-m", "ansys.mapdl.mcp"]
		}
	}
}
```

If you prefer `uv`:

```json
{
  "servers": {
    "pymapdl": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "ansys.mapdl.mcp"]
    }
  }
}
```

</details>


<details>
<summary><b>Other tools like Claude Code</b></summary>

```json
{
  "mcpServers": {
    "pymapdl": {
      "command": "/path/to/venv/python",
      "args": ["-m", "ansys.mapdl.mcp"],
    }
  }
}
```
The Python virtual environment should have `pymapdl-mcp` installed.

Or if you prefer `uv`:
```json
{
  "mcpServers": {
    "pymapdl": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/pymapdl-mcp-2", "python", "-m", "ansys.mapdl.mcp"]
    }
  }
}
```

</details>

## Testing

The project includes a comprehensive pytest-based testing suite with 40+ tests covering all functionality.

### Quick set up

Run unit tests (fast, no MAPDL required):

```bash
pytest -m "not integration"
```

Run all tests with coverage:

```bash
pytest --cov=ansys.mapdl.mcp --cov-report=html
```

Run integration tests (requires MAPDL on localhost:50052):

```bash
pytest -m integration
```

### Coverage

Current test coverage: **70%**

- Full coverage on package initialization
- Comprehensive coverage on tool functions
- Integration tests validate real-world usage

### Test Commands Reference

```bash
# Run specific test file
pytest tests/test_tools.py

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov=ansys.mapdl.mcp --cov-report=html
# Open htmlcov/index.html to view

# Run specific test
pytest tests/test_tools.py::TestWriteComment::test_write_comment_success
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Install development dependencies: `pip install -e ".[dev]"`
4. Install pre-commit hooks: `pre-commit install`
5. Make your changes
6. Add tests for new functionality (aim for >80% coverage)
7. Run tests: `pytest -m "not integration"`
8. Commit (pre-commit hooks will run automatically)
9. Push and submit a pull request

The pre-commit hooks and CI will ensure code quality. If hooks fail, review the changes, stage them with `git add .`, and commit again.
pre-commit run --all-files


## Architecture

The server uses the FastMCP framework with lifespan management:

1. **Startup**: Connects to an existing MAPDL instance
2. **Runtime**: Exposes tools for MAPDL interaction
3. **Shutdown**: Gracefully disconnects from MAPDL

### Adding New Tools

To add new MAPDL tools, edit `src/ansys/mapdl/mcp/mcp.py` and use the `@mcp.tool()` decorator:

```python
@mcp.tool()
def your_new_tool(ctx: Context, param: str) -> str:
    """Description of your tool."""
    mapdl = ctx.mapdl

    # Your MAPDL operations here
    result = mapdl.your_command()

    return f"Result: {result}"
```


## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Resources

- [PyMAPDL Documentation](https://mapdl.docs.pyansys.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Ansys MAPDL](https://www.ansys.com/products/structures/ansys-mechanical-apdl)

## Docker Deployment

Deploy PyMAPDL MCP Server as a containerized application with HTTP transport for remote access. The server can connect to either a containerized MAPDL instance or a local MAPDL installation.

> [!WARNING]
> The HTTP transport is not encrypted. Use only in trusted networks or with a reverse proxy (Nginx, HAProxy) providing TLS/SSL.

### Quick Start with Docker Compose

The easiest way to run both MAPDL and the MCP server is using Docker Compose.

**1. Configure environment:**

```bash
# Copy and edit the environment file
cp env.example .env
```

Edit `.env` with your settings:
- `PYMAPDL_IP`: Set to `mapdl` (container), `host.docker.internal` (local Windows/Mac), or IP address (remote)
- `ANSYSLMD_LICENSE_FILE`: Your ANSYS license server

**2. Start services:**

```bash
# Start MAPDL container and MCP server
docker compose up

# Or run in detached mode
docker compose up -d
```

The MCP server will be available at `http://localhost:8080`.

### Docker Compose Configuration

The `docker-compose.yml` includes two services:

- **pymapdl-mcp**: MCP server with HTTP transport
- **mapdl**: ANSYS MAPDL container (optional, can connect to local instance instead)

To connect to a local MAPDL instance instead of the container:
1. Remove or comment out the `mapdl` service and `depends_on` in `docker-compose.yml`
2. Set `PYMAPDL_IP=host.docker.internal` (Windows/Mac)
3. Start MAPDL locally: `pymapdl start --port 50052`

### Building Standalone Image

To build the MCP server image without Docker Compose:

#### On Linux
For the repository root:

```bash
export GITHUB_TOKEN="your_token_here"
DOCKER_BUILDKIT=1 docker build --secret id=github_token,env=GITHUB_TOKEN -f docker/Dockerfile -t pymapdl-mcp .
```

#### On Windows
For the repository root:

```pwsh
$env:GITHUB_TOKEN = "your_token_here"
$env:DOCKER_BUILDKIT=1
docker build --secret id=github_token,env=GITHUB_TOKEN -f docker\Dockerfile -t pymapdl-mcp .
```

### Running Standalone Container

**Connect to local MAPDL:**
```bash
# Windows/Mac
docker run -p 8080:8080 -e PYMAPDL_IP=host.docker.internal pymapdl-mcp

# Linux
docker run --network host -e PYMAPDL_IP=localhost pymapdl-mcp
```

**Connect to remote MAPDL:**
```bash
docker run -p 8080:8080 \
  -e PYMAPDL_IP=192.168.1.100 \
  -e PYMAPDL_PORT=50053 \
  pymapdl-mcp
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYMAPDL_IP` | `host.docker.internal` | MAPDL IP/hostname |
| `PYMAPDL_PORT` | `50052` | MAPDL gRPC port |
| `HTTP_HOST` | `0.0.0.0` | HTTP server host |
| `HTTP_PORT` | `8080` | HTTP server port |
| `ANSYSLMD_LICENSE_FILE` | - | License server (format: `port@server`) |

### MCP Client Configuration

Configure your MCP client to connect to the HTTP server:

**VS Code** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "pymapdl": {
      "type": "http",
      "url": "http://localhost:8080"
    }
  }
}
```

## Support

For issues and questions:

- Open an issue on GitHub
- Consult the PyMAPDL documentation
- Check the Ansys Developer Portal

## Acknowledgments

Built with:

- [PyMAPDL](https://github.com/ansys/pymapdl) - Python interface for MAPDL
- [FastMCP](https://github.com/jlowin/fastmcp) - Fast Model Context Protocol implementation
- [Ansys MAPDL](https://www.ansys.com/) - Finite element analysis software
