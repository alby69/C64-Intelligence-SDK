import os
import re
import logging

from .basic_tokens import detokenize_basic

log = logging.getLogger("d64")


def _track_offsets():
    offsets = {}
    offset = 0
    for t in range(1, 36):
        sectors = 21 if t < 18 else 19 if t < 25 else 18 if t < 31 else 17
        offsets[t] = (offset, sectors)
        offset += sectors * 256
    return offsets


TRACK_OFFSETS = _track_offsets()
TYPE_MAP = {0x80: "DEL", 0x81: "SEQ", 0x82: "PRG", 0x83: "USR", 0x84: "REL"}


class D64Error(Exception):
    pass


class D64Image:
    def __init__(self, data: bytes):
        self._data = data

    @classmethod
    def load(cls, path: str) -> "D64Image":
        with open(path, "rb") as f:
            return cls(f.read())

    def _read_sector(self, track: int, sector: int) -> bytes:
        if track not in TRACK_OFFSETS:
            raise D64Error(f"Track {track} out of range")
        t_off, t_sectors = TRACK_OFFSETS[track]
        if sector >= t_sectors:
            raise D64Error(f"Sector {sector} out of range for track {track}")
        start = t_off + sector * 256
        return self._data[start : start + 256]

    def _read_chain(self, track: int, sector: int) -> bytes:
        data = bytearray()
        while track != 0:
            sec = self._read_sector(track, sector)
            next_track = sec[0]
            next_sector = sec[1]
            data.extend(sec[2:])
            track, sector = next_track, next_sector
        return bytes(data)

    def list_files(self) -> list[dict]:
        entries: list[dict] = []
        dir_sector = 18
        while True:
            sec = self._read_sector(18, dir_sector)
            for i in range(8):
                off = i * 32
                entry = sec[off : off + 32]
                if len(entry) < 32:
                    break
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

    def extract_file(self, name: str) -> bytes:
        dir_sector = 18
        target = name.upper().strip()
        while True:
            sec = self._read_sector(18, dir_sector)
            for i in range(3):
                off = i * 32
                entry = sec[off : off + 32]
                if len(entry) < 5:
                    break
                raw_name = entry[5:21]
                fname = "".join(
                    chr(b & 0x7F) for b in raw_name if b != 0xA0 and b != 0
                ).strip()
                if fname.upper() == target:
                    return self._read_chain(entry[3], entry[4])
            next_track = sec[0]
            dir_sector = sec[1]
            if next_track == 0:
                break
        raise FileNotFoundError(f"File '{name}' not found in D64")

    def to_basic(self, name: str) -> str:
        prg_data = self.extract_file(name)
        return detokenize_basic(prg_data)

    def extract_all(self, output_dir: str) -> list[str]:
        os.makedirs(output_dir, exist_ok=True)
        entries = self.list_files()
        extracted: list[str] = []
        for e in list(entries):
            if e["type"] == "PRG":
                try:
                    prg_data = self.extract_file(e["name"])
                    source = detokenize_basic(prg_data)
                    if source.strip():
                        safe = re.sub(r"[^\w\-_.]", "_", e["name"].lower())
                        out_path = os.path.join(output_dir, f"{safe}.dat.txt")
                        with open(out_path, "w") as f:
                            f.write(f"REM BASIC program extracted from D64\n")
                            f.write(f"REM File: {e['name']}\n\n")
                            f.write(source)
                        log.info(f"  BASIC -> {out_path}")
                        extracted.append(out_path)
                except Exception as ex:
                    log.warning(f"  Error extracting {e['name']}: {ex}")
        return extracted


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pyc64c.formats.d64 <file.d64> [output_dir]")
        sys.exit(1)

    path = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "data/input"
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    img = D64Image.load(path)
    files = img.list_files()
    print(f"Directory ({len(files)} file):")
    for f in files:
        print(f"  {f['type']}: {f['name']} ({f['size_blocks']} blocchi)")

    extracted = img.extract_all(output)
    print(f"\nEstratti {len(extracted)} file.")


if __name__ == "__main__":
    main()
