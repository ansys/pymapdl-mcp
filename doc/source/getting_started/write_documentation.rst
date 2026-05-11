.. _ref_write_documentation:

===================
Write documentation
===================

Contributing documentation is a valuable way to improve PyMAPDL-MCP for everyone.
This guide explains how to write, build, and submit documentation changes.

Why document?
=============

Good documentation:

- Helps new users get started quickly
- Reduces support questions
- Makes the project more professional
- Creates opportunities for learning
- Builds community engagement

Types of documentation
======================

**API documentation**
    Detailed reference for MCP tools, parameters, return values, and examples.
    Located in ``doc/source/api/``.

**User guides**
    How-to guides, tutorials, and best practices.
    Located in ``doc/source/user_guide/``.

**Getting started**
    Installation, quick start, and initial setup guides.
    Located in ``doc/source/getting_started/``.

**Examples**
    Practical usage examples and tutorials.
    Located in ``doc/source/examples/``.

**API docstrings**
    In-code documentation of functions and classes.
    Located in ``src/ansys/mapdl/mcp/``.

Documentation format
====================

PyMAPDL-MCP documentation uses reStructuredText (RST) format with Sphinx.

Basic RST syntax
~~~~~~~~~~~~~~~~

.. code-block:: rst

   Heading Level 1
   ===============

   Heading Level 2
   ---------------

   Heading Level 3
   ~~~~~~~~~~~~~~~

   **Bold text** and *italic text*

   - Bullet point 1
   - Bullet point 2

   1. Numbered item
   2. Second item

   `Link text <https://example.com>`_

   .. code-block:: python

      # Code block with syntax highlighting
      print("Hello, PyMAPDL-MCP!")

   .. image:: ../images/example.png
       :width: 400
       :align: center
       :alt: Alternative text

Cross-references
~~~~~~~~~~~~~~~~

Link to other documentation pages:

.. code-block:: rst

   See :doc:`../user_guide/overview` for more information.
   Check :ref:`ref_contributing` for contribution guidelines.

Setting up documentation locally
================================

1. **Install documentation dependencies:**

.. code-block:: bash

   pip install -e ".[doc]"

2. **Navigate to doc directory:**

.. code-block:: bash

   cd doc

3. **Build HTML documentation:**

.. code-block:: bash

   make.bat html    # On Windows
   make html        # On Linux/macOS

4. **View in browser:**

   Open ``_build/html/index.html``

Editing documentation
=====================

**Edit existing pages:**

1. Navigate to the RST file in ``doc/source/``
2. Make your changes
3. Save the file
4. Rebuild: ``make html``
5. Review in browser

**Create a new page:**

1. Create a new ``.rst`` file in appropriate directory
2. Write your content
3. Add the file to the parent ``index.rst`` toctree:

.. code-block:: rst

   .. toctree::
      :maxdepth: 2

      existing_page
      your_new_page    # Add this line

4. Build and review: ``make html``

Writing good documentation
==========================

**Be clear and concise**

.. code-block:: rst

   ✓ Good: This tool launches a new MAPDL instance and automatically connects to it.

   ✗ Bad: This tool can be used for launching an instance of MAPDL and making a connection.

**Use Examples**

Include practical code examples:

.. code-block:: rst

   Example
   ~~~~~~~

   .. code-block:: python

      # Launch MAPDL with 4 processors
      mapdl = launch_mapdl_session(nproc=4)

**Explain why, not just how**

.. code-block:: rst

   Use ``run_multiple_commands`` instead of individual commands
   for better performance, as batch execution is significantly faster.

**Structure logically**

- Start with overview
- Progress to specific details
- End with examples or next steps

**Add cross-references**

.. code-block:: rst

   See :doc:`../api/tools` for complete tool reference.
   Learn more in :doc:`../user_guide/best_practices`.

Documenting code
================

Add comprehensive docstrings to functions using NumPy style:

