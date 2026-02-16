Installation
=============

Prerequisites
-------------

- Python 3.10 or later
- Ansys MAPDL installation (for running simulations)
- PyMAPDL (installed automatically as a dependency)

Install from PyPI
-----------------

The easiest way to install PyMAPDL-MCP is through pip:

.. code-block:: bash

   pip install ansys-mapdl-mcp

Install from Source
-------------------

To install from the source repository:

.. code-block:: bash

   git clone https://github.com/ansys/pymapdl-mcp.git
   cd pymapdl-mcp
   pip install -e .

Install Development Dependencies
---------------------------------

If you plan to contribute to development:

.. code-block:: bash

   pip install -e ".[dev]"

For documentation building:

.. code-block:: bash

   pip install -e ".[doc]"

Verify Installation
-------------------

To verify that PyMAPDL-MCP is installed correctly:

.. code-block:: bash

   ansys-mapdl-mcp --help

This should display the command-line help for the MCP server.

Next Steps
----------

- Explore the :doc:`quick_start` guide to launch your first MAPDL instance
- Check out the :doc:`../user_guide/index` for detailed usage instructions
