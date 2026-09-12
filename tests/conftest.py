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

Careful with the escape hatch: `labscript_utils.excepthook` reads this as
`bool(os.environ.get(...))`, so *any* non-empty value suppresses the dialog --
`LABSCRIPT_NO_ERROR_DIALOG=0` suppresses it exactly as `=1` does. `setdefault`
will not overwrite an explicit setting, but the only settings that restore the
dialog are the empty string or unsetting the variable. Someone writing a test
of the dialog will reach for `=0`, get no dialog, and have no reason to suspect
the environment.
"""
import os

os.environ.setdefault('LABSCRIPT_NO_ERROR_DIALOG', '1')
