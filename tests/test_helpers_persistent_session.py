# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
from contextlib import redirect_stdout
import inspect
import io
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import pytest

from ansys.mapdl.mcp._security import _attach_main_log, _retire_native_log, _SecurityOptions
from ansys.mapdl.mcp.helpers import connect_to_mapdl_in_persistent_python
from ansys.mapdl.mcp.server import PyMAPDLAppContext, PyMAPDLMCP
from tests.test_command_logging import NativeLogClient


class LocalSession:
    def __init__(self):
        self.process = object()
        self.metadata = {}
        self.namespace = {}
        self.result_success = True
        self.discard_stdout = False

    def execute(self, code, timeout=30, no_output_timeout=1.2):
        output = io.StringIO()
        try:
            with (
                patch.dict(
                    sys.modules,
                    {
                        "ansys.mapdl.mcp.python_helper.startup_code": ModuleType(
                            "ansys.mapdl.mcp.python_helper.startup_code"
                        )
                    },
                ),
                redirect_stdout(output),
            ):
                exec(code, self.namespace)
            return {
                "success": self.result_success,
                "stdout": "" if self.discard_stdout else output.getvalue(),
            }
        except Exception as exc:
            return {"success": False, "stdout": output.getvalue(), "error": str(exc)}


@pytest.fixture
def child_context(mock_context, tmp_path):
    context = PyMAPDLAppContext(
        mapdl=NativeLogClient(ip="host'\\name"),
        python_session=LocalSession(),
        security_options=_SecurityOptions(tmp_path / "log'\\directory"),
    )
    mock_context.request_context.lifespan_context = context
    yield mock_context
    if "mapdl" in context.python_session.namespace:
        _retire_native_log(context.python_session.namespace["mapdl"])


@pytest.mark.unit
def test_child_reuses_only_confirmed_main_and_process(child_context):
    context = child_context.request_context.lifespan_context
    session = context.python_session
    with patch("ansys.mapdl.core.Mapdl", NativeLogClient):
        first = connect_to_mapdl_in_persistent_python(child_context)
        child = session.namespace["mapdl"]
        child._apdl_log.write("/COM,old-child\n")
        assert first is context.mapdl
        assert child.ip == "host'\\name"
        assert connect_to_mapdl_in_persistent_python(child_context) is first
        assert len(context.command_logs) == 1
        context.mapdl = NativeLogClient()
        assert connect_to_mapdl_in_persistent_python(child_context) is context.mapdl
        assert child._apdl_log is None
        replacement = session.namespace["mapdl"]
        session.process = object()
        assert connect_to_mapdl_in_persistent_python(child_context) is context.mapdl
        assert replacement._apdl_log is None
        assert len(context.command_logs) == 3
        assert session.metadata["mapdl_process"] is session.process
    assert all(ref.path.is_file() for ref in context.command_logs.values())
    assert all(ref.source == "python" for ref in context.command_logs.values())


@pytest.mark.unit
@pytest.mark.parametrize("success,discard_stdout", [(False, False), (True, True)])
def test_failed_or_unacknowledged_bootstrap_never_confirms_metadata(
    child_context, success, discard_stdout
):
    context = child_context.request_context.lifespan_context
    context.python_session.result_success = success
    context.python_session.discard_stdout = discard_stdout
    with patch("ansys.mapdl.core.Mapdl", NativeLogClient):
        result = connect_to_mapdl_in_persistent_python(child_context)
    assert result.startswith("Failed to connect to MAPDL in the persistent PyMAPDL session:")
    assert "mapdl" not in context.python_session.metadata
    assert "mapdl_process" not in context.python_session.metadata
    assert context.command_logs == {}


@pytest.mark.unit
def test_child_attachment_failure_is_reported_before_caller_work(child_context):
    context = child_context.request_context.lifespan_context
    with (
        patch("ansys.mapdl.core.Mapdl", NativeLogClient),
        patch.object(NativeLogClient, "open_apdl_log", side_effect=OSError("disk full")),
    ):
        result = connect_to_mapdl_in_persistent_python(child_context)
    assert result == "Failed to connect to MAPDL in the persistent PyMAPDL session: disk full"
    assert context.python_session.metadata == {}
    assert context.command_logs == {}


