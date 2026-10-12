Tools and capabilities
======================

Tool availability
-----------------

PyMAPDL-MCP dynamically enables and disables tools based on whether an MAPDL instance is
connected. This keeps the AI assistant's context small when MAPDL is not in use.
Connection state is shared by the application. Connecting or disconnecting changes tool
availability for all clients, not only the client that changes the connection.

**Before connecting to MAPDL**, you can access these tools:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Tool
     - Description
   * - ``check_mapdl_installed``
     - Check if MAPDL is installed on the system
   * - ``list_mapdl_instances``
     - Discover running MAPDL instances
   * - ``connect_to_mapdl``
     - Connect to an existing MAPDL instance
   * - ``launch_mapdl_session``
     - Launch and connect to a new MAPDL instance
   * - ``get_guidelines_for``
     - Workflow guidance and best-practice context tool
   * - ``list_command_logs``
     - List native client command log IDs, even after disconnect
   * - ``read_command_log``
     - Read a bounded base64 byte page from a known command log

**After connecting to MAPDL**, you gain access to the tools allowed by startup policy.
When you call ``disconnect_from_mapdl``, the MAPDL-specific tools become unavailable.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Tool
     - Description
   * - ``check_mapdl_status``
     - Get comprehensive MAPDL status
   * - ``run_mapdl_command``
     - Execute a single MAPDL command
   * - ``run_multiple_mapdl_commands``
     - Execute multiple MAPDL commands in batch
   * - ``disconnect_from_mapdl``
     - Disconnect from the MAPDL instance
   * - ``screenshot``
     - Capture the MAPDL graphics window as a static image
   * - ``run_python_code``
     - Execute Python/PyMAPDL code in a persistent session
   * - ``custom_plot``
     - Create custom matplotlib or PyVista plots
   * - ``upload_file``
     - Upload a local file to the MAPDL working directory
   * - ``download_file``
     - Download a file from the MAPDL working directory
   * - ``resume_model``
     - Restore a saved model from a ``.db`` or ``.cdb`` file
   * - ``open_results``
     - Enter POST1 and set the active results file for post-processing

.. note::
   When you use ``--connect-on-startup``, MAPDL connects at startup and permitted tools
   are immediately available. ``connect_to_mapdl``, ``launch_mapdl_session``, and
   ``disconnect_from_mapdl`` are locked. Python-off remains effective after startup.

Tool sets
---------

PyMAPDL-MCP groups tools into logical tool sets so MCP clients can discover capabilities by role.
These sets are exposed through the ``toolsets://definition`` resource.

.. list-table::
   :header-rows: 1
   :widths: 20 45 35

   * - Tool set
     - Purpose
     - Tools included
   * - ``session_management``
     - Manage MAPDL lifecycle and connection state
     - ``check_mapdl_installed``, ``check_mapdl_status``, ``launch_mapdl_session``,
       ``connect_to_mapdl``, ``disconnect_from_mapdl``, ``list_mapdl_instances``
   * - ``file_management``
     - Transfer files to/from MAPDL and manage saved models
     - ``upload_file``, ``download_file``, ``resume_model``, ``open_results``
   * - ``command_execution``
     - Execute MAPDL commands and command batches
     - ``run_mapdl_command``, ``run_multiple_mapdl_commands``, ``run_python_code``,
       ``list_command_logs``, ``read_command_log``
   * - ``visualization``
     - Capture or generate result visualizations
     - ``screenshot``, ``custom_plot``
   * - ``python_execution``
     - Execute arbitrary Python or PyMAPDL code in the persistent session
     - ``run_python_code``, ``custom_plot``

The ``list_tool_sets(ctx)`` resource function reads the request's startup policy.
With Python disabled, it omits both Python tools, their recommendations, and the empty
``python_execution`` set. Native screenshot guidance remains available.

Using the tools
---------------

Running MAPDL commands
~~~~~~~~~~~~~~~~~~~~~~

Use ``run_mapdl_command`` for single commands:

*"Run VPLOT on the MAPDL instance."*

For multiple commands, use ``run_multiple_mapdl_commands``, which uses MAPDL's ``input_strings``
method for batch execution. This is significantly faster than running commands one by one:

