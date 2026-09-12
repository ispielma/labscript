"""Settings that have to be in place before the suite is imported.

Running the tests is not supposed to put anything on the screen of whoever runs
them. `labscript_utils.excepthook` replaces `sys.excepthook` at import time, and
every unhandled exception then spawns a separate tkinter subprocess window, up
to ten at once. A single bad run leaves a pile of them to close by hand.

Set here rather than expected on the command line: a test run should not depend
on remembering an environment variable. This affects test runs only — a real
labscript run does not import this file, so the dialog still appears where it is
meant to, which is the rule the workspace `AGENTS.md` guards.

`setdefault` will not overwrite an explicit setting. A test *of* the excepthook
itself should set `labscript_utils.excepthook.NO_ERROR_DIALOG` directly for its
own duration rather than relying on the environment.

This is a conftest rather than a fixture because the excepthook captures the
environment once, when it is imported: `NO_ERROR_DIALOG` is assigned at module
scope and the handler then reads that attribute. Setting the variable after the
import does nothing. pytest imports conftest before the test modules that pull
the suite in, which is what makes it early enough; a fixture would run too late.
A test of the dialog can still assign the attribute directly, which works at any
point.

`setdefault` leaves an explicit setting alone, and an explicit setting now means
what it looks like: `LABSCRIPT_NO_ERROR_DIALOG=0` keeps the dialog on, as do
`false`, `no`, `off` and the empty string. That was not true before `ae73495`
"Let LABSCRIPT_NO_ERROR_DIALOG=0 mean what it looks like" --
the variable was read for bare truthiness, so `=0` suppressed the dialog exactly
as `=1` did.
"""
import os

os.environ.setdefault('LABSCRIPT_NO_ERROR_DIALOG', '1')