@pytest.mark.unit
def test_main_and_child_have_distinct_native_files(child_context):
    context = child_context.request_context.lifespan_context
    _attach_main_log(context, context.mapdl)
    with patch("ansys.mapdl.core.Mapdl", NativeLogClient):
        assert connect_to_mapdl_in_persistent_python(child_context) is context.mapdl
    _retire_native_log(context.mapdl)
    refs = list(context.command_logs.values())
    assert [ref.source for ref in refs] == ["main", "python"]
    assert refs[0].path != refs[1].path
    assert all(ref.path.is_file() for ref in refs)


@pytest.mark.unit
def test_missing_context_session_or_main_returns_explicit_error(mock_context):
    assert (
        connect_to_mapdl_in_persistent_python(SimpleNamespace(request_context=None))
        == "No request context available."
    )
    context = mock_context.request_context.lifespan_context
    context.python_session = None
    assert connect_to_mapdl_in_persistent_python(mock_context) == (
        "No Python session available. The persistent Python session was not initialized."
    )
    context.python_session = LocalSession()
    context.mapdl = None
    assert connect_to_mapdl_in_persistent_python(mock_context).startswith(
        "No MAPDL instance available in lifespan context."
    )


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("tool", ["code", "plot"])
async def test_callers_stop_on_bootstrap_failure_and_recover(child_context, tool):
    from ansys.mapdl.mcp.tools import custom_plot, run_python_code

    context = child_context.request_context.lifespan_context
    session = context.python_session
    session.discard_stdout = True
    with patch("ansys.mapdl.core.Mapdl", NativeLogClient):
        if tool == "code":
            failed = await run_python_code(child_context, "caller_ran = True; print('ok')")
            assert json.loads(failed.content[0].text)["success"] is False
        else:
            failed = custom_plot(
                child_context, "caller_ran = True; print('Plot saved to result.png')"
            )
            assert "Failed to connect" in failed.content[0].text
        assert "caller_ran" not in session.namespace
        session.discard_stdout = False
        if tool == "code":
            recovered = await run_python_code(child_context, "caller_ran = True; print('ok')")
            assert json.loads(recovered.content[0].text)["stdout"].strip() == "ok"
        else:
            recovered = custom_plot(
                child_context, "caller_ran = True; print('Plot saved to result.png')"
            )
            assert "Plot saved to result.png" in recovered.content[0].text
        assert session.namespace["caller_ran"] is True


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("tool", ["code", "plot"])
async def test_failed_replacement_preserves_good_child_and_never_runs_caller(child_context, tool):
    from ansys.mapdl.mcp.tools import custom_plot, run_python_code

    context = child_context.request_context.lifespan_context
    session = context.python_session
    with patch("ansys.mapdl.core.Mapdl", NativeLogClient):
        assert connect_to_mapdl_in_persistent_python(child_context) is context.mapdl
        old_child = session.namespace["mapdl"]
        old_handle = old_child._apdl_log
        old_child._apdl_log.write("/COM,known-good\n")
        session.namespace["caller_ran"] = False
        context.mapdl = NativeLogClient()
        with patch.object(NativeLogClient, "open_apdl_log", side_effect=OSError("disk full")):
            if tool == "code":
                failed = await run_python_code(child_context, "caller_ran = True; print('ok')")
                assert json.loads(failed.content[0].text)["success"] is False
            else:
                failed = custom_plot(child_context, "caller_ran = True")
                assert "disk full" in failed.content[0].text
        assert session.namespace["mapdl"] is old_child
        assert old_child._apdl_log is old_handle and old_handle.closed is False
        assert session.namespace["caller_ran"] is False
        assert len(context.command_logs) == 1
        assert connect_to_mapdl_in_persistent_python(child_context) is context.mapdl
        assert old_handle.closed is True
        assert len(context.command_logs) == 2


@pytest.mark.unit
@pytest.mark.parametrize("changed_identity", ["main", "process"])
def test_identity_change_during_bootstrap_does_not_publish_connection(
    child_context, changed_identity
):
    context = child_context.request_context.lifespan_context
    session = context.python_session
    execute = session.execute

    def replace_during_bootstrap(code, **kwargs):
        result = execute(code, **kwargs)
        if changed_identity == "main":
            context.mapdl = NativeLogClient()
        else:
            session.process = object()
        return result

    with (
        patch("ansys.mapdl.core.Mapdl", NativeLogClient),
        patch.object(session, "execute", side_effect=replace_during_bootstrap),
    ):
        result = connect_to_mapdl_in_persistent_python(child_context)
    detail = (
        "Main MAPDL connection changed during bootstrap"
        if changed_identity == "main"
        else "Persistent Python process changed during bootstrap"
    )
    assert result.endswith(detail)
    assert session.metadata == {}
    assert context.command_logs == {}