*"Run these commands: /PREP7, ET,1,SOLID185, MP,EX,1,200E9."*

Direct APDL restrictions
~~~~~~~~~~~~~~~~~~~~~~~~

APDL is unrestricted by default. Operators can block selected direct command families
at startup without changing command logging or Python capability:

.. code-block:: bash

   python -m ansys.mapdl.mcp --block-apdl-command /SYS --block-apdl-command /SYP --block-apdl-command /INPUT

The repeatable option accepts only ``/SYS``, ``/SYP``, and ``/INPUT``. Each family
is independent. The checker reads the first comma-delimited command-head field and
trims its outer Unicode whitespace before quote recognition. This matches PyMAPDL's
downstream Python ``strip()`` boundary, including nonbreaking and em spaces; it does
not establish additional solver syntax. For unquoted heads, the checker removes only
internal ASCII spaces and tabs before case-insensitive significant-prefix matching.
Other internal head whitespace fails closed when restricted rather than assuming
the solver ignores it. A matching pair of single or double quotes around a whole head
is removed for classification only. Quoted heads containing whitespace or further
quotes, and malformed or mixed head quotes, fail closed in restricted mode.
Unicode in ordinary arguments or filename data is not generically banned.
The significant first four label characters match, including ``/INP`` and trailing
ignored spelling for ``/INPUT``. Shorter guessed abbreviations are not aliases.
Allowed dispatch text is unchanged apart from the batch tool's existing outer trimming.

The server checks every physical line and ``$`` command chain before dispatch. Unquoted
``!`` comments end the physical line, including later dollar-separated text. Restricted
mode rejects a physical line if its executable text contains a quote and the line uses
a dollar or comment delimiter, even if the quotes match or enclose a command head.
Quotes inside an actual comment are ignored. Delimiter-free quoted arguments remain
allowed. Whole-head quote recognition does not grant argument quote or escape protection.
MAPDL quote and delimiter behavior varies by command and form; this filter can reject
benign delimiter-bearing text. It is not a complete solver parser.

Single commands include their effective header and comment. Batches check all normalized
entries and metadata before sending any header or allowed entry. Screenshot commands are
checked before view changes, temporary files, capture, or restoration. A denied request
does not change the solver through these tools.

With any family blocked, headers reject line breaks, ``$``, and unsafe controls.
Comments still support separate physical lines but reject ``$`` and unsafe controls.
The interpolated ``resume_model.file_name`` and ``open_results.file_name`` reject
command separators, comma fields, comment delimiters, line breaks, and unsafe controls
before RESUME, CDREAD, or POST1. Ordinary paths are not whitelisted or scanned.
These extra boundary checks do not apply when APDL is unrestricted.

Allowed batch execution still uses PyMAPDL's internal temporary input-file transport.
Binary databases and CDB restoration remain available. The server does not inspect
macro or CDB contents, follow nested input files, or interpret generated command names.
A submitted batch error reports attempts because some commands may not have executed.

.. warning::
   Arbitrary Python, including ``run_python_code`` and ``custom_plot``, can bypass this
   direct text filter. Use ``--disable-python`` when relying on APDL restrictions.
   Restrictions add no HTTP authentication, filesystem isolation, or solver sandbox.

Disabling arbitrary Python
~~~~~~~~~~~~~~~~~~~~~~~~~

Python is enabled by default. To disable both code execution and custom plotting, start
the server with ``--disable-python``:

.. code-block:: bash

   python -m ansys.mapdl.mcp --disable-python

The server does not construct or start a persistent Python subprocess. Both
``run_python_code`` and ``custom_plot`` are hidden and reject direct calls before
connection bootstrap or code execution. Connect, launch, disconnect, reconnect, and
startup connections preserve this policy. Native ``screenshot`` remains usable where
the deployment permits it. AALI retains its separate visualization restrictions.

This option is independent of ``--apdl-log-dir`` and ``--block-apdl-command``.
Operators can combine all three. Disabling Python does not block internal Python used
by the server, inspect nested APDL files, or create a solver or OS sandbox.


Native command logs
~~~~~~~~~~~~~~~~~~~

Logging is off by default. Start the server with an operator-owned directory to enable it:

