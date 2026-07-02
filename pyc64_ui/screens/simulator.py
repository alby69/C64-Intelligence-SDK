from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DataTable, Button, Log
from textual.containers import Horizontal, Vertical, Container
from textual.binding import Binding
from pyc64c.simulation_engine import C64Simulator

class SimulatorScreen(Screen):
    """Simulator screen for running and debugging 6502 code."""

    BINDINGS = [
        Binding('escape', 'app.pop_screen', 'Back'),
        Binding('f5', 'run', 'Run'),
        Binding('f6', 'step', 'Step'),
        Binding('f7', 'reset', 'Reset'),
    ]

    CSS = """
    #sim-main {
        layout: horizontal;
        height: 1fr;
    }
    #sim-left {
        width: 40%;
        height: 100%;
        border-right: solid $primary;
    }
    #sim-right {
        width: 60%;
        height: 100%;
    }
    #sim-registers {
        height: 8;
        border-bottom: solid $primary;
        padding: 1;
    }
    #sim-history {
        height: 1fr;
    }
    #sim-output {
        height: 1fr;
        border-bottom: solid $primary;
        padding: 1;
    }
    #sim-controls {
        height: 3;
        layout: horizontal;
        align: center middle;
        background: $surface;
    }
    .reg-label { color: $accent; text-style: bold; }
    .reg-value { color: $text; }
    """

    def __init__(self, prg: bytes, labels=None):
        super().__init__()
        self.prg = prg
        self.labels = labels
        self.simulator = C64Simulator(prg, symbols=labels)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id='sim-main'):
            with Vertical(id='sim-left'):
                yield Static("REGISTERS", id='sim-registers-title')
                yield Static(id='sim-registers')
                yield Static("HISTORY", id='sim-history-title')
                yield Log(id='sim-history')
            with Vertical(id='sim-right'):
                yield Static("OUTPUT", id='sim-output-title')
                yield Log(id='sim-output')
                with Horizontal(id='sim-controls'):
                    yield Button("Run (F5)", id='run-btn', variant='success')
                    yield Button("Step (F6)", id='step-btn', variant='primary')
                    yield Button("Reset (F7)", id='reset-btn', variant='error')
        yield Footer()

    def on_mount(self) -> None:
        self.update_ui()

    def update_ui(self) -> None:
        # Update Registers
        regs = self.simulator.sim
        reg_text = (
            f"PC: [bold #ffaa00]${regs.pc:04X}[/]    "
            f"SP: [bold #ffaa00]${regs.sp:02X}[/]\n\n"
            f"A: [bold #ffaa00]${regs.a:02X}[/]  "
            f"X: [bold #ffaa00]${regs.x:02X}[/]  "
            f"Y: [bold #ffaa00]${regs.y:02X}[/]\n\n"
            f"Flags: [bold #ffaa00]{regs.cc:08b}[/]"
        )
        self.query_one('#sim-registers', Static).update(reg_text)

        # Update History Log
        history_log = self.query_one('#sim-history', Log)
        history_log.clear()
        for entry in self.simulator.history:
            history_log.write_line(entry['line'])
        history_log.scroll_end()

        # Update Output Log
        output_log = self.query_one('#sim-output', Log)
        output_log.clear()
        output_log.write(self.simulator.output_buffer)
        output_log.scroll_end()

    def action_step(self) -> None:
        if self.simulator.step():
            self.update_ui()
        else:
            self.notify("Simulation stopped or error", severity="warning")

    def action_run(self) -> None:
        steps = self.simulator.run(max_steps=1000)
        self.update_ui()
        self.notify(f"Executed {steps} steps")

    def action_reset(self) -> None:
        self.simulator = C64Simulator(self.prg, symbols=self.labels)
        self.update_ui()
        self.notify("Simulator reset")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'run-btn':
            self.action_run()
        elif event.button.id == 'step-btn':
            self.action_step()
        elif event.button.id == 'reset-btn':
            self.action_reset()
