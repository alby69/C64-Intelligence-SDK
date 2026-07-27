# Copyright (c) 2026 Moonspace Labs, LLC
# Licensed under the MIT License. See LICENSE in the project root for license information.

"""
Client for running programs on the VICE emulator via its binary monitor interface.
"""

import os
import sys
import struct
import asyncio
import tempfile
import subprocess
from typing import Tuple, Optional, Dict, Any

class ViceInfo:
    def __init__(self, version: str = ""):
        self.version = version


class ViceClient:
    _apiVersion = 0x02
    _autostartCommand = 0xdd
    _advanceInstructionsCommand = 0x71
    _exitCommand = 0xaa
    _quitCommand = 0xbb
    _resetCommand = 0xcc
    _infoCommand = 0x85
    _requestId = 1

    # Keep a paused connection alive
    _paused_reader: Optional[asyncio.StreamReader] = None
    _paused_writer: Optional[asyncio.StreamWriter] = None

    def __init__(self, monitor_host: str, monitor_port: int):
        self._monitor_host = monitor_host
        self._monitor_port = monitor_port

    async def transfer_async(self, emulator_path: str, prg_data: bytes, program_name: str, bring_to_foreground: bool):
        """
        Loads a .prg program into VICE without running it.
        """
        prg_file = self._write_prg_to_temp_file(prg_data, program_name)
        await self._send_autostart_async(emulator_path, prg_file, run_after_loading=False, bring_to_foreground=bring_to_foreground)

    async def run_async(self, emulator_path: str, prg_data: bytes, program_name: str, bring_to_foreground: bool):
        """
        Loads a .prg program into VICE and runs it immediately.
        """
        prg_file = self._write_prg_to_temp_file(prg_data, program_name)
        await self._send_autostart_async(emulator_path, prg_file, run_after_loading=True, bring_to_foreground=bring_to_foreground)

    async def reset_async(self, emulator_path: str):
        """
        Performs a soft reset of the machine currently running in VICE.
        """
        await self._require_vice_running_async()
        await self._send_one_shot_command_async(self._build_request(self._resetCommand, b'\x00'))

    async def reboot_async(self, emulator_path: str):
        """
        Performs a hard reset (power cycle) of the machine currently running in VICE.
        """
        await self._require_vice_running_async()
        await self._send_one_shot_command_async(self._build_request(self._resetCommand, b'\x01'))

    async def power_off_async(self, emulator_path: str):
        """
        Quits the running VICE process, closing the emulator window.
        """
        await self._require_vice_running_async()
        await self._send_one_shot_command_async(self._build_request(self._quitCommand, b''))
        self._clear_paused_connection()

    async def pause_async(self, emulator_path: str):
        """
        Pauses the machine currently running in VICE by stepping a single instruction.
        """
        await self._require_vice_running_async()

        if self._paused_writer is not None:
            raise ValueError("VICE is already paused.")

        reader, writer = await asyncio.open_connection(self._monitor_host, self._monitor_port)

        # SO=0, IC=1 (Step 1 instruction)
        request = self._build_request(self._advanceInstructionsCommand, b'\x00\x01\x00')
        writer.write(request)
        await writer.drain()

        error_code = await self._read_response_error_code_async(reader)
        if error_code != 0:
            writer.close()
            await writer.wait_closed()
            raise ValueError(f"VICE rejected the request (binary monitor error code {error_code}).")

        # Save connection to keep VICE in stopped/paused state
        type(self)._paused_reader = reader
        type(self)._paused_writer = writer

    async def get_info_async(self) -> ViceInfo:
        """
        Retrieves version information from the VICE binary monitor.
        """
        await self._require_vice_running_async()

        reader, writer = await asyncio.open_connection(self._monitor_host, self._monitor_port)
        try:
            request = self._build_request(self._infoCommand, b'')
            writer.write(request)
            await writer.drain()

            error_code, body = await self._read_response_async(reader)
            if error_code != 0:
                raise ValueError(f"VICE rejected the request (binary monitor error code {error_code}).")

            return self._parse_info_response(body)
        finally:
            writer.close()
            await writer.wait_closed()

    async def resume_async(self):
        """
        Resumes a machine previously paused.
        """
        if self._paused_writer is None or self._paused_reader is None:
            raise ValueError("VICE is not paused.")

        try:
            request = self._build_request(self._exitCommand, b'')
            self._paused_writer.write(request)
            await self._paused_writer.drain()

            error_code = await self._read_response_error_code_async(self._paused_reader)
            if error_code != 0:
                raise ValueError(f"VICE rejected the request (binary monitor error code {error_code}).")
        finally:
            self._clear_paused_connection()

    # Private Helpers

    async def _send_autostart_async(self, emulator_path: str, prg_file_path: str, run_after_loading: bool, bring_to_foreground: bool):
        await self._ensure_vice_running_async(emulator_path)

        file_name_bytes = prg_file_path.encode('ascii', errors='ignore')
        # Autostart request body: RL (1 byte), FI (2 bytes, 0), FL (1 byte), FN (file name bytes)
        body = bytearray(4 + len(file_name_bytes))
        body[0] = 1 if run_after_loading else 0
        # body[1:3] remains 0 (file index)
        body[3] = len(file_name_bytes) & 0xFF
        body[4:] = file_name_bytes

        await self._send_one_shot_command_async(self._build_request(self._autostartCommand, bytes(body)))

        if bring_to_foreground:
            self._bring_vice_to_foreground(emulator_path)

    def _bring_vice_to_foreground(self, emulator_path: str):
        # Foreground activation is Windows-specific; on Linux/Docker it's a no-op
        if sys.platform != 'win32':
            return
        # WPF-specific focus logic not ported, stubbed for parity

    async def _send_one_shot_command_async(self, request: bytes):
        reader, writer = await asyncio.open_connection(self._monitor_host, self._monitor_port)
        try:
            writer.write(request)
            await writer.drain()

            error_code = await self._read_response_error_code_async(reader)
            if error_code != 0:
                raise ValueError(f"VICE rejected the request (binary monitor error code {error_code}).")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _require_vice_running_async(self):
        if not await self._is_monitor_listening_async():
            raise ValueError("VICE is not running. Use Transfer or Run to start it first.")

    def _clear_paused_connection(self):
        if self._paused_writer:
            try:
                self._paused_writer.close()
            except Exception:
                pass
        type(self)._paused_reader = None
        type(self)._paused_writer = None

    async def _ensure_vice_running_async(self, emulator_path: str):
        if await self._is_monitor_listening_async():
            return

        if not emulator_path or emulator_path.isspace():
            raise ValueError("The VICE emulator path has not been configured.")

        # Subprocess invocation to launch emulator
        subprocess.Popen([
            emulator_path,
            "-binarymonitor",
            "-binarymonitoraddress",
            f"{self._monitor_host}:{self._monitor_port}"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Wait up to 9 seconds
        for _ in range(30):
            if await self._is_monitor_listening_async():
                return
            await asyncio.sleep(0.3)

        raise ValueError("Timed out waiting for VICE to start.")

    async def _is_monitor_listening_async(self) -> bool:
        try:
            _, writer = await asyncio.open_connection(self._monitor_host, self._monitor_port)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    def _build_request(self, command_id: int, body: bytes) -> bytes:
        # Request Header: STX (1 byte), apiVersion (1 byte), bodyLength (4 bytes), requestId (4 bytes), commandId (1 byte)
        header = struct.pack('<BBIIB', 0x02, self._apiVersion, len(body), self._requestId, command_id)
        return header + body

    async def _read_response_error_code_async(self, reader: asyncio.StreamReader) -> int:
        error_code, _ = await self._read_response_async(reader)
        return error_code

    async def _read_response_async(self, reader: asyncio.StreamReader) -> Tuple[int, bytes]:
        for _ in range(20):
            header = await reader.readexactly(12)
            stx, api_ver, body_length, response_cmd, error_code, request_id = struct.unpack('<BBIBBI', header)

            body = await reader.readexactly(body_length)

            # Ignore unsolicited async events (req_id == 0xffffffff)
            if request_id == self._requestId:
                return error_code, body

        raise ValueError("VICE did not respond to the request.")

    def _parse_info_response(self, body: bytes) -> ViceInfo:
        version_len = body[0]
        version_bytes = body[1 : 1 + version_len]
        # Join bytes as string parts (e.g. 3.5.0.0)
        version_str = ".".join(str(b) for b in version_bytes)
        return ViceInfo(version=version_str)

    def _write_prg_to_temp_file(self, prg_data: bytes, program_name: str) -> str:
        base_name = os.path.splitext(os.path.basename(program_name))[0].lower()
        # Sanitize filename characters
        for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            base_name = base_name.replace(char, '_')

        if not base_name or base_name.isspace():
            base_name = "readycode"

        temp_dir = tempfile.gettempdir()
        path = os.path.join(temp_dir, f"{base_name}.prg")
        with open(path, 'wb') as f:
            f.write(prg_data)
        return path
