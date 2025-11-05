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

- Python 3.8 or higher
- Ansys MAPDL installation (local or Docker)
- PyMAPDL library
- FastMCP library

## Installation

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

3. Install dependencies:
```bash
pip install .
```

## Usage

### Running MAPDL in Docker

The easiest way to use this MCP server is with MAPDL running in a Docker container:

```bash
docker run -p 50052:50052 --rm -it ghcr.io/ansys/mapdl:latest -grpc
```

### Starting the MCP Server

Run the server in stdio mode:

```bash
python src/mpc.py
```

### Configuration

By default, the server connects to MAPDL on `localhost:50052`. To modify the connection settings, edit the `app_lifespan` function in `src/mpc.py`:

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

```json
{
  "mcpServers": {
    "pymapdl": {
      "command": "python",
      "args": ["/path/to/pymapdl-mcp/src/mpc.py"],
      "cwd": "/path/to/pymapdl-mcp"
    }
  }
}
```

## Testing

The project includes several test scripts to verify functionality:

### Test MAPDL Docker Connection
```bash
python test_docker_connection.py
```
Tests connection to a MAPDL instance running in Docker.

### Test MAPDL Launch
```bash
python test_ansys.py
```
Tests launching a local MAPDL instance.

### Test MCP Server
```bash
python test_mcp_server.py
```
Tests the MCP server lifespan and tool availability.

### Test stdio Communication
```bash
python test_stdio.py
```
Tests the stdio communication protocol.

## Project Structure

```
pymapdl-mcp/
├── src/
│   ├── __init__.py
│   └── mpc.py              # Main MCP server implementation
├── test_ansys.py           # MAPDL launch test
├── test_docker_connection.py  # Docker connection test
├── test_mcp_server.py      # MCP server test
├── test_stdio.py           # stdio protocol test
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Architecture

The server uses the FastMCP framework with lifespan management:

1. **Startup**: Connects to an existing MAPDL instance
2. **Runtime**: Exposes tools for MAPDL interaction
3. **Shutdown**: Gracefully disconnects from MAPDL

The `AppContext` dataclass maintains the MAPDL connection throughout the server's lifecycle, ensuring type-safe access to MAPDL functionality.


## Development

### Adding New Tools

To add new MAPDL tools, use the `@mcp.tool()` decorator:

```python
@mcp.tool()
def your_new_tool(ctx: Context[ServerSession, AppContext], param: str) -> str:
    """Description of your tool."""
    mapdl = ctx.request_context.lifespan_context.mapdl
    
    # Your MAPDL operations here
    result = mapdl.your_command()
    
    return f"Result: {result}"
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

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
