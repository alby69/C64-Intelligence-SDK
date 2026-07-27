# Copyright (c) 2026 Moonspace Labs, LLC
# Licensed under the MIT License. See LICENSE in the project root for license information.

"""
Reads the directory and file contents of a CBM DOS disk image (.d64 or .d81).
"""

from enum import Enum, auto
from typing import List, Tuple, Optional
from .tokenizer import PrgConverter

class C64UFileKind(Enum):
    Folder = auto()
    Bas = auto()
    Prg = auto()
    Ml = auto()
    Asm = auto()
    D64 = auto()
    D81 = auto()
    Other = auto()


class DiskFormat(Enum):
    D64 = auto()
    D81 = auto()


class DiskGeometry:
    def __init__(
        self,
        sectors_per_track: List[int],
        directory_track: int,
        directory_sector: int,
        standard_image_size: int,
        max_chain_steps: int,
        disk_format: DiskFormat
    ):
        self.sectors_per_track = sectors_per_track
        self.directory_track = directory_track
        self.directory_sector = directory_sector
        self.standard_image_size = standard_image_size
        self.max_chain_steps = max_chain_steps
        self.disk_format = disk_format

    @classmethod
    def _build_uniform(cls, tracks: int, sectors_per_track: int) -> List[int]:
        table = [0] * (tracks + 1)
        for t in range(1, tracks + 1):
            table[t] = sectors_per_track
        return table


# Standard 1541 Disk Geometry
DiskGeometry.D64 = DiskGeometry(
    sectors_per_track=[
        0, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
           19, 19, 19, 19, 19, 19, 19,
           18, 18, 18, 18, 18, 18,
           17, 17, 17, 17, 17
    ],
    directory_track=18,
    directory_sector=1,
    standard_image_size=174848,
    max_chain_steps=700,
    disk_format=DiskFormat.D64
)

# Standard 1581 Disk Geometry
DiskGeometry.D81 = DiskGeometry(
    sectors_per_track=DiskGeometry._build_uniform(80, 40),
    directory_track=40,
    directory_sector=3,
    standard_image_size=819200,
    max_chain_steps=3300,
    disk_format=DiskFormat.D81
)


class D64Entry:
    def __init__(self, name: str, kind: C64UFileKind, content: bytes):
        self.name = name
        self.kind = kind
        self.content = content


