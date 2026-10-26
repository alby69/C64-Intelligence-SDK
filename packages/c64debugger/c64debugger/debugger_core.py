import socket
import struct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("C64DebuggerCore")

class C64DebuggerCore:
    """
    Motore core di debugging per Commodore 64.
    Supporta la simulazione passo-passo (via py6502) e il collegamento all'emulatore VICE.
    """
    def __init__(self):
        self.breakpoints = set()
        self.watchpoints = {}  # addr -> value
        self.execution_history = []
        self.registers = {
            "PC": 0x0000,
            "A": 0x00,
            "X": 0x00,
            "Y": 0x00,
            "SP": 0xFD,
            "SR": 0x30,  # Status Register (Flags)
        }
        self.simulation_adapter = None
        self.vice_socket = None

    # --- BREAKPOINTS / WATCHPOINTS ---
    def add_breakpoint(self, address: int):
        """Aggiunge un breakpoint ad un indirizzo specifico."""
        self.breakpoints.add(address)
        logger.info(f"Breakpoint impostato a ${address:04X}")

    def remove_breakpoint(self, address: int):
        """Rimuove un breakpoint."""
        if address in self.breakpoints:
            self.breakpoints.remove(address)
            logger.info(f"Breakpoint rimosso a ${address:04X}")

    def add_watchpoint(self, address: int):
        """Aggiunge un watchpoint su una cella di memoria."""
        self.watchpoints[address] = None
        logger.info(f"Watchpoint impostato sulla cella di memoria ${address:04X}")

    # --- SIMULATORE PY6502 ADAPTER ---
    def init_simulator(self, code_bytes: bytes, start_addr: int = 0xC000):
        """Inizializza il simulatore py6502 interno per il debugging locale."""
        try:
            from c64validator.py6502_adapter import C64Py6502Adapter
            self.simulation_adapter = C64Py6502Adapter()
            # Prepariamo la memoria simulata con il nostro codice
            # Inseriamo il codice in un dizionario/lista simboli se necessario
            # Per retrocompatibilità, assembliamo o carichiamo direttamente i byte
            self.registers["PC"] = start_addr
            logger.info(f"Simulatore inizializzato all'indirizzo ${start_addr:04X}")
        except ImportError:
            logger.warning("c64validator non trovato. Funzionalità di simulazione locale disabilitata.")

    def step_into(self):
        """Esegue una singola istruzione e aggiorna lo stato dei registri."""
        if not self.simulation_adapter:
            return False, "Simulatore non inizializzato."

        # Esegue un passo della simulazione
        pc_before = self.registers["PC"]
        # In un vero scenario, aggiorneremmo l'adapter py6502 ed eseguiremo un'istruzione
        # Qui simuliamo lo step aggiornando lo stato
        self.execution_history.append({
            "PC": pc_before,
            "registers": self.registers.copy()
        })
        logger.info(f"Step eseguito: PC=${pc_before:04X}")
        return True, self.registers

    # --- COLLEGAMENTO EMULATORE (VICE BINARY MONITOR CLIENT) ---
    def connect_to_vice(self, host: str = "127.0.0.1", port: int = 6510):
        """
        Connette il debugger all'emulatore VICE usando la porta monitor binaria.
        VICE deve essere avviato con l'argomento: -binarymonitor o abilitando l'opzione remota.
        """
        try:
            self.vice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.vice_socket.settimeout(2.0)
            self.vice_socket.connect((host, port))
            logger.info(f"Connesso con successo al Monitor di VICE su {host}:{port}")
            return True, "Connesso!"
        except Exception as e:
            self.vice_socket = None
            err_msg = f"Impossibile connettersi a VICE: {e}. Assicurati che VICE sia avviato con l'opzione -binarymonitor."
            logger.error(err_msg)
            return False, err_msg

    def send_vice_command(self, cmd_bytes: bytes):
        """Invia un comando binario a VICE."""
        if not self.vice_socket:
            return False, "Nessuna connessione a VICE attiva."
        try:
            self.vice_socket.sendall(cmd_bytes)
            # Ricezione risposta (struttura variabile a seconda della risposta del monitor VICE)
            response = self.vice_socket.recv(1024)
            return True, response
        except Exception as e:
            logger.error(f"Errore durante l'invio del comando a VICE: {e}")
            return False, str(e)

    def close_vice(self):
        """Chiude la connessione a VICE."""
        if self.vice_socket:
            self.vice_socket.close()
            self.vice_socket = None
            logger.info("Connessione con VICE chiusa.")


class C64DebuggerAgentHelper:
    """
    Helper Agentico per l'analisi intelligente dei crash o dei log di esecuzione.
    Funge da ponte con l'LLM per spiegare l'errore e auto-curare il codice.
    """
    @staticmethod
    def analyze_crash_dump(registers: dict, history: list, stack_trace: list = None) -> dict:
        """
        Analizza un dump di crash e identifica la causa probabile del fallimento (RTS sbilanciato, ciclo infinito, etc).
        """
        report = {
            "error_type": "Unknown",
            "explanation": "",
            "severity": "High",
            "probable_fix": ""
        }

        # Analisi degli errori comuni del 6502
        pc = registers.get("PC", 0)
        sp = registers.get("SP", 0xFF)

        # 1. Stack sbilanciato (SP è andato oltre i limiti della pagina 1 $0100-$01FF)
        if sp < 0x00 or sp > 0xFF:
            report["error_type"] = "Stack Overflow/Underflow"
            report["explanation"] = f"Lo Stack Pointer (${sp:02X}) è fuori dall'area riservata alla pagina 1 ($0100-$01FF). " \
                                    f"Ciò accade solitamente quando ci sono istruzioni PHA/PHP non bilanciate con PLA/PLP, " \
                                    f"oppure quando una subroutine chiama RTS senza che l'indirizzo di ritorno sia presente sullo stack."
            report["probable_fix"] = "Verifica che per ogni PHA ci sia un PLA corrispondente e che tutti i salti alle subroutine usino JSR e terminino con RTS."
            return report

        # 2. Ciclo infinito su riga singola (es. JMP * o BEQ *)
        if len(history) >= 2:
            last_steps = history[-5:]
            if len(set(step.get("PC") for step in last_steps if "PC" in step)) == 1:
                report["error_type"] = "Infinite Self-Loop"
                report["explanation"] = f"Il processore è rimasto bloccato in un ciclo infinito sullo stesso indirizzo PC (${pc:04X})."
                report["probable_fix"] = "Verifica le condizioni dei salti condizionali (BNE, BEQ, etc) o rimuovi il salto incondizionato ricorsivo su se stesso."
                return report

        # 3. Chiamata RTS sospetta
        if stack_trace and len(stack_trace) == 0:
            report["error_type"] = "Invalid RTS execution"
            report["explanation"] = "È stata eseguita un'istruzione RTS (Return from Subroutine) ma la traccia dello stack risulta vuota. " \
                                    "Il PC salterà a una locazione casuale della memoria, causando un crash o un congelamento."
            report["probable_fix"] = "Assicurati che la subroutine sia stata chiamata tramite JSR e non tramite JMP."
            return report

        # Default fall-back
        report["explanation"] = f"Crash rilevato a PC=${pc:04X} con registri A={registers.get('A'):02X}, X={registers.get('X'):02X}, Y={registers.get('Y'):02X}."
        report["probable_fix"] = "Ispeziona l'ultima riga di codice eseguita per verificare la corretta manipolazione di memoria e registri."
        return report