.. code-block:: python

   def launch_mapdl_session(ctx: Context, nproc: int = 4) -> str:
       """
       Launch a new MAPDL instance.

       This tool starts a new MAPDL process and automatically
       establishes a connection to it for immediate use.

       Parameters
       ----------
       ctx : Context
           The tool execution context
       nproc : int, optional
           Number of processors to use. Default is 4.

       Returns
       -------
       str
           Status message with MAPDL version and connection info

       Examples
       --------
       >>> launch_mapdl_session(nproc=4)
       'MAPDL launched with 4 processors'

       Notes
       -----
       This tool is disabled when --connect-on-startup is used.

       See Also
       --------
       connect_to_mapdl : Connect to existing instance
       disconnect_from_mapdl : Close connection
       """
       # Implementation here
       pass

Building documentation
======================

**Clean build (remove old build files):**

.. code-block:: bash

   cd doc
   make.bat clean   # On Windows
   make clean       # On Linux/macOS
   make.bat html    # On Windows
   make html        # On Linux/macOS

**Check for warnings:**

.. code-block:: bash

   # The build output shows warnings and errors
   # Address any RST syntax errors before committing

Documentation testing
=====================

Test that your documentation builds without warnings:

.. code-block:: bash

   cd doc
   make.bat html SPHINXOPTS="-W --keep-going"

The ``-W`` flag treats warnings as errors (useful for CI).

Checking documentation quality
==============================

Before submitting:

1. **No broken links:** Verify all cross-references work
2. **No syntax errors:** Check build output for RST errors
3. **Clear structure:** Use consistent heading levels
4. **Proper formatting:** Check code blocks render correctly
5. **Accurate information:** Verify all examples work
6. **Consistent style:** Match existing documentation style

Common documentation issues
===========================

**Broken cross-reference**

.. code-block:: rst

   ✗ :doc:`../non_existent_page`
   ✓ :doc:`../user_guide/overview`

**Indentation in code blocks**

.. code-block:: rst

   ✗ No blank line before code block
   .. code-block:: python
   def example():
       pass

   ✓ Blank line before code block
   .. code-block:: python

      def example():
          pass

**Unescaped special characters**

.. code-block:: rst

   ✗ Use \* for multiplication
   ✓ Use ``*`` for multiplication

Submitting documentation changes
================================

1. **Make your changes** to RST files
2. **Build locally:** ``make html``
3. **Review in browser:** Open ``_build/html/index.html``
4. **Test links:** Verify all cross-references work
5. **Commit changes:**

.. code-block:: bash

   git add doc/source/
   git commit -m "docs: Update installation instructions"

6. **Create Pull Request** with:

   - Clear description of changes
   - Screenshots if visual changes
   - Link to any related issues

Documentation template
======================

For new pages, use this template:

.. code-block:: rst

   .. _ref_my_page:

   ========
   My Title
   ========

   Brief introduction paragraph explaining what this page covers
   and who should read it.

   Overview
   ========

   High-level explanation of the topic.

   Concepts
   ========

   Explain key concepts and terminology.

   How-To Guide
   ============

   Step-by-step instructions for common tasks.

   Examples
   ~~~~~~~~

   Code examples demonstrating usage.

   Advanced Topics
   ===============

   More complex information or edge cases.

   Troubleshooting
   ===============

   Common issues and solutions.

   See Also
   ========

   - :doc:`related_page1`
   - :doc:`related_page2`

Resources
=========

- `Sphinx Documentation <https://www.sphinx-doc.org/>`_
- `reStructuredText Primer <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_
- `NumPy Docstring Guide <https://numpydoc.readthedocs.io/en/latest/format.html>`_
- `PyAnsys Developer's Guide <https://dev.docs.pyansys.com/>`_

Recognition
===========

Documentation contributors are recognized in:

- Pull Request comments
- Release notes
- Contributors file

Thank you for improving PyMAPDL-MCP documentation!

See also
========

- :ref:`ref_contributing` - General contribution guidelines
- :ref:`ref_developing_pymapdl_mcp` - Code development guide
- `Sphinx <https://www.sphinx-doc.org/>`_ - Documentation generator
