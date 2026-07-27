# Copyright (c) 2026 Moonspace Labs, LLC
# Licensed under the MIT License. See LICENSE in the project root for license information.

"""
Client for the Commodore 64 Ultimate's REST API.
"""

import urllib.parse
from typing import List, Dict, Any, Optional
import httpx

class C64UltimateClient:
    def __init__(self):
        pass

    def _build_endpoint_uri(self, base_url: str, path: str) -> str:
        if not base_url or base_url.isspace():
            raise ValueError("The C64 Ultimate URL has not been configured.")

        # Ensure base URL is absolute
        parsed = urllib.parse.urlparse(base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"'{base_url}' is not a valid URL.")

        if not base_url.endswith('/'):
            base_url += '/'

        return urllib.parse.urljoin(base_url, path)

    async def load_prg_async(self, base_url: str, prg_data: bytes) -> str:
        """
        Uploads a tokenized BASIC program and runs it via POST /v1/runners:load_prg.
        """
        endpoint = self._build_endpoint_uri(base_url, "v1/runners:load_prg")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                content=prg_data,
                headers={"Content-Type": "application/octet-stream"}
            )
            response.raise_for_status()
            return response.text

    async def run_prg_async(self, base_url: str, prg_data: bytes) -> str:
        """
        Uploads a tokenized BASIC program and runs it immediately via POST /v1/runners:run_prg.
        """
        endpoint = self._build_endpoint_uri(base_url, "v1/runners:run_prg")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                content=prg_data,
                headers={"Content-Type": "application/octet-stream"}
            )
            response.raise_for_status()
            return response.text

    async def get_info_async(self, base_url: str) -> Dict[str, Any]:
        """
        Retrieves basic device information via GET /v1/info.
        """
        endpoint = self._build_endpoint_uri(base_url, "v1/info")
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            return response.json()

    async def machine_action_async(self, base_url: str, action: str) -> None:
        """
        Sends a machine control command via PUT /v1/machine:{action} (reset, reboot, pause, resume, poweroff).
        """
        endpoint = self._build_endpoint_uri(base_url, f"v1/machine:{action}")
        async with httpx.AsyncClient() as client:
            response = await client.put(endpoint)
            response.raise_for_status()

    async def get_drives_async(self, base_url: str) -> List[Dict[str, Any]]:
        """
        Retrieves the status of all drives via GET /v1/drives.
        """
        endpoint = self._build_endpoint_uri(base_url, "v1/drives")
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            body = response.json()

            drives = []
            if "drives" in body:
                for entry in body["drives"]:
                    for drive_id, drive_val in entry.items():
                        drives.append({
                            "id": drive_id,
                            "enabled": drive_val.get("enabled", False),
                            "type": drive_val.get("type"),
                            "image_file": drive_val.get("image_file", "")
                        })
            return drives

    async def mount_drive_async(self, base_url: str, drive_id: str, image_path: str) -> None:
        """
        Mounts a disk image already on the device's storage to the given drive via PUT /v1/drives/{driveId}:mount.
        """
        escaped_path = urllib.parse.quote(image_path)
        endpoint = self._build_endpoint_uri(base_url, f"v1/drives/{drive_id}:mount?image={escaped_path}")
        async with httpx.AsyncClient() as client:
            response = await client.put(endpoint)
            response.raise_for_status()

    async def remove_drive_async(self, base_url: str, drive_id: str) -> None:
        """
        Ejects the disk image currently mounted on the given drive via PUT /v1/drives/{driveId}:remove.
        """
        endpoint = self._build_endpoint_uri(base_url, f"v1/drives/{drive_id}:remove")
        async with httpx.AsyncClient() as client:
            response = await client.put(endpoint)
            response.raise_for_status()
