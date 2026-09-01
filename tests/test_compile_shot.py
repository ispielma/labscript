"""Compiling a shot all the way to a shot file.

Every table labscript writes on the way out is a chance to name a dtype numpy
no longer understands, and there is no earlier warning than the compile itself
failing: the shot file is left holding the groups written before the failure,
so it cannot even be compiled again. One shot that uses the features which
write those tables is enough to catch it.
"""
import os
import sys
import tempfile
import textwrap
import unittest
from types import ModuleType

import labscript_utils.h5_lock  # must precede h5py, as labscript itself does
import h5py

import labscript


SHOT = textwrap.dedent(
    '''
    from labscript import (
        start, stop, add_time_marker, wait, AnalogOut, DigitalOut, Shutter,
    )
    from labscript_devices.DummyPseudoclock.labscript_devices import (
        DummyPseudoclock,
    )
    from labscript_devices.DummyIntermediateDevice import (
        DummyIntermediateDevice,
    )

    DummyPseudoclock(name='pseudoclock')
    DummyIntermediateDevice(
        name='intermediate_device', parent_device=pseudoclock.clockline
    )
    AnalogOut(
        name='analog_out', parent_device=intermediate_device, connection='ao0'
    )
    DigitalOut(
        name='digital_out',
        parent_device=intermediate_device,
        connection='port0/line0',
    )
    Shutter(
        name='shutter',
        parent_device=intermediate_device,
        connection='port0/line1',
        delay=(0.0, 0.0),
    )

    t = 0
    add_time_marker(t, 'Start')
    start()
    t += 1
    digital_out.go_high(t)
    shutter.open(t)
    t += 1
    wait('a wait', t, timeout=5)
    t += 1
    add_time_marker(t, 'Stop')
    stop(t)
    '''
)


class CompileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.script = os.path.join(self.directory, 'a_shot.py')
        with open(self.script, 'w') as f:
            f.write(SHOT)
        self.run_file = os.path.join(self.directory, 'a_shot.h5')
        # A run file as runmanager makes one: globals and nothing else.
        with h5py.File(self.run_file, 'w') as f:
            f.create_group('globals')

        self.saved_main = sys.modules.get('__main__')
        self.saved_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.saved_cwd)
        if self.saved_main is not None:
            sys.modules['__main__'] = self.saved_main
        try:
            labscript.labscript_cleanup()
        except Exception:
            pass

    def compile_the_shot(self):
        """Compile it the way runmanager's batch compiler does."""
        module = ModuleType('__main__')
        module.__file__ = self.script
        sys.modules['__main__'] = module
        os.chdir(self.directory)
        try:
            labscript.labscript_init(self.run_file, labscript_file=self.script)
            with open(self.script) as f:
                code = compile(f.read(), self.script, 'exec', dont_inherit=True)
            exec(code, module.__dict__)
        finally:
            labscript.labscript_cleanup()

    def test_a_shot_using_markers_waits_and_a_shutter_compiles(self):
        self.compile_the_shot()

        with h5py.File(self.run_file, 'r') as f:
            for group in (
                'connection table',
                'devices',
                'script',
                'shot_properties',
                'time_markers',
                'waits',
            ):
                self.assertIn(group, f, '%s is written by a full compile' % group)
            # The tables whose dtypes are the risk, read back as strings:
            self.assertEqual(
                [row['label'].decode() for row in f['time_markers'][:]],
                ['Start', 'Stop'],
            )
            self.assertEqual(
                [row['label'].decode() for row in f['waits'][:]], ['a wait']
            )
            self.assertIn(
                b'pseudoclock', [row['name'] for row in f['connection table'][:]]
            )

    def test_the_shot_knows_how_long_it_runs(self):
        # BLACS asks the master pseudoclock's stop_time how long to wait, so a
        # shot that compiles without one runs in no time at all and looks like
        # a shot that never ran.
        import labscript_utils.properties as properties

        self.compile_the_shot()

        with h5py.File(self.run_file, 'r') as f:
            properties_ = properties.get(f, 'pseudoclock', 'device_properties')
        self.assertEqual(properties_['stop_time'], 3)


if __name__ == '__main__':
    unittest.main()
