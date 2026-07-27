import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from readycode_py.ultimate_client import C64UltimateClient
from readycode_py.ultimate_ftp import C64UFtpClient
from readycode_py.vice_client import ViceClient, ViceInfo

# -- C64UltimateClient Mocks --

@pytest.mark.asyncio
async def test_ultimate_client_get_info():
    client = C64UltimateClient()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"version": "3.10"}
    mock_resp.raise_for_status = MagicMock()

    with patch('httpx.AsyncClient.get', AsyncMock(return_value=mock_resp)) as mock_get:
        info = await client.get_info_async("http://localhost:8000")
        assert info == {"version": "3.10"}
        mock_get.assert_called_once_with("http://localhost:8000/v1/info")

@pytest.mark.asyncio
async def test_ultimate_client_run_prg():
    client = C64UltimateClient()
    mock_resp = MagicMock()
    mock_resp.text = "OK"
    mock_resp.raise_for_status = MagicMock()

    with patch('httpx.AsyncClient.post', AsyncMock(return_value=mock_resp)) as mock_post:
        res = await client.run_prg_async("http://localhost:8000", b"\x01\x08")
        assert res == "OK"
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_ultimate_client_get_drives():
    client = C64UltimateClient()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "drives": [
            {"a": {"enabled": True, "type": "1541", "image_file": "game.d64"}}
        ]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch('httpx.AsyncClient.get', AsyncMock(return_value=mock_resp)):
        drives = await client.get_drives_async("http://localhost:8000")
        assert len(drives) == 1
        assert drives[0]["id"] == "a"
        assert drives[0]["enabled"] is True
        assert drives[0]["image_file"] == "game.d64"


# -- C64UFtpClient Mocks --

@pytest.mark.asyncio
async def test_ftp_client_connect_and_list():
    client = C64UFtpClient()
    mock_ftp = MagicMock()
    mock_ftp.mlsd.return_value = [
        ("game.d64", {"type": "file", "size": "174848"}),
        ("docs", {"type": "dir", "size": "0"})
    ]

    with patch('readycode_py.ultimate_ftp.FTP', return_value=mock_ftp):
        await client.connect_async("192.168.1.64")
        listing = await client.list_directory_async("/USB")

        # Sorts folders first, then files
        assert len(listing) == 2
        assert listing[0][0] == "docs"  # Folder first
        assert listing[0][2] is True    # is_folder
        assert listing[1][0] == "game.d64"
        assert listing[1][2] is False   # is_folder
        assert listing[1][3] == 174848


# -- ViceClient Mocks --

@pytest.mark.asyncio
async def test_vice_client_get_info():
    client = ViceClient("127.0.0.1", 6502)

    mock_reader = AsyncMock()
    # Response header: STX (0x02), version, body_length (4 bytes: 5), cmd, err, req_id (4 bytes: 1)
    # let's construct bytes for struct.pack('<BBIBBI', 0x02, 0x02, 5, 0, 0, 1)
    # len is 12 bytes
    import struct
    header_bytes = struct.pack('<BBIBBI', 0x02, 0x02, 5, 0x85, 0, 1)
    # Body bytes: version_len (1 byte: 4), version (4 bytes: 3, 5, 0, 0)
    body_bytes = bytes([4, 3, 5, 0, 0])

    mock_reader.readexactly.side_effect = [header_bytes, body_bytes]
    mock_writer = AsyncMock()

    # Stub asyncio.open_connection to return our mock reader/writer
    with patch('asyncio.open_connection', AsyncMock(return_value=(mock_reader, mock_writer))):
        info = await client.get_info_async()
        assert isinstance(info, ViceInfo)
        assert info.version == "3.5.0.0"
