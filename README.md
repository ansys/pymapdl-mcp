# PyMAPDL MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with the ability to interact with Ansys MAPDL (Mechanical APDL) through PyMAPDL. This server enables natural language interaction with MAPDL for finite element analysis tasks.

## Overview

This MCP server bridges the gap between AI assistants and Ansys MAPDL, allowing you to:

- Discover and list running MAPDL instances on your system
- Connect to and disconnect from MAPDL instances dynamically
- Execute MAPDL commands through natural language
- Check MAPDL instance status and version information
- Write comments and run custom commands

## Features

- **Dynamic Connection Management**: Connect to and disconnect from MAPDL instances on demand
- **Instance Discovery**: Automatically discover running MAPDL instances on your system
- **Flexible Deployment**: Supports MAPDL running locally, remotely, or in Docker containers
- **Type-Safe Context**: Strongly typed application context for reliable operations
- **Comprehensive Tools**: Six specialized tools for MAPDL interaction

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
      "args": ["--from", "git+https://github.com/ansys/pymapdl-mcp", "ansys.mapdl.mcp.mcp"]
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
      "args": ["--from", "git+https://github.com/ansys/pymapdl-mcp", "ansys-mapdl-mcp"]
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

## Usage

### Starting the MCP Server

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

**Note**: This tool uses MAPDL's `input_strings` method for batch processing, which is significantly faster than executing commands individually. Perfect for running multiple setup commands or creating complex geometries.

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

### Test Organization

The test suite is organized into focused test modules:

- **conftest.py** - Pytest configuration and shared fixtures (mock MAPDL, contexts)
- **test_basic.py** - Package basics (version, imports, exports, AppContext)
- **test_tools.py** - MCP tools functionality
  - check_mapdl_status tool
  - write_comment tool
  - run_mapdl_command tool
- **test_connection_tools.py** - Connection management tools
  - connect_to_mapdl tool
  - disconnect_from_mapdl tool
  - list_mapdl_instances tool
- **test_integration.py** - MAPDL integration tests
- **test_error_handling.py** - Error scenarios
  - Command failures, timeouts, invalid inputs
- **test_lifespan.py** - Server lifespan management
- **test_mcp_protocol.py** - MCP protocol compliance
- **test_main.py** - Entry point functionality

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

## Project Structure

```
pymapdl-mcp/
├── .github/
│   └── workflows/
│       └── test.yml                    # CI/CD workflow
├── src/
│   └── ansys/
│       └── mapdl/
│           └── mcp/
│               ├── __init__.py         # Package initialization & exports
│               ├── mpc.py              # Main MCP server & lifecycle management
│               ├── tools.py            # MCP tool implementations
│               ├── helpers.py          # Helper functions (instance discovery)
│               ├── prompts.py          # MCP prompts (future use)
│               └── py.typed            # PEP 561 type marker
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures and configuration
│   ├── test_basic.py                   # Basic package tests
│   ├── test_tools.py                   # Core MCP tools tests
│   ├── test_connection_tools.py        # Connection management tests
│   ├── test_error_handling.py          # Error handling tests
│   ├── test_lifespan.py                # Lifespan management tests
│   ├── test_mcp_protocol.py            # MCP protocol tests
│   ├── test_main.py                    # Entry point tests
│   └── test_integration.py             # Integration tests (require MAPDL)
├── .pre-commit-config.yaml             # Pre-commit hooks configuration
├── pyproject.toml                      # Package metadata and dependencies
├── LICENSE                             # MIT License
└── README.md                           # This file
```

## Architecture

The server uses the FastMCP framework with lifespan management:

1. **Startup**: Connects to an existing MAPDL instance
2. **Runtime**: Exposes tools for MAPDL interaction
3. **Shutdown**: Gracefully disconnects from MAPDL

### Adding New Tools

To add new MAPDL tools, edit `src/ansys/mapdl/mcp/mpc.py` and use the `@mcp.tool()` decorator:

```python
@mcp.tool()
def your_new_tool(ctx: Context[ServerSession, AppContext], param: str) -> str:
    """Description of your tool."""
    mapdl = ctx.request_context.lifespan_context.mapdl

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
