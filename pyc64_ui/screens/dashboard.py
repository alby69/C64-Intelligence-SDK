"""Dashboard screen — Project metrics and AI assistant."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DataTable, Label
from textual.containers import Vertical, Horizontal, Grid
from textual.binding import Binding

class DashboardScreen(Screen):
    """Dashboard showing compilation metrics and suggestions."""

    BINDINGS = [
        Binding('escape', 'back', 'Back to Editor'),
    ]

    CSS = """
    DashboardScreen {
        background: $surface;
    }
    #dash-container {
        padding: 1 2;
    }
    .card {
        border: solid $primary;
        padding: 1;
        margin: 1;
        height: auto;
    }
    .card-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #metrics-grid {
        grid-size: 2;
        grid-gutter: 1;
        height: auto;
    }
    #suggestions-list {
        background: $boost;
        padding: 1;
        height: 1fr;
    }
    """

    def __init__(self, metrics=None, diagnostics=None):
        super().__init__()
        self.metrics = metrics or {}
        self.diagnostics = diagnostics or []

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id='dash-container'):
            yield Label('[bold size=200%]Project Dashboard[/]', id='dash-title')

            with Grid(id='metrics-grid'):
                with Vertical(classes='card'):
                    yield Label('📊 [bold]Compilation Metrics[/]', classes='card-title')
                    yield Static(self._format_metrics())

                with Vertical(classes='card'):
                    yield Label('🧠 [bold]AI Assistant Suggestions[/]', classes='card-title')
                    yield Static(self._format_suggestions(), id='suggestions-list')

            with Vertical(classes='card'):
                yield Label('📜 [bold]Diagnostics[/]', classes='card-title')
                yield DataTable(id='diag-table')

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one('#diag-table', DataTable)
        table.add_columns('Severity', 'Source', 'Message')
        for d in self.diagnostics:
            table.add_row(
                d.get('severity', 'info').upper(),
                d.get('source', 'engine').capitalize(),
                d.get('message', '')
            )

    def _format_metrics(self) -> str:
        m = self.metrics
        return (
            f"Binary Size: {m.get('binary_size_bytes', 0)} bytes\n"
            f"Compile Time: {m.get('compile_time_ms', 0)} ms\n"
            f"Global Vars: {m.get('globalVars', 0)}\n"
            f"Functions: {m.get('funcCount', 0)}\n"
            f"Max AST Depth: {m.get('maxDepth', 0)}\n"
            f"Uses Floats: {'Yes' if m.get('usesFloat') else 'No'}"
        )

    def _format_suggestions(self) -> str:
        suggs = [d['message'] for d in self.diagnostics if d.get('source') == 'ai-assistant']
        if not suggs:
            return "No suggestions at this time. Code looks good!"
        return "\n\n".join(f"• {s}" for s in suggs)

    def action_back(self) -> None:
        self.app.pop_screen()