@pytest.fixture
def repl_context(mock_context, tmp_path, monkeypatch):
    checkout = Path(__file__).resolve().parents[1]
    monkeypatch.setenv(
        "PYTHONPATH",
        os.pathsep.join([str(checkout / "src"), os.environ.get("PYTHONPATH", "")]),
    )
    server = PyMAPDLMCP()
    server.python_executable = sys.executable
    server.working_directory = str(checkout)
    server._cli_config = {"apdl_log_dir": tmp_path / "logs"}
    context = server.create_context()
    context.mapdl = NativeLogClient()
    mock_context.request_context.lifespan_context = context
    session = context.python_session
    assert session.startup_code is None
    try:
        assert session.start()["success"] is True
        before = session.execute(
            "print('plt' in globals(), 'save_plot' in globals())", no_output_timeout=None
        )
        assert before["success"] is True
        assert before["stdout"].strip() == "False False"
        source = (
            "import logging\n"
            "from ansys.mapdl.core.mapdl_core import _MapdlCore\n"
            + inspect.getsource(NativeLogClient)
            + "\nimport ansys.mapdl.core as _test_core\n"
            "_test_core.Mapdl = NativeLogClient\n"
        )
        seeded = session.execute(f"exec({source!r})", no_output_timeout=None)
        assert seeded["success"] is True, seeded
        yield mock_context
    finally:
        session.stop()


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("tool", ["code", "plot"])
async def test_real_repl_attachment_failure_preserves_global_and_stops_callers(repl_context, tool):
    from ansys.mapdl.mcp._security import _allocate_log
    from ansys.mapdl.mcp.tools import custom_plot, run_python_code

    context = repl_context.request_context.lifespan_context
    session = context.python_session
    assert connect_to_mapdl_in_persistent_python(repl_context) is context.mapdl
    saved = session.execute(
        "prior_mapdl = mapdl; prior_handle = mapdl._apdl_log; caller_ran = False; "
        "mapdl._apdl_log.write('/COM,known-good\\n'); print('saved')",
        no_output_timeout=None,
    )
    assert saved["success"] is True
    assert "saved" in saved["stdout"].splitlines()
    prior_ref = next(iter(context.command_logs.values()))
    context.mapdl = NativeLogClient()

    def allocate_directory(app_context, source):
        allocation = _allocate_log(app_context, source)
        allocation[1].path.mkdir()
        return allocation

    results = []
    execute = session.execute

    def capture_execute(code, **kwargs):
        result = execute(code, **kwargs)
        results.append(result)
        return result

    with (
        patch("ansys.mapdl.mcp.helpers._allocate_log", side_effect=allocate_directory),
        patch.object(session, "execute", side_effect=capture_execute),
    ):
        if tool == "code":
            failed = await run_python_code(repl_context, "caller_ran = True; print('ran')")
            failure = json.loads(failed.content[0].text)
            assert failure["success"] is False
            error = failure["error"]
        else:
            failed = custom_plot(repl_context, "caller_ran = True; print('ran')")
            error = failed.content[0].text
        assert "Error" in error
        assert "Failed to connect" in error
        assert len(results) == 1
        assert results[0]["success"] is False
        assert "Error" in results[0]["stderr"]
        assert "__MAPDL_CONNECTED_" not in results[0]["stdout"]
    observed = session.execute(
        "print(mapdl is prior_mapdl, prior_handle.closed, "
        "prior_mapdl._apdl_log is prior_handle, caller_ran)",
        no_output_timeout=None,
    )
    assert observed["success"] is True
    assert observed["stdout"].strip() == "True False True False"
    assert session.metadata == {}
    assert len(context.command_logs) == 1
    assert b"/COM,known-good" in prior_ref.path.read_bytes()
    if tool == "code":
        recovered = await run_python_code(repl_context, "caller_ran = True; print('ran')")
        assert json.loads(recovered.content[0].text)["stdout"].strip() == "ran"
    else:
        recovered = custom_plot(
            repl_context, "caller_ran = True; print('Plot saved to result.png')"
        )
        assert "Plot saved to result.png" in recovered.content[0].text
    observed = session.execute("print(prior_handle.closed, caller_ran)", no_output_timeout=None)
    assert observed["success"] is True
    assert observed["stdout"].strip() == "True True"
    assert len(context.command_logs) == 2


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("tool", ["code", "plot"])
async def test_real_repl_initializes_plotting_once_and_again_after_restart(repl_context, tool):
    from ansys.mapdl.mcp.tools import custom_plot, run_python_code

    context = repl_context.request_context.lifespan_context
    session = context.python_session
    ready = (
        "print(matplotlib.get_backend().lower(), pv.OFF_SCREEN, "
        "callable(save_plot), callable(save_matplotlib_plot), hasattr(plt, 'figure'))"
    )
    plot = "plt.figure(); plt.plot([0, 1], [0, 1]); print(save_matplotlib_plot())"
    if tool == "code":
        result = await run_python_code(repl_context, ready)
        result = json.loads(result.content[0].text)
        assert result["success"] is True
        assert result["stdout"].strip() == "agg True True True True"
    else:
        result = custom_plot(repl_context, plot)
        image = next(content for content in result.content if content.type == "image")
        assert base64.b64decode(image.data).startswith(b"\x89PNG\r\n\x1a\n")
        observed = session.execute(ready, no_output_timeout=None)
        assert observed["success"] is True
        assert observed["stdout"].strip() == "agg True True True True"
    mutated = session.execute(
        "plt = 'kept'; save_plot = 'kept-helper'; Mapdl = 'kept-user'; print('mutated')",
        no_output_timeout=None,
    )
    assert mutated["success"] is True
    context.mapdl = NativeLogClient()
    assert connect_to_mapdl_in_persistent_python(repl_context) is context.mapdl
    preserved = session.execute("print(plt, save_plot, Mapdl)", no_output_timeout=None)
    assert preserved["success"] is True
    assert preserved["stdout"].strip() == "kept kept-helper kept-user"
    old_process = session.process
    assert session.restart()["success"] is True
    assert session.process is not old_process
    seed = "import ansys.mapdl.core as _test_core; _test_core.Mapdl = NativeLogClient"
    source = (
        "import logging\n"
        "from ansys.mapdl.core.mapdl_core import _MapdlCore\n"
        + inspect.getsource(NativeLogClient)
        + "\n"
        + seed
    )
    seeded = session.execute(f"exec({source!r})", no_output_timeout=None)
    assert seeded["success"] is True, seeded
    if tool == "code":
        result = json.loads((await run_python_code(repl_context, ready)).content[0].text)
        assert result["success"] is True
        assert result["stdout"].strip() == "agg True True True True"
    else:
        result = custom_plot(repl_context, plot)
        image = next(content for content in result.content if content.type == "image")
        assert base64.b64decode(image.data).startswith(b"\x89PNG\r\n\x1a\n")
    assert len(context.command_logs) == 3
    assert session.metadata["mapdl_process"] is session.process