.. code-block:: bash

   python -m ansys.mapdl.mcp --apdl-log-dir /private/mapdl-logs

Each server run has its own directory. Each managed main connection and persistent
Python connection writes a separate exclusively created native PyMAPDL log file.
Both ``run_python_code`` and ``custom_plot`` use the managed Python connection.
A requested logging attachment failure is an error, not a silent fallback to logging off.

``list_command_logs(offset=0, limit=50)`` returns a JSON object with ``success``,
``enabled``, ``logs``, and ``next_offset``. Each entry has an opaque ``log_id`` and
``source``, either ``main`` or ``python``. The offset is a nonnegative integer catalogue index.
The limit is an integer between 1 and 100. ``next_offset`` is null at the end of the catalogue.
An offset equal to the catalogue size returns an empty final page. A larger offset returns
``success=false`` with an ``error`` string. When logging is off, ``enabled`` is false and
``logs`` is empty.

``read_command_log(log_id, offset=0, max_bytes=65536)`` accepts only a returned ID,
not a filesystem path. Its JSON result has ``success``, ``log_id``, ``source``,
``data_base64``, ``size_bytes``, and ``next_offset``. Decode ``data_base64`` to obtain
the exact bytes. The offset is a nonnegative integer byte position and ``max_bytes`` is an
integer between 1 and 65536. The next offset follows the returned bytes, including at the current end.
Read again at that offset to see later growth. A byte page can split an encoded character.
Unknown IDs, missing files, read failures, and invalid ranges return ``success=false``
with an ``error`` string.
For both tools, booleans, numeric strings, and floating-point values fail MCP argument
validation before retrieval. Only the retrieval arguments use this strict integer rule.

Both tools remain available after disconnect. They read a bounded on-disk prefix without
flushing or executing work in Python. Logs record partial, mutable command attempts,
not execution receipts or every solver-executed command. Native logging can be suppressed
by arbitrary Python. Referenced input files, macros, and independently created clients
are not an exhaustive command history. No order across the main and Python streams is claimed.

Files stay on the MCP host after disconnect and shutdown. ``download_file`` accesses
MAPDL-host files, not these client-local logs. The operator manages retention and disk
quota. Files and catalogue metadata grow until operator cleanup. The server does not
delete or rotate evidence. Process termination can leave an unflushed suffix.

.. warning::
   Logs can contain sensitive model data and paths. HTTP clients share this application's
   catalogue. Logging adds no authentication, per-user privacy, or solver sandbox.

Custom Python code execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``run_python_code`` to execute arbitrary Python and PyMAPDL code in a persistent session:

*"Execute this Python code: displacements = mapdl.get_array('NODE', item1='U', it1num='Y'); print(f'Max displacement: {displacements.max()}')."*

This is useful for:

- Custom data processing and analysis
- Advanced PyVista visualizations
- NumPy/Pandas data manipulation
- Complex computations not available through direct MAPDL commands

Creating custom plots
~~~~~~~~~~~~~~~~~~~~~

Use ``custom_plot`` to create Matplotlib or PyVista plots that are not available in MAPDL's
native plotting:

*"Create a Matplotlib plot showing nodal displacements versus node number."*

.. important::
   ``custom_plot`` is for plots that MAPDL cannot produce natively. For standard MAPDL plots
   (``APLOT``, ``LPLOT``, ``KPLOT``, ``PLNSOL``, etc.), use the MAPDL commands together with
   the ``screenshot`` tool.

Capturing plots
~~~~~~~~~~~~~~~

Use the ``screenshot`` tool to run a MAPDL plot command and capture the result as an image:

*"Show a plot of the mesh."*

*"Capture the average stress distribution."*

The tool returns the image directly so the AI assistant can display it inline. It supports all
MAPDL native plot commands:

- Geometry: ``APLOT``, ``LPLOT``, ``KPLOT``, ``VPLOT``
- Mesh: ``EPLOT``, ``NPLOT``
- Post-processing: ``PLNSOL``, ``PLESOL``, ``PLDISP``

**Parameters**

``commands``
    Optional APDL commands to run before capturing the screenshot
    (for example ``EPLOT`` or ``SET,LAST``).

