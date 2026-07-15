import os
import re
import struct
import logging

from .basic_tokens import detokenize_basic, hex_dump

log = logging.getLogger("g64")

GCR5_TO_4 = {
    0x0A: 0,
    0x0B: 1,
    0x12: 2,
    0x13: 3,
    0x0E: 4,
    0x0F: 5,
    0x16: 6,
    0x17: 7,
    0x09: 8,
    0x19: 9,
    0x1A: 10,
    0x1B: 11,
    0x0D: 12,
    0x1D: 13,
    0x1E: 14,
    0x1F: 15,
}

SECTORS_PER_TRACK = {
    1: 21,
    2: 21,
    3: 21,
    4: 21,
    5: 21,
    6: 21,
    7: 21,
    8: 21,
    9: 21,
    10: 21,
    11: 21,
    12: 21,
    13: 21,
    14: 21,
    15: 21,
    16: 21,
    17: 21,
    18: 19,
    19: 19,
    20: 19,
    21: 19,
    22: 19,
    23: 19,
    24: 19,
    25: 18,
    26: 18,
    27: 18,
    28: 18,
    29: 18,
    30: 18,
    31: 17,
    32: 17,
    33: 17,
    34: 17,
    35: 17,
    36: 17,
    37: 17,
    38: 17,
    39: 17,
    40: 17,
}

TYPE_MAP = {0x80: "DEL", 0x82: "PRG", 0x81: "SEQ", 0x83: "USR", 0x84: "REL"}


class G64Error(Exception):
    pass


