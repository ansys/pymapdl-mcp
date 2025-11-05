# PyMAPDL MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with the ability to interact with Ansys MAPDL (Mechanical APDL) through PyMAPDL. This server enables natural language interaction with MAPDL for finite element analysis tasks.

## Overview

This MCP server bridges the gap between AI assistants and Ansys MAPDL, allowing you to:
- Execute MAPDL commands through natural language
- Check MAPDL instance status
- Write comments and run preprocessing commands
- Interact with MAPDL running locally or in Docker containers

## Features

- **Lifespan Management**: Automatic connection and disconnection from MAPDL instances
- **Docker Support**: Connects to MAPDL instances running in Docker containers
- **Type-Safe Context**: Strongly typed application context for reliable operations
- **Multiple Tools**: Pre-built tools for common MAPDL operations
- **Error Handling**: Graceful fallback and comprehensive error reporting

## Quick Start

```bash
# 1. Make sure you have MAPDL
/ansys_inc/vxXX/ansys/bin/ansysXXX -grpc

# 2. Install the package
pip install -e .

# 3. Run the MCP server
ansys-mapdl-mcp
```

## Available Tools

### `check_mapdl_status`
Check the status and version of the connected MAPDL instance.

**Returns**: MAPDL version information

### `say_hi`
Test tool that executes the `prep7` preprocessor command.

**Returns**: Result of the prep7 command execution

### `write_comment`
Write a comment in the MAPDL session.

**Parameters**:
- `comment` (string): The comment text to write

**Returns**: Confirmation of comment execution

### `run_mapdl_command`
Execute arbitrary MAPDL commands.

**Parameters**:
- `cmd` (string): The MAPDL command to execute

**Returns**: Command execution result

## Prerequisites

- Python 3.10 or higher
- Ansys MAPDL installation (local or Docker)
- PyMAPDL library
- FastMCP library

## Installation

### From Source

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

## Usage

### Starting the MCP Server

After installation, you can run the server in multiple ways:

**Option 1: Using the installed console script (recommended):**
```bash
ansys-mapdl-mcp
```

**Option 2: Using Python module execution:**
```bash
python -m ansys.mapdl.mcp.mpc
```

**Option 3: Direct script execution:**
```bash
python src/ansys/mapdl/mcp/mpc.py
```

### Configuration

By default, the server connects to MAPDL on `localhost:50052`. To modify the connection settings, edit the `app_lifespan` function in `src/ansys/mapdl/mcp/mpc.py`:

```python
mapdl = Mapdl(
    start_instance=False,
    ip="localhost",        # Change to your MAPDL host
    port=50052,           # Change to your MAPDL port
    cleanup_on_exit=False,
    loglevel="DEBUG",
    log_apdl="/path/to/your/mapdl.log"
)
```

### Integrating with AI Assistants

This MCP server can be integrated with MCP-compatible AI assistants (like Claude Desktop, etc.). Add the server configuration to your MCP settings file:

**Using the installed package (recommended):**
```json
{
  "mcpServers": {
    "pymapdl": {
      "command": "ansys-mapdl-mcp"
    }
  }
}
```

**Using Python module execution:**
```json
{
  "mcpServers": {
    "pymapdl": {
      "command": "python",
      "args": ["-m", "ansys.mapdl.mcp.mpc"]
    }
  }
}
```

**Using direct script execution (development):**
```json
{
  "mcpServers": {
    "pymapdl": {
      "command": "/path/to/venv/python",
      "args": ["-m", "ansys.mapdl.mcp.mpc"],
    }
  }
}
```
The Python virtual environment should have `pymapdl-mcp` installed.

## Testing

The project includes a comprehensive pytest-based testing suite with 40+ tests covering all functionality.

### Quick Start

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
- **test_tools.py** - MCP tools functionality (12 tests)
  - check_mapdl_status tool
  - write_comment tool
  - run_mapdl_command tool
- **test_error_handling.py** - Error scenarios (7 tests)
  - Command failures, timeouts, invalid inputs
- **test_lifespan.py** - Server lifespan management (5 tests)
- **test_mcp_protocol.py** - MCP protocol compliance (6 tests)
- **test_main.py** - Entry point functionality (3 tests)
- **test_integration.py** - Integration tests with real MAPDL (4 tests)
  - Requires MAPDL on localhost:50052
  - Automatically skipped if unavailable

### Coverage

Current test coverage: **66%**
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

## Development

### Quick Start for Developers

1. **Clone and setup**
```bash
git clone https://github.com/ansys/pymapdl-mcp.git
cd pymapdl-mcp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

2. **Install pre-commit hooks** (important!)
```bash
pre-commit install
```

3. **Make changes and test**
```bash
# Edit code...
pytest -m "not integration"  # Run tests
```

4. **Commit** (pre-commit hooks run automatically)
```bash
git add .
git commit -m "feat: your feature description"
```

### Code Quality

## CI/CD

GitHub Actions automatically run on pull requests and pushes:

### Test Job
- **Platforms**: Ubuntu, Windows (macOS only on tags)
- **Python versions**: 3.10, 3.11, 3.12
- **Coverage**: Unit tests with coverage reporting

### Lint Job
- Black formatting check
- isort import sorting check
- mypy type checking

### Integration Job
- Integration tests (gracefully skips if MAPDL unavailable)

See `.github/workflows/test.yml` for full configuration.

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

# Run specific checks
black src tests
isort src tests
mypy src/ansys/mapdl/mcp
```

### Package Structure

The package follows the Ansys namespace convention (`ansys.mapdl.mcp`) and is configured using modern Python packaging standards with `pyproject.toml`.
```bash
python test_stdio.py
```
Tests the stdio communication protocol.

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
│               ├── __init__.py         # Package initialization
│               ├── mpc.py              # Main MCP server implementation
│               └── py.typed            # PEP 561 type marker
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures and configuration
│   ├── test_basic.py                   # Basic package tests
│   ├── test_tools.py                   # MCP tools tests
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

The `AppContext` dataclass maintains the MAPDL connection throughout the server's lifecycle, ensuring type-safe access to MAPDL functionality.


## Development

### Package Structure

The package follows the Ansys namespace convention (`ansys.mapdl.mcp`) and is configured using modern Python packaging standards with `pyproject.toml`.

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

### Building the Package

To build distribution packages:
```bash
pip install build
python -m build
```

This creates both wheel and source distributions in the `dist/` directory.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -e ".[dev]"`
4. Make your changes
5. Format code with `black` and `isort`
6. Add tests for new functionality
7. Run tests to ensure everything works
8. Submit a pull request

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
