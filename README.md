# PyMAPDL MCP Server

[![PyAnsys](https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5+OQgMJ/0AqCqXGQMEBAwBEKQj5gGDjQsA80UeCDscxrD4YhGsgABEELnC5zAwAu6ACKQDAQzNBFwAAVdgFEAnfDiQAATyIBaAFgCbkAI5DQwAVGAYkAMA4gHgg2AC+AAgQIABggagAqyAD4AACkR7cEdcEBQOPjIvAEtRDoAbYLANQAZGsBEAFeBwCsAY0HgGCAAEQTaDj7xQABItJ+S3DsQAAAABJRU5ErkJggg==)](https://docs.pyansys.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Apache](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

PyMAPDL MCP Server provides a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
server that enables AI assistants to interact with Ansys MAPDL (Mechanical APDL) through
[PyMAPDL](https://mapdl.docs.pyansys.com/). This server enables natural language interaction with MAPDL for finite element analysis tasks.

## Overview

Key features:

- **Dynamic connection management**: Launch new MAPDL instances, connect to existing ones, or disconnect on demand
- **Execute MAPDL commands**: Run single commands or batch multiple commands for efficiency
- **Custom Python execution**: Run arbitrary Python and PyMAPDL code in a persistent session
- **Advanced visualization**: Create custom matplotlib and PyVista plots, or capture MAPDL native plots
- **Workflow guidance**: Access comprehensive context and best practices for all phases of MAPDL simulations
- **Flexible deployment**: Works with MAPDL running locally, remotely, or in Docker containers

## Installation

### For users

Install the latest release with:

```bash
pip install ansys-mapdl-mcp
```

Or run directly without installing using [`uvx`](https://docs.astral.sh/uv/):

```bash
uvx --from git+https://github.com/ansys/pymapdl-mcp ansys-mapdl-mcp
```

### For developers

```bash
git clone https://github.com/ansys/pymapdl-mcp.git
cd pymapdl-mcp
pip install -e .[tests]
```

## Quick start

Add PyMAPDL-MCP to VS Code by creating a `.vscode/mcp.json` file in your project:

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

For more information visit [Use MCP servers in VS Code](https://code.visualstudio.com/docs/copilot/customization/mcp-servers). In this page, you can find information about adding an MCP server globally to the user.

Make sure you enabled the access to MCPs in your VS Code settings as presented here:
![VS Code settings](enable_mcp.png)

For Claude Desktop, Claude Code, HTTP transport, Docker deployment, and full CLI reference,
see the [PyMAPDL-MCP documentation](https://mapdl-mcp.docs.pyansys.com).
## License

This project is licensed under the Apache 2.0 license agreement. See the [LICENSE](./LICENSE) file for details.

## Resources

- [PyMAPDL-MCP documentation](https://mapdl-mcp.docs.pyansys.com)
- [PyMAPDL Documentation](https://mapdl.docs.pyansys.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Ansys MAPDL](https://www.ansys.com/products/structures/ansys-mechanical-apdl)
- [Repository's Issues page](https://github.com/ansys/pymapdl-mcp/issues)
- [Repository's Discussions page](https://github.com/ansys/pymapdl-mcp/discussions)

For general PyAnsys questions, email [pyansys.core@ansys.com](mailto:pyansys.core@ansys.com).
