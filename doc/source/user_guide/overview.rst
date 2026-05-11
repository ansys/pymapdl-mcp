Overview
========

What is PyMAPDL-MCP?
--------------------

PyMAPDL-MCP is a bridge between AI assistants and Ansys MAPDL. It uses the Model Context Protocol (MCP)
to expose PyMAPDL capabilities as standardized tools that AI systems can call.

The Model Context Protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~

The Model Context Protocol (MCP) is a standardized interface for connecting AI systems to external tools and data sources.
It allows AI assistants to:

- Discover available tools and their capabilities
- Call tools with structured parameters
- Receive results and error information
- Maintain state across multiple interactions

How it works
~~~~~~~~~~~~

1. **Client connection**: An MCP-compatible client (for example, Claude) connects to the PyMAPDL-MCP server
2. **Tool discovery**: The client discovers available tools for controlling MAPDL
3. **Tool execution**: The client calls tools with appropriate parameters
4. **Result return**: The server returns results or errors to the client
5. **Interaction loop**: The cycle continues for the duration of the session

Architecture
------------

PyMAPDL-MCP consists of several key components:

- **MCP server**: Implements the MCP protocol and handles client connections
- **Tool registry**: Maintains the list of available tools
- **PyMAPDL integration**: Wraps PyMAPDL features as MCP tools
- **Session management**: Manages MAPDL instance lifecycle
- **Context management**: Maintains app state across interactions

Use cases
---------

**Automated simulations**
    Use AI to design and run parametric FEA studies automatically

**Interactive analysis**
    Ask an AI assistant to analyze simulation results and suggest improvements

**Documentation generation**
    Automatically create reports and documentation from simulations

**Script debugging**
    Get AI assistance in debugging complex MAPDL scripts

**Learning tool**
    Use an AI assistant as a tutor for learning MAPDL and FEA concepts

Next steps
----------

- Learn about available :doc:`tools_and_capabilities`
- Review :doc:`best_practices` for effective use
- Explore :doc:`../api/tools` for technical details
