"""Main editor screen — code editor with output tabs.

Resizable horizontal split (editor | output) and vertical split (tabs | errors).
Keyboard: Ctrl+←/→ to adjust horizontal split, Ctrl+↑/↓ for vertical split.
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, TextArea, TabbedContent, TabPane, Static
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from pyc64_ui.widgets.hex_viewer import HexViewer
from pyc64_ui.widgets.listing_view import ListingView
from pyc64_ui.widgets.error_panel import ErrorPanel
from pyc64_ui.widgets.status_bar import EditorStatusBar
from pyc64_ui.controller import compile_source_text

ROOT = Path('/app/source') if Path('/app/source').exists() else Path.cwd()


class EditorScreen(Screen):
    """Main editor screen with resizable splits."""

    BINDINGS = [
        Binding('ctrl+s', 'save_compile', 'Save+Compile'),
        Binding('ctrl+o', 'browse_files', 'Browse'),
        Binding('ctrl+t', 'show_tutorial', 'Tutorial'),
        Binding('ctrl+d', 'show_dashboard', 'Dashboard'),
        Binding('ctrl+q', 'quit', 'Quit'),

        Binding('ctrl+left', 'shrink_editor', '←'),
        Binding('ctrl+right', 'grow_editor', '→'),
        Binding('ctrl+up', 'grow_tabs', '↑'),
        Binding('ctrl+down', 'grow_errors', '↓'),
    ]

    CSS = """
    #main-split {
        height: 1fr;
    }
    #editor-panel, #output-panel {
        width: auto;
        height: 100%;
    }
    #editor {
        height: 1fr;
    }
    #tabs-errors-split {
        height: 100%;
    }
    #tabs {
        height: auto;
    }
    #errors {
        height: auto;
        border-top: solid $error;
        padding: 1;
    }
    #h-divider {
        width: 3;
        min-width: 3;
        height: 100%;
        background: $primary 15%;
        &:hover {
            background: $accent 50%;
        }
    }
    #v-divider {
        height: 3;
        min-height: 3;
        width: 100%;
        background: $primary 15%;
        &:hover {
            background: $accent 50%;
        }
    }
    #source-label {
        padding: 0 1;
        background: $primary-background;
        color: $primary;
        text-style: bold;
    }
    TabPane {
        padding: 1;
    }
    HexViewer, ListingView {
        min-height: 3;
    }
    """

    _hratio: float = 0.50   # editor fraction (0-1)
    _vratio: float = 0.70   # tabs fraction (0-1)
    _dragging: str | None = None

    def __init__(self, filepath=None):
        super().__init__()
        self.current_path = Path(filepath) if filepath else None
        self._saved_text = ''
        self._last_compile_result = None

    # ── Compose ─────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id='main-split'):
            with Vertical(id='editor-panel'):
                yield Static('[bold]Source (.c64)[/]', id='source-label')
                yield TextArea(
                    '', id='editor', language='python',
                    show_line_numbers=True, highlight_cursor_line=True,
                )
                yield EditorStatusBar(id='status-bar')
            yield Static(id='h-divider')
            with Vertical(id='output-panel'):
                with Vertical(id='tabs-errors-split'):
                    with TabbedContent(id='tabs'):
                        with TabPane('BASIC', id='basic'):
                            yield Static(
                                '(compile to see BASIC output)', id='basic-text'
                            )
                        with TabPane('Listing', id='listing'):
                            yield ListingView(id='listing-view')
                        with TabPane('Hex', id='hex'):
                            yield HexViewer(id='hex-view')
                    yield Static(id='v-divider')
                    yield ErrorPanel(id='errors')
        yield Footer()

    def on_mount(self) -> None:
        editor = self.query_one('#editor', TextArea)
        if self.current_path and self.current_path.exists():
            text = self.current_path.read_text()
            editor.text = text
            self._saved_text = text
            self._update_title()
            self.set_timer(0.05, self.action_compile)
        else:
            editor.text = (
                'score: byte = 0\n'
                '\n'
                'def main():\n'
                '    clear_screen()\n'
                '    while True:\n'
                '        print("SCORE: ")\n'
                '        print(score)\n'
                '        wait_frames(1)\n'
            )
        self.set_timer(0.1, self._apply_layout)
        self.set_timer(0.15, self._update_status_bar)

    # ── Resizable layout ────────────────────────────────────────────

    def _apply_layout(self) -> None:
        self._apply_hsplit()
        self._apply_vsplit()

    def _apply_hsplit(self) -> None:
        container = self.query_one('#main-split', Horizontal)
        total = container.region.width
        if total <= 0:
            return
        div_w = 3
        lw = max(total * 0.12, total * self._hratio - div_w / 2)
        rw = max(total * 0.12, total * (1 - self._hratio) - div_w / 2)
        s = lw + rw + div_w
        self.query_one('#editor-panel').styles.width = f'{lw / s * 100:.1f}%'
        self.query_one('#output-panel').styles.width = f'{rw / s * 100:.1f}%'

    def _apply_vsplit(self) -> None:
        container = self.query_one('#tabs-errors-split', Vertical)
        total = container.region.height
        if total <= 0:
            return
        div_h = 3
        th = max(total * 0.15, total * self._vratio - div_h / 2)
        eh = max(total * 0.10, total * (1 - self._vratio) - div_h / 2)
        s = th + eh + div_h
        self.query_one('#tabs').styles.height = f'{th / s * 100:.1f}%'
        self.query_one('#errors').styles.height = f'{eh / s * 100:.1f}%'

    def on_resize(self) -> None:
        self._apply_layout()

    # ── Mouse drag ──────────────────────────────────────────────────

    def on_mouse_down(self, event) -> None:
        wid = getattr(event.widget, 'id', None)
        if wid == 'h-divider':
            self._dragging = 'h'
            event.stop()
        elif wid == 'v-divider':
            self._dragging = 'v'
            event.stop()

    def on_mouse_move(self, event) -> None:
        if self._dragging == 'h':
            container = self.query_one('#main-split', Horizontal)
            total = container.region.width
            if total > 0:
                x = event.screen_x - container.region.x
                self._hratio = max(0.12, min(0.88, x / total))
                self._apply_hsplit()
        elif self._dragging == 'v':
            container = self.query_one('#tabs-errors-split', Vertical)
            total = container.region.height
            if total > 0:
                y = event.screen_y - container.region.y
                self._vratio = max(0.15, min(0.85, y / total))
                self._apply_vsplit()

    def on_mouse_up(self, event) -> None:
        if self._dragging:
            self._dragging = None
            event.stop()

    # ── Keyboard split adjustment ───────────────────────────────────

    def action_shrink_editor(self) -> None:
        self._hratio = max(0.12, self._hratio - 0.05)
        self._apply_hsplit()

    def action_grow_editor(self) -> None:
        self._hratio = min(0.88, self._hratio + 0.05)
        self._apply_hsplit()

    def action_grow_tabs(self) -> None:
        self._vratio = min(0.85, self._vratio + 0.05)
        self._apply_vsplit()

    def action_grow_errors(self) -> None:
        self._vratio = max(0.15, self._vratio - 0.05)
        self._apply_vsplit()

    # ── Status bar ──────────────────────────────────────────────────

    def _update_status_bar(self) -> None:
        ta = self.query_one('#editor', TextArea)
        sb = self.query_one('#status-bar', EditorStatusBar)
        try:
            pos = ta.selection.end
            sb.cursor_pos = (pos.row + 1, pos.column + 1)
        except Exception:
            sb.cursor_pos = (1, 1)
        fn = self.current_path.name if self.current_path else 'untitled.c64'
        sb.filename = fn
        sb.is_modified = (
            not self.current_path or ta.text != self._saved_text
        )

    def on_text_area_selection_changed(self, event) -> None:
        self._update_status_bar()

    def on_text_area_changed(self, event) -> None:
        self._update_status_bar()

    # ── Compile ─────────────────────────────────────────────────────

    def action_compile(self) -> None:
        self._compile_and_save_outputs()

    def _compile_and_save_outputs(self) -> None:
        source = self.query_one('#editor', TextArea).text
        result = compile_source_text(source)
        self._last_compile_result = result
        sb = self.query_one('#status-bar', EditorStatusBar)

        self.query_one('#errors', ErrorPanel).errors = result.errors

        if not result.ok:
            sb.compile_ok = False
            return

        sb.compile_ok = True

        self.query_one('#basic-text', Static).update(
            result.basic_code or '(no BASIC output)'
        )
        self.query_one('#listing-view', ListingView).entries = result.listing
        self.query_one('#hex-view', HexViewer).data = result.prg or b''

        base = self.current_path.stem if self.current_path else 'untitled'
        if result.basic_code:
            p = ROOT / f'output/basic/{base}.bas'
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(result.basic_code)
        if result.prg:
            p = ROOT / f'output/prg/{base}.prg'
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(result.prg)

    # ── File operations ─────────────────────────────────────────────

    def _update_title(self) -> None:
        name = self.current_path.name if self.current_path else 'untitled.c64'
        self.query_one('#source-label', Static).update(f'[bold]{name}[/]')

    def _save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = self.query_one('#editor', TextArea).text
        path.write_text(text)
        self.current_path = path
        self._saved_text = text
        self._update_title()
        self._update_status_bar()

    def action_browse_files(self) -> None:
        from pyc64_ui.screens.file_browser import FileBrowser

        def on_pick(result):
            if result is None:
                return
            action, path = result
            if action == 'open':
                if path.suffix == '.prg':
                    self.notify('PRG files are binaries — run in emulator')
                    return
                self.current_path = path
                text = path.read_text()
                self.query_one('#editor', TextArea).text = text
                self._saved_text = text
                self._update_title()
                self._update_status_bar()
                self.action_compile()

        self.app.push_screen(FileBrowser(current_mode='c64'), on_pick)

    def action_save_compile(self) -> None:
        if self.current_path:
            self._save(self.current_path)
        else:
            self._save_as()
            return
        self._compile_and_save_outputs()

    def _save_as(self) -> None:
        from textual.screen import ModalScreen
        from textual.widgets import Input, Label, Button
        from textual.containers import Vertical, Horizontal as H

        class SaveAsScreen(ModalScreen):
            DEFAULT_CSS = """
            SaveAsScreen { align: center middle; }
            #save-dialog { width: 50; height: 10; border: thick $primary; }
            Input { margin: 1 2; }
            Button { margin: 0 1; }
            """

            def compose(self):
                with Vertical(id='save-dialog'):
                    yield Label('[bold]Save as[/]')
                    yield Input(placeholder='filename.c64')
                    with H():
                        yield Button('Save', variant='primary', id='save-btn')
                        yield Button('Cancel', id='cancel-btn')

            def on_input_submitted(self, event):
                self._do_save(event.value.strip())

            def on_button_pressed(self, event):
                if event.button.id == 'save-btn':
                    inp = self.query_one(Input)
                    self._do_save(inp.value.strip())
                elif event.button.id == 'cancel-btn':
                    self.dismiss(None)

            def _do_save(self, name):
                if not name:
                    self.notify('Enter a filename', severity='error')
                    return
                if '.' not in name:
                    name += '.c64'
                self.dismiss(ROOT / name)

        def on_save(path):
            if path:
                self._save(path)
                self._compile_and_save_outputs()

        self.app.push_screen(SaveAsScreen(), on_save)

    def action_show_tutorial(self) -> None:
        from pyc64_ui.screens.tutorial import TutorialScreen

        def on_select(content):
            if content:
                self.query_one('#editor', TextArea).text = content
                self._saved_text = content
                self.action_compile()

        self.app.push_screen(TutorialScreen(), on_select)

    def action_show_dashboard(self) -> None:
        if self._last_compile_result:
            from pyc64_ui.screens.dashboard import DashboardScreen
            # Map result back to engine-like structure for dashboard if needed,
            # but we can also pass the result directly or enhance CompileResult.
            # For now, let's just use the metrics and errors from result.
            diag = []
            for e in self._last_compile_result.errors:
                diag.append({"severity": "error", "message": e})
            # Dashboard handles AI suggestions if we pass them.
            # compile_source_text currently only returns errors/warnings strings.
            # We might want to pass more structured data.

            # Actually, let's re-run engine to get full structured data for dashboard
            # to be truly decoupled and accurate.
            from pyc64c.engine import run_pipeline
            source = self.query_one('#editor', TextArea).text
            engine_res = run_pipeline(source)

            self.app.push_screen(DashboardScreen(
                metrics=engine_res.metrics,
                diagnostics=engine_res.diagnostics
            ))

    def action_quit(self) -> None:
        self.app.exit()
