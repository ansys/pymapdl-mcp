.. _ref_developing_pymapdl_mcp:

======================
Developing PyMAPDL-MCP
======================

This guide helps you set up your development environment and start contributing code to PyMAPDL-MCP.

Architecture
============

PyMAPDL-MCP is built on the ``PyAnsysBaseMCP`` framework (from ``ansys-common-mcp``), which
is itself built on top of FastMCP. The server lifecycle has three phases:

**Startup**

- Initializes a persistent Python session for custom code execution.
- If ``--connect-on-startup`` is used, connects to an existing MAPDL instance.
- Otherwise, waits for a dynamic connection through the ``connect_to_mapdl`` or
  ``launch_mapdl_session`` tools.

**Runtime**

- Exposes MCP tools for MAPDL interaction.
- Manages dynamic MAPDL connections through the tools.
- Executes commands in both the MAPDL session and the persistent Python session.
- Provides workflow guidance through the ``get_guidelines_for`` context tool.
- Dynamically enables and disables tools based on the MAPDL connection state.

**Shutdown**

- Gracefully disconnects from MAPDL.
- Cleans up the persistent Python session resources.

Application Context
-------------------

The server uses a strongly-typed ``PyMAPDLAppContext`` dataclass that holds:

- The active MAPDL instance connection.
- The persistent Python session for custom code execution.
- Transport configuration (STDIO or HTTP).
- Connection settings (IP, port, auto-connect flags).
- Command history tracking.

Prerequisites
=============

Before you begin, ensure you have:

- Python 3.10 or higher
- Git installed
- A text editor or IDE (VS Code, PyCharm, etc.)
- A GitHub account

Cloning the Repository
======================

1. Fork the repository on GitHub
2. Clone your fork locally:

.. code-block:: bash

   git clone https://github.com/YOUR_USERNAME/pymapdl-mcp.git
   cd pymapdl-mcp

3. Add the upstream repository as a remote:

.. code-block:: bash

   git remote add upstream https://github.com/ansys/pymapdl-mcp.git

Setting Up Your Development Environment
========================================

1. Create a virtual environment:

.. code-block:: bash

   python -m venv .venv

2. Activate the virtual environment:

**On Windows:**

.. code-block:: bash

   .venv\Scripts\activate

**On macOS/Linux:**

.. code-block:: bash

   source .venv/bin/activate

3. Install the package in editable mode with development dependencies:

.. code-block:: bash

   pip install -e .[tests]

4. Install pre-commit hooks:

.. code-block:: bash

   pre-commit install

This ensures code quality checks run automatically before each commit.

Project Structure
=================

.. code-block::

   pymapdl-mcp/
   ├── src/ansys/mapdl/mcp/          # Main package source
   │   ├── __init__.py
   │   ├── __main__.py               # Entry point
   │   ├── contexts.py               # Application context and guidelines
   │   ├── helpers.py                # Utility functions
   │   ├── mcp.py                    # MCP server setup
   │   ├── prompts.py                # Prompt definitions
   │   ├── server.py                 # Server implementation
   │   ├── tools.py                  # MCP tools
   │   └── python_helper/            # Python session helpers
   ├── tests/                        # Test suite
   ├── doc/                          # Documentation
   ├── docker/                       # Docker configuration
   ├── pyproject.toml               # Project metadata
   └── README.md                    # Main README

Development Workflow
====================

1. **Create a feature branch:**

.. code-block:: bash

   git checkout -b feature/your-feature-name

2. **Make your changes:**

   - Edit the relevant files
   - Add or modify tests as needed
   - Update documentation if applicable

3. **Run tests:**

.. code-block:: bash

   # Run unit tests (no MAPDL required)
   pytest -m "not integration"

   # Run all tests with coverage
   pytest --cov=ansys.mapdl.mcp --cov-report=html

4. **Check code quality:**

.. code-block:: bash

   # Run pre-commit checks manually
   pre-commit run --all-files

5. **Commit your changes:**

.. code-block:: bash

   git add .
   git commit -m "feat: Add your feature description"

   # Pre-commit hooks will run automatically

6. **Push to your fork:**

.. code-block:: bash

   git push origin feature/your-feature-name

7. **Create a Pull Request:**

   - Go to the main repository on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Fill in the PR description
   - Submit the PR

Code Conventions
================

Follow these conventions when contributing:

**Branch Naming:**

- Features: ``feature/short-description``
- Fixes: ``fix/short-description``
- Documentation: ``doc/short-description``
- Tests: ``test/short-description``

**Commit Messages:**

Use conventional commits format:

.. code-block:: bash

   feat: Add new tool for XYZ functionality
   fix: Correct handling of edge case
   docs: Update installation instructions
   test: Add tests for feature ABC
   refactor: Simplify tool implementation
   chore: Update dependencies

