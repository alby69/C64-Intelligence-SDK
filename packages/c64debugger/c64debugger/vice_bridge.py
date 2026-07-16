import socket
import struct
import subprocess
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VICERemoteMonitorBridge")

class VICERemoteMonitorBridge:
    """
    Bridge di connessione remota per il monitor dell'emulatore VICE (x64sc).
    Supporta sia l'interfaccia a riga di comando (CLI Monitor) sia la connessione
    via socket TCP al monitor (testuale o binario).
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 6510):
        self.host = host
        self.port = port
        self.socket = None
        self.vice_process = None

    def start_vice_headless(self, prg_path: str = None, limit_cycles: int = 10000000, extra_args: list = None) -> bool:
        """
        Avvia l'emulatore x64sc (VICE) in modalità headless (senza interfaccia grafica)
        abilitando il monitor remoto TCP sulla porta configurata.
        """
        args = [
            "x64sc",
            "-default",
            "-headless",           # Rende l'interfaccia invisibile (disponibile in VICE moderno)
            "-sound", "none",      # Disabilita il suono per risparmiare CPU
            "-monitorport", str(self.port)  # Abilita il monitor di testo sulla porta configurata
        ]

        if limit_cycles:
            args.extend(["-limitcycles", str(limit_cycles)])

        if prg_path:
            args.extend(["-autostartprgmode", "1", prg_path])

        if extra_args:
            args.extend(extra_args)

        try:
            logger.info(f"Avvio di VICE con comando: {' '.join(args)}")
            self.vice_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(1.5)
            return True
        except FileNotFoundError:
            logger.error("Emulatore 'x64sc' non trovato nel sistema. Assicurati che VICE sia installato e nel PATH.")
            return False
        except Exception as e:
            logger.error(f"Errore durante l'avvio di VICE: {e}")
            return False

    def connect(self, timeout: float = 2.0) -> tuple:
        """
        Connette il bridge alla porta monitor TCP di VICE.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.host, self.port))

            try:
                banner = self.socket.recv(1024).decode("utf-8", errors="ignore")
                logger.info(f"Ricevuto banner di benvenuto da VICE: {banner.strip()}")
            except socket.timeout:
                pass

            logger.info(f"Connesso con successo al Monitor di VICE su {self.host}:{self.port}")
            return True, "Connesso con successo!"
        except Exception as e:
            self.socket = None
            err_msg = f"Impossibile connettersi al monitor TCP di VICE: {e}."
            logger.error(err_msg)
            return False, err_msg

    def send_command(self, cmd: str) -> str:
        """
        Invia un comando testuale al monitor (es. 'r' per visualizzare i registri,
        'm 0400 0410' per visualizzare una porzione di memoria).
        """
        if not self.socket:
            logger.warning("Nessuna connessione attiva con VICE.")
            return "Nessuna connessione attiva."

        try:
            self.socket.settimeout(0.1)
            try:
                while True:
                    self.socket.recv(1024)
            except socket.timeout:
                pass

            self.socket.settimeout(2.0)

            if not cmd.endswith("\n"):
                cmd += "\n"

            self.socket.sendall(cmd.encode("utf-8"))

            response = ""
            while True:
                data = self.socket.recv(2048).decode("utf-8", errors="ignore")
                if not data:
                    break
                response += data
                if any(prompt in response for prompt in ["(C64)", "(CBRK)", "(C64 debugger)", "(C64 monitor)"]):
                    break

            return response.strip()
        except socket.timeout:
            logger.warning("Timeout durante l'attesa della risposta da VICE.")
            return response.strip() if response else "Timeout"
        except Exception as e:
            logger.error(f"Errore di comunicazione: {e}")
            return f"Errore: {e}"

    def get_registers(self) -> dict:
        """
        Esegue il comando 'r' sul monitor e decodifica i registri del processore 6502.
        """
        response = self.send_command("r")
        registers = {"PC": 0, "A": 0, "X": 0, "Y": 0, "SP": 0, "Flags": ""}

        import re
        match = re.search(r'\.([0-9a-fA-F]{4})\s+([0-9a-fA-F]{2})\s+([0-9a-fA-F]{2})\s+([0-9a-fA-F]{2})\s+([0-9a-fA-F]{2})', response)
        if match:
            registers["PC"] = int(match.group(1), 16)
            registers["A"] = int(match.group(2), 16)
            registers["X"] = int(match.group(3), 16)
            registers["Y"] = int(match.group(4), 16)
            registers["SP"] = int(match.group(5), 16)
        else:
            for line in response.splitlines():
                if "PC=" in line or "A=" in line:
                    for part in line.split():
                        if "=" in part:
                            k, v = part.split("=")
                            try:
                                registers[k] = int(v.replace("$", ""), 16)
                            except ValueError:
                                registers[k] = v
        return registers

    def read_memory(self, start_addr: int, end_addr: int) -> bytes:
        """
        Legge una porzione di memoria usando il comando 'm'.
        """
        cmd = f"m {start_addr:04x} {end_addr:04x}"
        response = self.send_command(cmd)

        byte_list = []
        for line in response.splitlines():
            line = line.strip()
            if line.startswith(".") or line.startswith(">"):
                parts = line.split()
                if len(parts) > 1:
                    for part in parts[1:]:
                        if len(part) != 2 or not all(c in "0123456789abcdefABCDEF" for c in part):
                            break
                        byte_list.append(int(part, 16))
        return bytes(byte_list)

    def write_memory(self, addr: int, data: bytes) -> bool:
        """
        Scrive dei byte in memoria usando il comando '>' del monitor.
        """
        if not data:
            return True
        bytes_str = " ".join(f"{b:02x}" for b in data)
        cmd = f"> {addr:04x} {bytes_str}"
        self.send_command(cmd)
        return True

    def set_breakpoint(self, addr: int) -> bool:
        """
        Imposta un breakpoint ad un indirizzo specifico.
        """
        response = self.send_command(f"break {addr:04x}")
        return "Breakpoint" in response or "impostato" in response or "Breakpoint" in self.send_command("bk")

    def step_instruction(self) -> dict:
        """
        Esegue un singolo step (istruzione successiva) e ritorna lo stato dei registri.
        """
        self.send_command("z")
        return self.get_registers()

    def stop_execution(self):
        """
        Invia un comando di stop all'emulatore.
        """
        self.send_command("stop")

    def resume_execution(self):
        """
        Invia un comando di go per riprendere l'esecuzione ordinaria.
        """
        self.send_command("g")

    def disconnect(self):
        """
        Chiude la connessione socket.
        """
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            logger.info("Connessione socket chiusa.")

    def kill_vice(self):
        """
        Termina forzatamente il processo dell'emulatore VICE.
        """
        self.disconnect()
        if self.vice_process:
            try:
                self.vice_process.kill()
                logger.info("Processo VICE terminato.")
            except:
                pass
            self.vice_process = None
        else:
            try:
                os.system("killall -9 x64sc 2>/dev/null || true")
            except:
                pass
