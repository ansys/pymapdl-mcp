Overview
========

What is PyMAPDL-MCP?
--------------------

PyMAPDL-MCP is a bridge between AI assistants and Ansys MAPDL. It uses the Model Context Protocol (MCP)
to expose PyMAPDL capabilities as standardized tools that AI systems can call.

The Model Context Protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Model Context Protocol (MCP) is a standardized interface for connecting AI systems to external tools and data sources.
It allows AI assistants to:

- Discover available tools and their capabilities
- Call tools with structured parameters
- Receive results and error information
- Maintain state across multiple interactions

How It Works
~~~~~~~~~~~~

1. **Client Connection**: An MCP-compatible client (e.g., Claude) connects to the PyMAPDL-MCP server
2. **Tool Discovery**: The client discovers available tools for controlling MAPDL
3. **Tool Execution**: The client calls tools with appropriate parameters
4. **Result Return**: The server returns results or errors to the client
5. **Interaction Loop**: The cycle continues for the duration of the session

Architecture
------------

PyMAPDL-MCP consists of several key components:

- **MCP Server**: Implements the MCP protocol and handles client connections
- **Tool Registry**: Maintains the list of available tools
- **PyMAPDL Integration**: Wraps PyMAPDL functionality as MCP tools
- **Session Management**: Manages MAPDL instance lifecycle
- **Context Management**: Maintains application state across interactions

Use Cases
---------

**Automated Simulations**
    Use AI to design and run parametric FEA studies automatically

**Interactive Analysis**
    Ask an AI assistant to analyze simulation results and suggest improvements

**Documentation Generation**
    Automatically create reports and documentation from simulations

**Script Debugging**
    Get AI assistance in debugging complex MAPDL scripts

**Learning Tool**
    Use an AI assistant as a tutor for learning MAPDL and FEA concepts

Next Steps
----------

- Learn about available :doc:`tools_and_capabilities`
- Review :doc:`best_practices` for effective use
- Explore :doc:`../api/tools` for technical details
