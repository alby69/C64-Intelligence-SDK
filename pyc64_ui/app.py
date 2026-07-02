#!/usr/bin/env python3
"""PYC64 TUI — Textual-based editor for Python-to-C64 compilation.

Usage:
    python3 -m pyc64_ui.app              # empty editor
    python3 -m pyc64_ui.app file.c64     # open file
"""

import sys
from pathlib import Path

from textual.app import App
from textual.binding import Binding

from pyc64_ui.screens.editor import EditorScreen
from pyc64_ui.screens.about import AboutScreen
from pyc64_ui.screens.dashboard import DashboardScreen
from pyc64_ui.screens.tutorial import TutorialScreen
from pyc64_ui.screens.simulator import SimulatorScreen


class PYC64App(App):
    """PYC64 Textual application."""

    TITLE = 'PYC64 — C64 Cross Compiler'
    SUB_TITLE = 'Python → 6502 · PRG · BASIC'

    SCREENS = {
        'editor': EditorScreen,
        'about': AboutScreen,
        'dashboard': DashboardScreen,
        'tutorial': TutorialScreen,
        'simulator': SimulatorScreen,
    }

    BINDINGS = [
        Binding('f1', 'show_about', 'Help'),
        Binding('ctrl+q', 'quit', 'Quit'),
    ]

    CSS = """
    Screen {
        background: $surface;
    }
    #about-content {
        padding: 2 4;
    }
    """

    def on_ready(self) -> None:
        filepath = sys.argv[1] if len(sys.argv) > 1 else None
        self.push_screen(EditorScreen(filepath=filepath))

    def action_show_about(self) -> None:
        self.push_screen('about')


def main():
    app = PYC64App()
    app.run()


if __name__ == '__main__':
    main()