class DiskImage:
    def __init__(self, geometry: DiskGeometry):
        self._geometry = geometry

    @classmethod
    def for_kind(cls, kind: C64UFileKind) -> 'DiskImage':
        if kind == C64UFileKind.D64:
            return cls(DiskGeometry.D64)
        elif kind == C64UFileKind.D81:
            return cls(DiskGeometry.D81)
        else:
            raise ValueError(f"{kind} is not a disk image kind.")

    def read_directory(self, disk_image: bytes) -> List[D64Entry]:
        self._validate_image_size(disk_image)

        entries = []
        track = self._geometry.directory_track
        sector = self._geometry.directory_sector
        steps = 0

        while track != 0 and steps < self._geometry.max_chain_steps:
            steps += 1
            dir_sector = self._read_sector(disk_image, track, sector)
            next_track = dir_sector[0]
            next_sector = dir_sector[1]

            for i in range(8):
                entry_offset = 2 + i * 32
                type_byte = dir_sector[entry_offset]
                if (type_byte & 0x80) == 0:
                    continue  # not closed (scratched/invalid) - skip

                file_track = dir_sector[entry_offset + 1]
                file_sector = dir_sector[entry_offset + 2]
                name_bytes = dir_sector[entry_offset + 3 : entry_offset + 19]

                name = self._decode_name(name_bytes)
                if not name:
                    continue

                content = self._read_file_chain(disk_image, file_track, file_sector)

                is_prg_type = (type_byte & 0x0F) == 2
                is_basic = is_prg_type and PrgConverter().is_basic_program(content)

                entries.append(D64Entry(
                    name=name,
                    kind=C64UFileKind.Prg if is_basic else (C64UFileKind.Ml if is_prg_type else C64UFileKind.Other),
                    content=content
                ))

            track = next_track
            sector = next_sector

        return entries

    def create_blank_image(self, disk_name: str) -> bytes:
        image = bytearray(self._geometry.standard_image_size)
        self._initialize_bam(image, disk_name)

        dir_sector_offset = self._sector_offset(self._geometry.directory_track, self._geometry.directory_sector)
        image[dir_sector_offset] = 0
        image[dir_sector_offset + 1] = 0xFF  # end of directory chain

        return bytes(image)

    def get_free_sectors(self, disk_image: bytes) -> List[Tuple[int, int]]:
        self._validate_image_size(disk_image)

        free_sectors = []
        total_tracks = len(self._geometry.sectors_per_track) - 1
        for t in range(1, total_tracks + 1):
            sectors_on_track = self._geometry.sectors_per_track[t]
            for s in range(sectors_on_track):
                if self._is_sector_free(disk_image, t, s):
                    free_sectors.append((t, s))
        return free_sectors

    def add_entry(self, disk_image: bytes, name: str, kind: C64UFileKind, content: bytes) -> bytes:
        self._validate_image_size(disk_image)
        image = bytearray(disk_image)

        chain = self._allocate_sector_chain(image, self._sectors_needed(len(content)))
        self._write_file_chain(image, chain, content)

        track, sector, index = self._find_free_directory_slot_or_extend(image)
        self._write_directory_entry(image, track, sector, index, name, chain[0][0], chain[0][1])

        return bytes(image)

    def delete_entry(self, disk_image: bytes, name: str) -> bytes:
        self._validate_image_size(disk_image)
        image = bytearray(disk_image)

        slot = self._find_directory_slot_by_name(image, name)
        if slot is None:
            raise ValueError(f"'{name}' was not found on this disk.")

        track, sector, index = slot
        entry_offset = self._sector_offset(track, sector) + 2 + index * 32
        file_track = image[entry_offset + 1]
        file_sector = image[entry_offset + 2]

        image[entry_offset] &= 0x7F  # clear the "closed" bit - scratches the entry
        self._free_sector_chain(image, file_track, file_sector)

        return bytes(image)

    def rename_entry(self, disk_image: bytes, old_name: str, new_name: str) -> bytes:
        self._validate_image_size(disk_image)
        image = bytearray(disk_image)

        slot = self._find_directory_slot_by_name(image, old_name)
        if slot is None:
            raise ValueError(f"'{old_name}' was not found on this disk.")

        track, sector, index = slot
        entry_offset = self._sector_offset(track, sector) + 2 + index * 32
        encoded = self._encode_name(new_name, 16)
        image[entry_offset + 3 : entry_offset + 19] = encoded

        return bytes(image)

    def replace_entry(self, disk_image: bytes, name: str, new_content: bytes) -> bytes:
        image = self.delete_entry(disk_image, name)
        return self.add_entry(image, name, C64UFileKind.Prg, new_content)

    # Private helpers

    def _read_file_chain(self, disk_image: bytes, track: int, sector: int) -> bytes:
        content = bytearray()
        steps = 0

        while track != 0 and steps < self._geometry.max_chain_steps:
            steps += 1
            data = self._read_sector(disk_image, track, sector)
            next_track = data[0]
            next_sector = data[1]

            if next_track == 0:
                # next_sector holds the offset of the last used byte, inclusive
                content.extend(data[2 : 1 + next_sector])
                break

            content.extend(data[2:256])
            track = next_track
            sector = next_sector

        return bytes(content)

    def _read_sector(self, disk_image: bytes, track: int, sector: int) -> bytes:
        offset = self._sector_offset(track, sector)
        return disk_image[offset : offset + 256]

    def _sector_offset(self, track: int, sector: int) -> int:
        sectors_per_track = self._geometry.sectors_per_track
        if track < 1 or track >= len(sectors_per_track):
            raise ValueError(f"Invalid track {track} in disk image directory/file chain.")

        sectors_before = sum(sectors_per_track[1:track])
        return (sectors_before + sector) * 256

    def _decode_name(self, raw: bytes) -> str:
        length = len(raw)
        while length > 0 and raw[length - 1] == 0xA0:
            length -= 1

        chars = []
        for b in raw[:length]:
            chars.append(chr(b) if 0x20 <= b <= 0x5F else '?')
        return "".join(chars)

    def _validate_image_size(self, disk_image: bytes):
        if len(disk_image) != self._geometry.standard_image_size:
            raise ValueError(
                f"Not a standard disk image ({len(disk_image)} bytes; expected {self._geometry.standard_image_size})."
            )

    def _write_sector(self, disk_image: bytearray, track: int, sector: int, data: bytes):
        offset = self._sector_offset(track, sector)
        disk_image[offset : offset + 256] = data

    def _sectors_needed(self, content_length: int) -> int:
        return 1 if content_length == 0 else (content_length + 253) // 254

    def _write_file_chain(self, disk_image: bytearray, chain: List[Tuple[int, int]], content: bytes):
        offset = 0
        for i, (track, sector) in enumerate(chain):
            sector_data = bytearray(256)
            is_last = (i == len(chain) - 1)
            if is_last:
                remaining = len(content) - offset
                sector_data[0] = 0
                sector_data[1] = (remaining + 1) & 0xFF
                sector_data[2 : 2 + remaining] = content[offset:]
            else:
                next_track, next_sector = chain[i + 1]
                sector_data[0] = next_track & 0xFF
                sector_data[1] = next_sector & 0xFF
                sector_data[2:256] = content[offset : offset + 254]
                offset += 254

            self._write_sector(disk_image, track, sector, bytes(sector_data))

    def _allocate_sector_chain(self, disk_image: bytearray, count: int) -> List[Tuple[int, int]]:
        result = []
        reserved_track = self._geometry.directory_track
        total_tracks = len(self._geometry.sectors_per_track) - 1

        for t in range(1, total_tracks + 1):
            if t == reserved_track:
                continue
            sectors_on_track = self._geometry.sectors_per_track[t]
            for s in range(sectors_on_track):
                if len(result) >= count:
                    break
                if self._is_sector_free(disk_image, t, s):
                    result.append((t, s))

        if len(result) < count:
            raise ValueError("Not enough free space on this disk image.")

        for t, s in result:
            self._set_sector_free(disk_image, t, s, False)

        return result

    def _free_sector_chain(self, disk_image: bytearray, track: int, sector: int):
        steps = 0
        while track != 0 and steps < self._geometry.max_chain_steps:
            steps += 1
            sector_offset = self._sector_offset(track, sector)
            next_track = disk_image[sector_offset]
            next_sector = disk_image[sector_offset + 1]
            self._set_sector_free(disk_image, track, sector, True)
            track = next_track
            sector = next_sector

    def _find_free_directory_slot_or_extend(self, disk_image: bytearray) -> Tuple[int, int, int]:
        track = self._geometry.directory_track
        sector = self._geometry.directory_sector
        steps = 0
        last_track, last_sector = track, sector

        while track != 0 and steps < self._geometry.max_chain_steps:
            steps += 1
            sector_offset = self._sector_offset(track, sector)
            for i in range(8):
                type_byte = disk_image[sector_offset + 2 + i * 32]
                if (type_byte & 0x80) == 0:
                    return (track, sector, i)

            last_track = track
            last_sector = sector
            next_track = disk_image[sector_offset]
            next_sector = disk_image[sector_offset + 1]
            if next_track == 0:
                break
            track = next_track
            sector = next_sector

        # Allocate new directory sector
        new_track, new_sector = self._allocate_sector_on_track(disk_image, self._geometry.directory_track)

        last_sector_offset = self._sector_offset(last_track, last_sector)
        disk_image[last_sector_offset] = new_track & 0xFF
        disk_image[last_sector_offset + 1] = new_sector & 0xFF

        new_sector_offset = self._sector_offset(new_track, new_sector)
        disk_image[new_sector_offset : new_sector_offset + 256] = b'\x00' * 256
        disk_image[new_sector_offset] = 0
        disk_image[new_sector_offset + 1] = 0xFF

        return (new_track, new_sector, 0)

    def _allocate_sector_on_track(self, disk_image: bytearray, track: int) -> Tuple[int, int]:
        sectors_on_track = self._geometry.sectors_per_track[track]
        for s in range(sectors_on_track):
            if self._is_sector_free(disk_image, track, s):
                self._set_sector_free(disk_image, track, s, False)
                return (track, s)

        return self._allocate_sector_chain(disk_image, 1)[0]

    def _write_directory_entry(
        self, disk_image: bytearray, track: int, sector: int, index: int,
        name: str, file_track: int, file_sector: int
    ):
        entry_offset = self._sector_offset(track, sector) + 2 + index * 32
        disk_image[entry_offset] = 0x82  # closed (0x80) + PRG type (0x02)
        disk_image[entry_offset + 1] = file_track & 0xFF
        disk_image[entry_offset + 2] = file_sector & 0xFF
        encoded = self._encode_name(name, 16)
        disk_image[entry_offset + 3 : entry_offset + 19] = encoded

    def _find_directory_slot_by_name(self, disk_image: bytearray, name: str) -> Optional[Tuple[int, int, int]]:
        track = self._geometry.directory_track
        sector = self._geometry.directory_sector
        steps = 0
        target = name.upper()

        while track != 0 and steps < self._geometry.max_chain_steps:
            steps += 1
            sector_offset = self._sector_offset(track, sector)
            for i in range(8):
                entry_offset = 2 + i * 32
                type_byte = disk_image[sector_offset + entry_offset]
                if (type_byte & 0x80) == 0:
                    continue

                entry_name = self._decode_name(disk_image[sector_offset + entry_offset + 3 : sector_offset + entry_offset + 19])
                if entry_name == target:
                    return (track, sector, i)

            next_track = disk_image[sector_offset]
            next_sector = disk_image[sector_offset + 1]
            track = next_track
            sector = next_sector

        return None

    def _initialize_bam(self, disk_image: bytearray, disk_name: str):
        total_tracks = len(self._geometry.sectors_per_track) - 1
        bitmap_bytes = 3 if self._geometry.disk_format == DiskFormat.D64 else 5

        for t in range(1, total_tracks + 1):
            bam_track, bam_sector, byte_offset = self._locate_bam_entry(t)
            sector_offset = self._sector_offset(bam_track, bam_sector)
            count = self._geometry.sectors_per_track[t]
            disk_image[sector_offset + byte_offset] = count & 0xFF

            for b in range(bitmap_bytes):
                bits_in_this_byte = max(0, min(8, count - b * 8))
                disk_image[sector_offset + byte_offset + 1 + b] = 0 if bits_in_this_byte == 0 else ((1 << bits_in_this_byte) - 1) & 0xFF

        if self._geometry.disk_format == DiskFormat.D64:
            self._set_sector_free(disk_image, self._geometry.directory_track, 0, False)
        else:
            self._set_sector_free(disk_image, self._geometry.directory_track, 0, False)
            self._set_sector_free(disk_image, self._geometry.directory_track, 1, False)
            self._set_sector_free(disk_image, self._geometry.directory_track, 2, False)

        self._set_sector_free(disk_image, self._geometry.directory_track, self._geometry.directory_sector, False)
        self._write_header(disk_image, disk_name)

    def _write_header(self, disk_image: bytearray, disk_name: str):
        name_bytes = self._encode_name(disk_name, 16)
        disk_id = [ord('0'), ord('1')]

        if self._geometry.disk_format == DiskFormat.D64:
            bam_offset = self._sector_offset(self._geometry.directory_track, 0)
            disk_image[bam_offset + 0x00] = self._geometry.directory_track & 0xFF
            disk_image[bam_offset + 0x01] = self._geometry.directory_sector & 0xFF
            disk_image[bam_offset + 0x02] = ord('A')
            disk_image[bam_offset + 0x03] = 0
            disk_image[bam_offset + 0x90 : bam_offset + 0xA0] = name_bytes
            disk_image[bam_offset + 0xA0] = 0xA0
            disk_image[bam_offset + 0xA1] = 0xA0
            disk_image[bam_offset + 0xA2] = disk_id[0]
            disk_image[bam_offset + 0xA3] = disk_id[1]
            disk_image[bam_offset + 0xA4] = 0xA0
            disk_image[bam_offset + 0xA5] = ord('2')
            disk_image[bam_offset + 0xA6] = ord('A')
            disk_image[bam_offset + 0xA7] = 0xA0
            disk_image[bam_offset + 0xA8] = 0xA0
            disk_image[bam_offset + 0xA9] = 0xA0
            disk_image[bam_offset + 0xAA] = 0xA0
        else:
            header_offset = self._sector_offset(self._geometry.directory_track, 0)
            disk_image[header_offset + 0x00] = self._geometry.directory_track & 0xFF
            disk_image[header_offset + 0x01] = self._geometry.directory_sector & 0xFF
            disk_image[header_offset + 0x02] = ord('D')
            disk_image[header_offset + 0x03] = 0
            disk_image[header_offset + 0x04 : header_offset + 0x14] = name_bytes
            disk_image[header_offset + 0x14] = 0xA0
            disk_image[header_offset + 0x15] = 0xA0
            disk_image[header_offset + 0x16] = disk_id[0]
            disk_image[header_offset + 0x17] = disk_id[1]
            disk_image[header_offset + 0x18] = 0xA0
            disk_image[header_offset + 0x19] = ord('3')
            disk_image[header_offset + 0x1A] = ord('D')
            disk_image[header_offset + 0x1B] = 0xA0
            disk_image[header_offset + 0x1C] = 0xA0

            bam1_offset = self._sector_offset(self._geometry.directory_track, 1)
            disk_image[bam1_offset + 0] = self._geometry.directory_track & 0xFF
            disk_image[bam1_offset + 1] = 2
            disk_image[bam1_offset + 2] = ord('D')
            disk_image[bam1_offset + 3] = 0
            disk_image[bam1_offset + 4] = disk_id[0]
            disk_image[bam1_offset + 5] = disk_id[1]
            disk_image[bam1_offset + 6] = ord('D')
            disk_image[bam1_offset + 7] = 0

            bam2_offset = self._sector_offset(self._geometry.directory_track, 2)
            disk_image[bam2_offset + 0] = 0
            disk_image[bam2_offset + 1] = 0xFF
            disk_image[bam2_offset + 2] = ord('D')
            disk_image[bam2_offset + 3] = 0
            disk_image[bam2_offset + 4] = disk_id[0]
            disk_image[bam2_offset + 5] = disk_id[1]
            disk_image[bam2_offset + 6] = ord('D')
            disk_image[bam2_offset + 7] = 0

    def _locate_bam_entry(self, track: int) -> Tuple[int, int, int]:
        meta_track = self._geometry.directory_track
        if self._geometry.disk_format == DiskFormat.D64:
            return (meta_track, 0, 4 + (track - 1) * 4)

        if track <= 40:
            return (meta_track, 1, 16 + (track - 1) * 6)
        else:
            return (meta_track, 2, 16 + (track - 41) * 6)

    def _is_sector_free(self, disk_image: bytes, track: int, sector: int) -> bool:
        bam_track, bam_sector, byte_offset = self._locate_bam_entry(track)
        bitmap_start = self._sector_offset(bam_track, bam_sector) + byte_offset + 1
        byte_index = sector // 8
        bit_index = sector % 8
        return (disk_image[bitmap_start + byte_index] & (1 << bit_index)) != 0

    def _set_sector_free(self, disk_image: bytearray, track: int, sector: int, free: bool):
        bam_track, bam_sector, byte_offset = self._locate_bam_entry(track)
        sector_offset = self._sector_offset(bam_track, bam_sector)
        bitmap_start = sector_offset + byte_offset + 1
        byte_index = sector // 8
        bit_index = sector % 8

        is_currently_free = (disk_image[bitmap_start + byte_index] & (1 << bit_index)) != 0
        if is_currently_free == free:
            return

        if free:
            disk_image[bitmap_start + byte_index] |= (1 << bit_index) & 0xFF
        else:
            disk_image[bitmap_start + byte_index] &= (~(1 << bit_index)) & 0xFF

        free_count_offset = sector_offset + byte_offset
        disk_image[free_count_offset] = (disk_image[free_count_offset] + (1 if free else -1)) & 0xFF

    def _encode_name(self, name: str, length: int) -> bytes:
        bytes_out = bytearray(length)
        for i in range(length):
            bytes_out[i] = 0xA0

        upper = name.upper()
        count = min(len(upper), length)
        for i in range(count):
            c = upper[i]
            b = ord(c)
            bytes_out[i] = b if 0x20 <= b <= 0x5F else ord('?')

        return bytes(bytes_out)