**Code Style:**

- Follow PEP 8 and the `Coding style <https://dev.docs.pyansys.com/coding-style/index.html>`_
- Use type hints for all functions
- Write docstrings following NumPy style
- Maximum line length: 100 characters
- Format code with Black and isort (run automatically via pre-commit)

Adding a New Tool
=================

To add a new MCP tool to PyMAPDL-MCP:

1. **Edit** ``src/ansys/mapdl/mcp/tools.py``

2. **Add your tool** using the ``@app.tool()`` decorator:

.. code-block:: python

   @app.tool()
   def your_new_tool(ctx: Context, param1: str, param2: int = 10) -> str:
       """
       Brief description of what this tool does.

       Parameters
       ----------
       ctx : Context
           The tool execution context with access to MAPDL
       param1 : str
           Description of param1
       param2 : int, optional
           Description of param2. Default is 10.

       Returns
       -------
       str
           Description of what this tool returns
       """
       mapdl = ctx.application_context.mapdl

       if mapdl is None:
           return "Error: No MAPDL connection available"

       try:
           # Your implementation here
           result = mapdl.your_operation()
           return f"Success: {result}"
       except Exception as e:
           return f"Error: {str(e)}"

3. **Write tests** in ``tests/test_tools.py``

4. **Document the tool** in ``doc/source/api/tools.rst``

5. **Add usage example** if appropriate in ``doc/source/examples/``

Conditionally Enabling or Disabling a Tool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tools can be tagged so they are selectively disabled at runtime. Apply a tag via the
``@app.tool()`` decorator, then call ``app.disable()`` with that tag when the condition
applies (for example, when ``--connect-on-startup`` locks the connection):

.. code-block:: python

   # Tag the tool so it can be disabled as a group
   @app.tool(tags={"locked_connection"})
   def connect_to_mapdl(ctx: Context, port: int = 50052, ip: str = "localhost") -> str:
       ...

   # Disable all tools with this tag when the connection is locked
   app.disable(tags={"locked_connection"})

Adding Documentation
====================

To add or modify documentation:

1. **Edit RST files** in ``doc/source/``

2. **Build documentation locally:**

.. code-block:: bash

   cd doc
   make.bat html    # On Windows
   make html        # On Linux/macOS

3. **View the documentation:**

   Open ``doc/_build/html/index.html`` in your browser

4. **Commit changes** to documentation files

Running Tests
=============

PyMAPDL-MCP includes a comprehensive test suite with 40+ tests.

**Run unit tests (recommended for development):**

.. code-block:: bash

   pytest -m "not integration"

**Run all tests with coverage:**

.. code-block:: bash

   pytest --cov=ansys.mapdl.mcp --cov-report=html

**Run specific test file:**

.. code-block:: bash

   pytest tests/test_tools.py -v

**Run integration tests (requires MAPDL):**

.. code-block:: bash

   pytest -m integration

Test Coverage Goal
~~~~~~~~~~~~~~~~~~

Aim for >80% test coverage on new code:

.. code-block:: bash

   # Generate coverage report
   pytest --cov=ansys.mapdl.mcp --cov-report=html
   # Open htmlcov/index.html to view

Getting Help
============

If you need help during development:

1. **Check existing issues** at `PyMAPDL-MCP Issues <https://github.com/ansys/pymapdl-mcp/issues>`_
2. **Ask in discussions** at `PyMAPDL-MCP Discussions <https://github.com/ansys/pymapdl-mcp/discussions>`_
3. **Review the PyAnsys Developer's Guide** at `PyAnsys Dev Guide <https://dev.docs.pyansys.com/>`_
4. **Check PyMAPDL documentation** at `PyMAPDL Docs <https://mapdl.docs.pyansys.com/>`_

Submitting Your Work
====================

When your feature is ready:

1. Ensure all tests pass: ``pytest -m "not integration"``
2. Ensure code quality: ``pre-commit run --all-files``
3. Update relevant documentation
4. Add tests for new functionality (>80% coverage)
5. Create a Pull Request with:

   - Clear description of changes
   - Reference to related issues (use ``Fixes #123``)
   - List of changes made
   - Any breaking changes noted

Pull Request Guidelines
=======================

- Keep PRs focused on a single feature or fix
- Include tests for new functionality
- Update documentation as needed
- Respond to review feedback
- Keep the PR up-to-date with main branch
- Use "Squash and merge" when possible to keep history clean

Recognition
===========

Contributors are recognized in:

- Pull Request comments
- Release notes
- Contributors file (as applicable)

Thank you for contributing to PyMAPDL-MCP!

See Also
========

- :ref:`ref_contributing` - General contribution guidelines
- :ref:`write_documentation` - Documentation contribution guide
- `PyAnsys Developer's Guide <https://dev.docs.pyansys.com/>`_