``show_plot_on_popup``
    When ``True``, the captured image is also opened in the system's default image
    viewer so the user can inspect it at full resolution. Default is ``False``.

Python code execution
~~~~~~~~~~~~~~~~~~~~~

- Run Python code: Execute arbitrary Python code in the persistent session *(requires MAPDL connection)*.
- Integrate with data analysis: Use NumPy, Pandas, and other Python libraries.

File management
~~~~~~~~~~~~~~~

Use the file-management tools to transfer files between the local filesystem and the MAPDL
working directory, and to restore saved models or open result files for post-processing.

**Uploading files to MAPDL**

Use ``upload_file`` to transfer a local file (database, archive, or input file) to the MAPDL
working directory before referencing it with MAPDL commands:

*"Upload /home/user/project/beam.db to MAPDL."*

**Downloading files from MAPDL**

Use ``download_file`` to retrieve output files (result files, logs, databases) to the local
filesystem. Glob patterns such as ``"file*"`` are supported:

*"Download file.rst to /home/user/results."*

*"Download all files matching file* from MAPDL."*

**Resuming a saved model**

Use ``resume_model`` to restore a previously saved MAPDL model from a ``.db`` binary database
file or a ``.cdb`` coded ASCII archive file. If the file is not yet in the MAPDL working
directory, upload it first with ``upload_file``:

*"Resume the model from beam.db."*

*"Load the archived model from model.cdb."*

**Opening result files for post-processing**

Use ``open_results`` to switch MAPDL into the POST1 post-processor and optionally point it at
a specific RST result file. After calling this tool, you can query displacements, stresses, and
other result quantities:

*"Open the result file for post-processing."*

*"Enter POST1 and load beam.rst."*

**File-path resources**

Three MCP resources expose the paths to key MAPDL output files so the AI assistant can share
them with other tools or applications:

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Resource URI
     - Returns
   * - ``files://mapdl/working_directory``
     - Absolute path to the MAPDL working directory
   * - ``files://mapdl/rst_path``
     - Expected path to ``<jobname>.rst``
   * - ``files://mapdl/db_path``
     - Expected path to ``<jobname>.db``


Workflow examples
-----------------

Linear static analysis
~~~~~~~~~~~~~~~~~~~~~~

#. Launch MAPDL instance.
#. Define geometry (blocks, cylinders, and so on).
#. Define materials and element types.
#. Mesh the geometry.
#. Apply boundary conditions and loads.
#. Run solution.
#. Extract and visualize results.

Parametric study
~~~~~~~~~~~~~~~~

#. Set up the base MAPDL model.
#. Define parameter ranges.
#. Update parameters, run analysis, and extract results for each parameter combination.
#. Analyze and plot parameter sensitivity.

Result postprocessing
~~~~~~~~~~~~~~~~~~~~~

#. Run or load MAPDL analysis.
#. Extract result data.
#. Create custom visualizations.
#. Generate analysis reports.

Loading and post-processing an external result file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Upload the RST file: ``upload_file("/local/path/beam.rst")``.
#. Open the result file: ``open_results("beam")``.
#. Query result quantities (displacements, stresses, etc.) with MAPDL commands.
#. Download the results if needed: ``download_file("beam.rst", "/local/results/")``.

Restoring a saved model
~~~~~~~~~~~~~~~~~~~~~~~

#. Upload the database file: ``upload_file("/local/path/model.db")``.
#. Restore the model: ``resume_model("model", "db")``.
#. Inspect geometry, mesh, and boundary conditions.
#. Continue with further pre-processing, solution, or post-processing steps.

Interpreting tool results
-------------------------

Most tools return structured results with one of these outcomes:

- Success: A status or result message.
- Error: A detailed message describing what failed and how to correct it.

Additionally, some tools might return data as structured payloads (for example, JSON text or image content).

When building workflows, always validate results before continuing to the next step.
If a tool returns an error message, adjust the request and retry instead of assuming
that downstream steps are still valid.

Feature reference
-----------------

For the documentation of all available tools, including parameters and return values, see
:doc:`../api/ansys/mapdl/mcp/tools/index`.

Best practices
--------------

For recommendations on using PyMAPDL-MCP effectively, see :doc:`best_practices`.