class G64Image:
    def __init__(self, data: bytes):
        self._data = data
        self._header = self._read_g64_header()

    @classmethod
    def load(cls, path: str) -> "G64Image":
        with open(path, "rb") as f:
            return cls(f.read())

    def _read_g64_header(self) -> dict:
        d = self._data
        if len(d) < 12:
            raise G64Error("G64: file troppo corto")
        if d[:7] != b"GCR-154" and d[:7] != b"GCR-154":
            sig = d[:7]
            raise G64Error(f"G64: firma non valida: {sig}")
        version = struct.unpack_from("<I", d, 8)[0]
        num_tracks = struct.unpack_from("<I", d, 12)[0]
        track_offsets = []
        for i in range(84):
            off = struct.unpack_from("<I", d, 20 + i * 4)[0]
            track_offsets.append(off)
        track_sizes = []
        for i in range(84):
            sz = struct.unpack_from("<I", d, 20 + 84 * 4 + i * 4)[0]
            track_sizes.append(sz)
        actual_tracks = []
        for t_idx in range(min(num_tracks, 84)):
            off = track_offsets[t_idx]
            sz = track_sizes[t_idx]
            if off > 0 and sz > 0 and off + sz <= len(d):
                actual_tracks.append((t_idx + 1, off, sz))
        return {
            "version": version,
            "num_tracks": num_tracks,
            "tracks": actual_tracks,
        }

    def _decode_sector(self, gcr_bytes: bytes) -> bytes | None:
        nibbles = []
        for b in gcr_bytes:
            g5 = b & 0x1F
            val = GCR5_TO_4.get(g5)
            if val is None:
                return None
            nibbles.append(val)
        decoded = bytearray()
        for i in range(0, len(nibbles) - 1, 2):
            decoded.append((nibbles[i] << 4) | nibbles[i + 1])
        return bytes(decoded)

    def _scan_track(self, track_data: bytes) -> list[dict]:
        sectors: list[dict] = []
        i = 0
        while i < len(track_data) - 10:
            if track_data[i] == 0xFF:
                sync_start = i
                while i < len(track_data) and track_data[i] == 0xFF:
                    i += 1
                sync_len = i - sync_start
                if sync_len < 5:
                    continue
                while i < len(track_data) and track_data[i] == 0x55:
                    i += 1
                if i >= len(track_data):
                    break
                marker = track_data[i]
                i += 1
                if marker == 0x08:
                    header_gcr = track_data[i : i + 20]
                    i += len(header_gcr)
                    decoded = self._decode_sector(header_gcr)
                    if decoded and len(decoded) >= 6:
                        sectors.append(
                            {
                                "type": "header",
                                "track": decoded[0],
                                "sector": decoded[1],
                                "id1": decoded[4],
                                "id2": decoded[5],
                                "offset": sync_start,
                            }
                        )
                elif marker == 0x07:
                    data_gcr = track_data[i : i + 520]
                    i += len(data_gcr)
                    decoded = self._decode_sector(data_gcr)
                    if decoded and len(decoded) >= 257:
                        if decoded[0] == 0:
                            sectors.append(
                                {
                                    "type": "data",
                                    "data": decoded[1:257],
                                    "checksum": decoded[257],
                                    "offset": sync_start,
                                }
                            )
            else:
                i += 1
        return sectors

    def _match_sectors(self, raw_sectors: list[dict]) -> dict:
        headers = [s for s in raw_sectors if s["type"] == "header"]
        datas = [s for s in raw_sectors if s["type"] == "data"]
        result = {}
        for h in headers:
            key = (h["track"], h["sector"])
            best = None
            for d in datas:
                if best is None or abs(d["offset"] - h["offset"]) < abs(
                    best["offset"] - h["offset"]
                ):
                    best = d
            if best:
                result[key] = best["data"]
        return result

    def _read_all_sectors(self) -> dict:
        all_sectors = {}
        for track_num, track_off, track_sz in self._header["tracks"]:
            if track_num > 40:
                break
            track_data = self._data[track_off : track_off + track_sz]
            raw = self._scan_track(track_data)
            matched = self._match_sectors(raw)
            for key, data in matched.items():
                all_sectors[key] = data
        return all_sectors

    def _read_directory_from_sectors(self, sectors: dict) -> list[dict]:
        entries: list[dict] = []
        dir_sector = 18
        while True:
            key = (18, dir_sector)
            sec = sectors.get(key)
            if sec is None:
                break
            for i in range(8):
                off = i * 32
                if off + 32 > len(sec):
                    break
                entry = sec[off : off + 32]
                file_type = entry[2]
                if file_type == 0x00:
                    continue
                ftype = TYPE_MAP.get(file_type & 0x87, "???")
                raw_name = entry[5:21]
                name = "".join(
                    chr(b & 0x7F) for b in raw_name if b != 0xA0 and b != 0
                ).strip()
                size = entry[30] + (entry[31] << 8)
                entries.append(
                    {
                        "name": name,
                        "type": ftype,
                        "size_blocks": size,
                        "track": entry[3],
                        "sector": entry[4],
                    }
                )
            next_track = sec[0]
            dir_sector = sec[1]
            if next_track == 0:
                break
        return entries

    def list_files(self) -> list[dict]:
        sectors = self._read_all_sectors()
        return self._read_directory_from_sectors(sectors)

    def extract_file(self, name: str) -> bytes:
        sectors = self._read_all_sectors()
        dir_sector = 18
        target = name.upper().strip()
        while True:
            key = (18, dir_sector)
            sec = sectors.get(key)
            if sec is None:
                break
            for i in range(3):
                off = i * 32
                if off + 32 > len(sec):
                    break
                entry = sec[off : off + 32]
                raw_name = entry[5:21]
                fname = "".join(
                    chr(b & 0x7F) for b in raw_name if b != 0xA0 and b != 0
                ).strip()
                if fname.upper() == target:
                    data = bytearray()
                    t, s = entry[3], entry[4]
                    while t != 0:
                        k = (t, s)
                        if k not in sectors:
                            break
                        sec_data = sectors[k]
                        next_t = sec_data[0]
                        next_s = sec_data[1]
                        data.extend(sec_data[2:])
                        t, s = next_t, next_s
                    return bytes(data)
            next_track = sec[0]
            dir_sector = sec[1]
            if next_track == 0:
                break
        raise FileNotFoundError(f"File '{name}' not found in G64")

    def to_basic(self, name: str) -> str:
        prg_data = self.extract_file(name)
        return detokenize_basic(prg_data)

    def extract_all(self, output_dir: str) -> list[str]:
        os.makedirs(output_dir, exist_ok=True)
        entries = self.list_files()
        extracted: list[str] = []
        try:
            sectors = self._read_all_sectors()
        except Exception as e:
            log.warning(f"G64: cannot decode sectors: {e}")
            return []
        for e in entries:
            safe = re.sub(r"[^\w\-_.]", "_", e["name"].lower())
            prg_data = bytearray()

            try:
                t, s = e["track"], e["sector"]
                while t != 0:
                    k = (t, s)
                    if k not in sectors:
                        break
                    sec_data = sectors[k]
                    nt = sec_data[0]
                    ns = sec_data[1]
                    prg_data.extend(sec_data[2:])
                    t, s = nt, ns

                if not prg_data:
                    continue

                source = detokenize_basic(bytes(prg_data))
                if source.strip():
                    out_path = os.path.join(output_dir, f"{safe}.bas.txt")
                    with open(out_path, "w") as outfile:
                        outfile.write(f"REM BASIC extracted from G64\n")
                        outfile.write(f"REM File: {e['name']}\n\n")
                        outfile.write(source)
                    log.info(f"  BASIC -> {out_path}")
                    extracted.append(out_path)
            except Exception as ex:
                log.warning(f"  Error extracting {e['name']}: {ex}")

        return extracted


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pyc64c.formats.g64 <file.g64> [output_dir]")
        sys.exit(1)

    path = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "data/input"
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    img = G64Image.load(path)
    files = img.list_files()
    print(f"Directory ({len(files)} file):")
    for f in files:
        print(f"  {f['type']}: {f['name']} ({f['size_blocks']} blocchi)")

    extracted = img.extract_all(output)
    print(f"\nEstratti {len(extracted)} file.")


if __name__ == "__main__":
    main()
