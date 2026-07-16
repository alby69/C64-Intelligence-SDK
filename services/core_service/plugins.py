from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List, Optional

class BuildResult:
    def __init__(self, success: bool, prg_bytes: bytes, errors: List[Any]):
        self.success = success
        self.prg_bytes = prg_bytes
        self.errors = errors

class IBuildTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def compile(self, source: str, options: Dict[str, Any]) -> BuildResult:
        """Compila il codice sorgente in formato binario PRG."""
        pass

class IDebugger(ABC):
    @abstractmethod
    def connect(self, host: str, port: int) -> bool:
        """Connette il debugger all'emulatore."""
        pass

    @abstractmethod
    def set_breakpoint(self, address: int) -> bool:
        """Imposta un breakpoint."""
        pass

    @abstractmethod
    def step(self) -> Dict[str, Any]:
        """Esegue una singola istruzione."""
        pass

    @abstractmethod
    def register_on_break_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Registra una callback richiamata quando l'esecuzione si interrompe."""
        pass


# A simple Mock Compiler and Debugger to demonstrate implementations
class MockBuildTool(IBuildTool):
    @property
    def name(self) -> str:
        return "mock-compiler"

    def compile(self, source: str, options: Dict[str, Any]) -> BuildResult:
        # Generate basic fake PRG header $0801 + some mock instructions or detokenized pattern
        fake_bytes = b"\x01\x08" + source.encode("utf-8")[:10]
        return BuildResult(success=True, prg_bytes=fake_bytes, errors=[])

class MockDebugger(IDebugger):
    def __init__(self):
        self.connected = False
        self.breakpoints = set()
        self.callback = None

    def connect(self, host: str, port: int) -> bool:
        self.connected = True
        return True

    def set_breakpoint(self, address: int) -> bool:
        self.breakpoints.add(address)
        return True

    def step(self) -> Dict[str, Any]:
        return {"pc": 0x0810, "registers": {"a": 0, "x": 0, "y": 0, "sp": 0xff}}

    def register_on_break_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self.callback = callback
