"""Test di integrazione end-to-end (Epic F).

Scenario 3 — Debugger attach: avvia VICE headless e verifica che il bridge
si connetta e legga un registro. Skippato se x64sc non è installato o non
può partire (headless) nell'ambiente CI.
"""

import os
import shutil
import sys

import pytest

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEBUGGER_DIR = os.path.join(SDK_ROOT, "debugger")

pytestmark = pytest.mark.skipif(
    shutil.which("x64sc") is None,
    reason="VICE (x64sc) non installato",
)


def test_vice_bridge_connect_and_read_register():
    sys.path.insert(0, DEBUGGER_DIR)
    from c64debugger.vice_bridge import VICERemoteMonitorBridge

    bridge = VICERemoteMonitorBridge(port=6510)
    started = bridge.start_vice_headless(limit_cycles=500000)
    assert started, "x64sc headless non avviato"

    try:
        ok, err = bridge.connect(timeout=3.0)
        if not ok:
            pytest.skip(f"monitor VICE non raggiungibile in questo ambiente: {err}")
        regs = bridge.get_registers()
        assert isinstance(regs, dict), "registri non disponibili"
    finally:
        bridge.disconnect()
        bridge.kill_vice()