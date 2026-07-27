# Copyright (c) 2026 Moonspace Labs, LLC
# Licensed under the MIT License. See LICENSE in the project root for license information.

"""
Client for browsing and managing files on the Commodore 64 Ultimate's FTP file service.
"""

import io
import asyncio
from ftplib import FTP
from typing import List, Tuple, Optional

class C64UFtpClient:
    def __init__(self):
        self._ftp: Optional[FTP] = None

    async def connect_async(self, host: str):
        """
        Connects to the C64 Ultimate's FTP server on the given host, using its default
        "admin" account with a blank password.
        """
        if not host or host.isspace():
            raise ValueError("The C64 Ultimate URL has not been configured.")

        def _sync_connect():
            ftp = FTP()
            ftp.connect(host, 21, timeout=10)
            ftp.login("admin", "")
            return ftp

        try:
            self._ftp = await asyncio.to_thread(_sync_connect)
        except Exception as ex:
            if self._ftp:
                try:
                    self._ftp.close()
                except Exception:
                    pass
                self._ftp = None
            raise ValueError(f"Could not connect to the C64 Ultimate at '{host}': {str(ex)}")

    def _ensure_connected(self):
        if not self._ftp:
            raise ValueError("Not connected to the C64 Ultimate's FTP server.")

    async def list_directory_async(self, path: str) -> List[Tuple[str, str, bool, int]]:
        """
        Lists the immediate children of the given remote directory.
        Returns: List of (Name, FullPath, IsFolder, Size), folders first, then alphabetically by name.
        """
        self._ensure_connected()

        def _sync_list():
            items = []
            # Use MLSx command if supported (standard on C64U and modern FTP servers)
            try:
                for name, facts in self._ftp.mlsd(path):
                    if name in ('.', '..'):
                        continue
                    is_folder = facts.get("type") == "dir"
                    size = int(facts.get("size", 0))

                    # Normalize full path
                    normalized_path = path.rstrip('/') + '/' + name if path else name
                    items.append((name, normalized_path, is_folder, size))
            except Exception:
                # Fallback to standard NLST/LIST if MLSD fails
                names = self._ftp.nlst(path)
                for name in names:
                    if name in ('.', '..'):
                        continue
                    # Simple heuristic: try to cwd to see if it's a folder, or treat as file
                    is_folder = False
                    size = 0
                    try:
                        self._ftp.cwd(path.rstrip('/') + '/' + name)
                        is_folder = True
                        self._ftp.cwd(path)
                    except Exception:
                        pass
                    normalized_path = path.rstrip('/') + '/' + name if path else name
                    items.append((name, normalized_path, is_folder, size))

            # Sort: folders first, then alphabetically by name (case-insensitive)
            items.sort(key=lambda x: (not x[2], x[0].lower()))
            return items

        return await asyncio.to_thread(_sync_list)

    async def download_bytes_async(self, path: str) -> bytes:
        """
        Downloads a remote file's contents as a byte array.
        """
        self._ensure_connected()

        def _sync_download():
            bio = io.BytesIO()
            self._ftp.retrbinary(f"RETR {path}", bio.write)
            return bio.getvalue()

        return await asyncio.to_thread(_sync_download)

    async def upload_bytes_async(self, path: str, data: bytes):
        """
        Uploads a byte array to the server, overwriting any existing file at that path.
        """
        self._ensure_connected()

        def _sync_upload():
            bio = io.BytesIO(data)
            self._ftp.storbinary(f"STOR {path}", bio)

        await asyncio.to_thread(_sync_upload)

    async def create_folder_async(self, path: str):
        """
        Creates a new remote directory.
        """
        self._ensure_connected()

        def _sync_create():
            self._ftp.mkd(path)

        await asyncio.to_thread(_sync_create)

    async def delete_file_async(self, path: str):
        """
        Deletes a remote file.
        """
        self._ensure_connected()

        def _sync_delete():
            self._ftp.delete(path)

        await asyncio.to_thread(_sync_delete)

    async def delete_folder_async(self, path: str):
        """
        Deletes a remote directory and all of its contents recursively.
        """
        self._ensure_connected()

        def _sync_delete_folder():
            def _rec_delete(p: str):
                try:
                    for name, facts in self._ftp.mlsd(p):
                        if name in ('.', '..'):
                            continue
                        full_p = p.rstrip('/') + '/' + name
                        if facts.get("type") == "dir":
                            _rec_delete(full_p)
                        else:
                            self._ftp.delete(full_p)
                except Exception:
                    # Fallback recursive logic
                    pass
                self._ftp.rmd(p)

            _rec_delete(path)

        await asyncio.to_thread(_sync_delete_folder)

    async def rename_async(self, old_path: str, new_path: str):
        """
        Renames or moves a remote file or directory.
        """
        self._ensure_connected()

        def _sync_rename():
            self._ftp.rename(old_path, new_path)

        await asyncio.to_thread(_sync_rename)

    async def disconnect_async(self):
        """
        Disconnects from the server.
        """
        if self._ftp:
            def _sync_disconnect():
                try:
                    self._ftp.quit()
                except Exception:
                    try:
                        self._ftp.close()
                    except Exception:
                        pass

            await asyncio.to_thread(_sync_disconnect)
            self._ftp = None

    def dispose(self):
        """
        Disconnects and releases the underlying FTP connection.
        """
        if self._ftp:
            try:
                self._ftp.close()
            except Exception:
                pass
            self._ftp = None
