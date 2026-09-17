.. _ref_release_notes:

Release notes
#############

This section contains the release notes for PyMAPDL-MCP.

.. vale off

.. towncrier release notes start

`0.3.0 <https://github.com/ansys/pymapdl-mcp/releases/tag/v0.3.0>`_ - September 17, 2026
========================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Add \`show_plot_on_popup\` parameter to \`screenshot\` tool
          - `#130 <https://github.com/ansys/pymapdl-mcp/pull/130>`_

        * - Add switcher
          - `#144 <https://github.com/ansys/pymapdl-mcp/pull/144>`_

        * - Exposing toolset
          - `#145 <https://github.com/ansys/pymapdl-mcp/pull/145>`_

        * - Add file management tools and resources
          - `#151 <https://github.com/ansys/pymapdl-mcp/pull/151>`_

        * - Expand get_info with components, materials, sections and four-view screenshot
          - `#155 <https://github.com/ansys/pymapdl-mcp/pull/155>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Correct method name from \`input_string\` to \`input_strings\` in screenshot functionality
          - `#149 <https://github.com/ansys/pymapdl-mcp/pull/149>`_

        * - Update Sphinx dependencies for Python version compatibility
          - `#152 <https://github.com/ansys/pymapdl-mcp/pull/152>`_

        * - Update attribute name from 'information' to 'info' in \`get_info\` function
          - `#153 <https://github.com/ansys/pymapdl-mcp/pull/153>`_

        * - Update GitHub token for CI bot in approver workflow
          - `#154 <https://github.com/ansys/pymapdl-mcp/pull/154>`_

        * - Url in readme
          - `#163 <https://github.com/ansys/pymapdl-mcp/pull/163>`_

        * - Cicd
          - `#170 <https://github.com/ansys/pymapdl-mcp/pull/170>`_

        * - Update license information in pyproject.toml
          - `#179 <https://github.com/ansys/pymapdl-mcp/pull/179>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Updates and fixes
          - `#146 <https://github.com/ansys/pymapdl-mcp/pull/146>`_

        * - Update \`\`CONTRIBUTORS.md\`\` with the latest contributors
          - `#167 <https://github.com/ansys/pymapdl-mcp/pull/167>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Support python 3.14
          - `#103 <https://github.com/ansys/pymapdl-mcp/pull/103>`_

        * - Bump actions/checkout from 6.0.2 to 6.0.3 in the actions group
          - `#147 <https://github.com/ansys/pymapdl-mcp/pull/147>`_

        * - Bump the pip-deps group with 2 updates
          - `#158 <https://github.com/ansys/pymapdl-mcp/pull/158>`_, `#159 <https://github.com/ansys/pymapdl-mcp/pull/159>`_, `#176 <https://github.com/ansys/pymapdl-mcp/pull/176>`_

        * - Bump the actions group across 1 directory with 16 updates
          - `#160 <https://github.com/ansys/pymapdl-mcp/pull/160>`_

        * - Bump the pip-deps group across 1 directory with 2 updates
          - `#164 <https://github.com/ansys/pymapdl-mcp/pull/164>`_

        * - Bump the actions group with 17 updates
          - `#165 <https://github.com/ansys/pymapdl-mcp/pull/165>`_, `#175 <https://github.com/ansys/pymapdl-mcp/pull/175>`_

        * - Bump the actions group with 18 updates
          - `#169 <https://github.com/ansys/pymapdl-mcp/pull/169>`_

        * - Bump the actions group with 16 updates
          - `#173 <https://github.com/ansys/pymapdl-mcp/pull/173>`_

        * - Bump the actions group across 1 directory with 15 updates
          - `#177 <https://github.com/ansys/pymapdl-mcp/pull/177>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Update CHANGELOG for v0.2.1
          - `#143 <https://github.com/ansys/pymapdl-mcp/pull/143>`_

        * - Only run bandit on source code
          - `#168 <https://github.com/ansys/pymapdl-mcp/pull/168>`_

        * - Update missing or outdated files
          - `#172 <https://github.com/ansys/pymapdl-mcp/pull/172>`_

        * - Update license metadata in pyproject.toml
          - `#174 <https://github.com/ansys/pymapdl-mcp/pull/174>`_


  .. tab-item:: Miscellaneous

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Rename \`run_multiple_commands\` to \`run_multiple_mapdl_commands\` for consistency
          - `#150 <https://github.com/ansys/pymapdl-mcp/pull/150>`_


