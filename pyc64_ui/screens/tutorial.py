"""Tutorial Screen — Load examples from C64GameTutorial."""

from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListItem, ListView, Label
from textual.containers import Vertical
from textual.binding import Binding
from pyc64c.integration import get_bridge

class TutorialScreen(Screen):
    """List of examples from the tutorial project."""

    BINDINGS = [
        Binding('escape', 'back', 'Back'),
    ]

    CSS = """
    TutorialScreen {
        background: $surface;
    }
    #tutorial-container {
        padding: 1 2;
    }
    ListView {
        border: solid $primary;
        margin-top: 1;
        height: 1fr;
    }
    ListItem {
        padding: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.bridge = get_bridge()
        self.examples = self.bridge.get_tutorial_examples()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id='tutorial-container'):
            yield Label('[bold size=200%]Tutorial Examples[/]')
            yield Label('Select an example from C64GameTutorial to load into the editor.')

            if not self.examples:
                yield Static('\n[yellow]No examples found in tutorial/C64GameTutorial directory.[/]\n'
                             'Ensure the SDK submodules are correctly checked out.')
            else:
                with ListView(id='example-list'):
                    for ex in self.examples:
                        yield ListItem(Static(f"📄 {ex['name']} - [dim]{ex['path']}[/]"), name=ex['path'])

        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_path = event.item.name
        # Find the content
        content = ""
        for ex in self.examples:
            if ex['path'] == selected_path:
                content = ex['content']
                break

        if content:
            self.dismiss(content)

    def action_back(self) -> None:
        self.dismiss(None)