@pytest.mark.unit
@pytest.mark.parametrize(
    "result,detail",
    [
        (None, "Invalid bootstrap result"),
        ({"success": False, "error": "", "stderr": ""}, "Bootstrap execution failed"),
        ({"success": True, "stdout": "", "error": ""}, "Bootstrap acknowledgement missing"),
        ({"success": True, "stdout": None, "error": ""}, "Bootstrap acknowledgement missing"),
        ({"success": False, "error": " \n", "stderr": " "}, "Bootstrap execution failed"),
        ({"success": False, "error": "", "stderr": "actual stderr"}, "actual stderr"),
        (
            {"success": False, "error": "actual error", "stderr": "actual stderr"},
            "actual error\nactual stderr",
        ),
    ],
)
def test_bootstrap_errors_are_specific_and_keep_stderr(child_context, result, detail):
    with patch.object(
        child_context.request_context.lifespan_context.python_session,
        "execute",
        return_value=result,
    ):
        error = connect_to_mapdl_in_persistent_python(child_context)
    assert error.endswith(detail)


@pytest.mark.unit
def test_unavailable_process_is_reported_before_bootstrap(child_context):
    child_context.request_context.lifespan_context.python_session.process = None
    assert connect_to_mapdl_in_persistent_python(child_context) == (
        "Failed to connect to MAPDL in the persistent PyMAPDL session: "
        "Persistent Python process is unavailable"
    )


@pytest.mark.unit
def test_empty_executor_exception_returns_specific_failure(child_context):
    with patch.object(
        child_context.request_context.lifespan_context.python_session,
        "execute",
        side_effect=RuntimeError(),
    ):
        assert connect_to_mapdl_in_persistent_python(child_context) == (
            "Failed to connect to MAPDL in the persistent PyMAPDL session: "
            "Bootstrap execution failed"
        )