`0.2.1 <https://github.com/ansys/pymapdl-mcp/releases/tag/v0.2.1>`_ - June 10, 2026
===================================================================================

.. tab-set::


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Adding pdf build
          - `#141 <https://github.com/ansys/pymapdl-mcp/pull/141>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Update CHANGELOG for v0.2.0
          - `#140 <https://github.com/ansys/pymapdl-mcp/pull/140>`_

        * - Add order for GH and PyPI releases
          - `#142 <https://github.com/ansys/pymapdl-mcp/pull/142>`_


`0.2.0 <https://github.com/ansys/pymapdl-mcp/releases/tag/v0.2.0>`_ - June 09, 2026
===================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Adding changelog
          - `#105 <https://github.com/ansys/pymapdl-mcp/pull/105>`_

        * - Update pre-commit with best practices
          - `#106 <https://github.com/ansys/pymapdl-mcp/pull/106>`_

        * - Replace MIT License with ANSYS MCP Server Technology Preview License Agreement
          - `#113 <https://github.com/ansys/pymapdl-mcp/pull/113>`_

        * - Rename system_prompt to pymapdl_system_prompt for clarity
          - `#114 <https://github.com/ansys/pymapdl-mcp/pull/114>`_

        * - Remove write_comment tool and related documentation
          - `#117 <https://github.com/ansys/pymapdl-mcp/pull/117>`_

        * - Adding \`commands\` argument to screenshot tool
          - `#119 <https://github.com/ansys/pymapdl-mcp/pull/119>`_

        * - Update ansys-common-mcp dependency to version 0.3.0
          - `#121 <https://github.com/ansys/pymapdl-mcp/pull/121>`_

        * - Standardize all tools to return ToolResult
          - `#123 <https://github.com/ansys/pymapdl-mcp/pull/123>`_

        * - Turn off and on tools based on MAPDL connection state
          - `#124 <https://github.com/ansys/pymapdl-mcp/pull/124>`_

        * - Reducing guidelines tools
          - `#126 <https://github.com/ansys/pymapdl-mcp/pull/126>`_

        * - Tech review
          - `#131 <https://github.com/ansys/pymapdl-mcp/pull/131>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Pass real_context to list_mapdl_instances in integration test
          - `#120 <https://github.com/ansys/pymapdl-mcp/pull/120>`_

        * - Auto-clear crashed MAPDL instance on launch/connect
          - `#128 <https://github.com/ansys/pymapdl-mcp/pull/128>`_

        * - List all MAPDL installations in \`check_mapdl_installed\`
          - `#129 <https://github.com/ansys/pymapdl-mcp/pull/129>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Alignment with PyAnsys documentation
          - `#107 <https://github.com/ansys/pymapdl-mcp/pull/107>`_

        * - Fix documentation build + add \`\`doc-deploy-pr\`\`
          - `#109 <https://github.com/ansys/pymapdl-mcp/pull/109>`_

        * - Review to meet style guide
          - `#135 <https://github.com/ansys/pymapdl-mcp/pull/135>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Bump the actions group across 1 directory with 3 updates
          - `#134 <https://github.com/ansys/pymapdl-mcp/pull/134>`_

        * - Bump the actions group across 1 directory with 2 updates
          - `#137 <https://github.com/ansys/pymapdl-mcp/pull/137>`_

        * - Bump the pip-deps group across 1 directory with 5 updates
          - `#138 <https://github.com/ansys/pymapdl-mcp/pull/138>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Enable official release
          - `#139 <https://github.com/ansys/pymapdl-mcp/pull/139>`_


  .. tab-item:: Miscellaneous

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Add prompts system and fix _cli_config propagation
          - `#96 <https://github.com/ansys/pymapdl-mcp/pull/96>`_


.. vale on
