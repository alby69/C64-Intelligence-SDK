import pytest
from readycode_py.diskimage import DiskImage, DiskGeometry, C64UFileKind, DiskFormat
from readycode_py.tokenizer import PrgConverter

BOTH_FORMATS = [
    DiskGeometry.D64,
    DiskGeometry.D81
]

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_create_blank_image_has_exact_standard_size(geometry):
    image = DiskImage(geometry).create_blank_image("TEST")
    assert len(image) == geometry.standard_image_size

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_create_blank_image_has_no_directory_entries(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    assert len(disk.read_directory(image)) == 0

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_add_entry_single_sector_content_round_trips_exactly(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    content = b"HELLO WORLD"

    image = disk.add_entry(image, "HELLO", C64UFileKind.Prg, content)
    entries = disk.read_directory(image)
    assert len(entries) == 1
    entry = entries[0]

    assert entry.name == "HELLO"
    assert entry.content == content

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_add_entry_multi_sector_content_round_trips_exactly(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    content = bytearray(600)
    for i in range(len(content)):
        content[i] = i % 251
    content = bytes(content)

    image = disk.add_entry(image, "BIGFILE", C64UFileKind.Prg, content)
    entries = disk.read_directory(image)
    assert len(entries) == 1
    entry = entries[0]

    assert entry.content == content

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_add_entry_exact_sector_multiple_content_round_trips_exactly(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    content = bytes(range(254))

    image = disk.add_entry(image, "EXACT", C64UFileKind.Prg, content)
    entries = disk.read_directory(image)
    assert len(entries) == 1
    entry = entries[0]

    assert entry.content == content

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_add_entry_empty_content_round_trips_as_zero_bytes(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")

    image = disk.add_entry(image, "EMPTY", C64UFileKind.Prg, b"")
    entries = disk.read_directory(image)
    assert len(entries) == 1
    entry = entries[0]

    assert entry.content == b""

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_add_entry_multiple_files_all_round_trip_independently(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")

    image = disk.add_entry(image, "FIRST", C64UFileKind.Prg, b"AAA")
    image = disk.add_entry(image, "SECOND", C64UFileKind.Prg, b"BBBBB")

    entries = disk.read_directory(image)
    assert len(entries) == 2

    first = next(e for e in entries if e.name == "FIRST")
    second = next(e for e in entries if e.name == "SECOND")

    assert first.content == b"AAA"
    assert second.content == b"BBBBB"

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_add_entry_does_not_mutate_the_input_array(geometry):
    disk = DiskImage(geometry)
    original = disk.create_blank_image("TEST")
    original_copy = bytes(original)

    disk.add_entry(original, "HELLO", C64UFileKind.Prg, b"\x01\x02\x03")
    assert original == original_copy

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_add_entry_more_than_eight_files_extends_directory_chain(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")

    for i in range(10):
        image = disk.add_entry(image, f"F{i}", C64UFileKind.Prg, f"FILE{i}".encode('ascii'))

    entries = disk.read_directory(image)
    assert len(entries) == 10
    for i in range(10):
        entry = next(e for e in entries if e.name == f"F{i}")
        assert entry.content == f"FILE{i}".encode('ascii')

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_add_entry_tokenized_basic_content_is_classified_as_prg(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    basic = PrgConverter().convert_to_prg("10 PRINT \"HI\"")

    image = disk.add_entry(image, "BAS", C64UFileKind.Prg, basic)
    entries = disk.read_directory(image)
    assert len(entries) == 1
    assert entries[0].kind == C64UFileKind.Prg

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_add_entry_non_basic_content_is_classified_as_ml(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    machine_code = bytes([0x01, 0x08, 0xA9, 0x00, 0x60])

    image = disk.add_entry(image, "ML", C64UFileKind.Prg, machine_code)
    entries = disk.read_directory(image)
    assert len(entries) == 1
    assert entries[0].kind == C64UFileKind.Ml

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_rename_entry_old_name_gone_new_name_present(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    image = disk.add_entry(image, "OLDNAME", C64UFileKind.Prg, b"\x01\x02\x03")

    image = disk.rename_entry(image, "OLDNAME", "NEWNAME")
    entries = disk.read_directory(image)

    assert not any(e.name == "OLDNAME" for e in entries)
    assert any(e.name == "NEWNAME" for e in entries)

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_rename_entry_preserves_content(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    content = b"UNCHANGED"
    image = disk.add_entry(image, "OLDNAME", C64UFileKind.Prg, content)

    image = disk.rename_entry(image, "OLDNAME", "NEWNAME")
    entries = disk.read_directory(image)
    assert len(entries) == 1
    assert entries[0].content == content

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_rename_entry_missing_name_throws(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    with pytest.raises(ValueError):
        disk.rename_entry(image, "NOSUCH", "NEW")

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_replace_entry_updates_content_under_same_name(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    image = disk.add_entry(image, "FILE", C64UFileKind.Prg, b"\x01\x02\x03")

    image = disk.replace_entry(image, "FILE", b"\x09\x09\x09\x09")
    entries = disk.read_directory(image)
    assert len(entries) == 1
    assert entries[0].name == "FILE"
    assert entries[0].content == b"\x09\x09\x09\x09"

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_replace_entry_missing_name_throws(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    with pytest.raises(ValueError):
        disk.replace_entry(image, "NOSUCH", b"\x01")

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_delete_entry_removes_entry_and_frees_its_sectors(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    image = disk.add_entry(image, "FILE", C64UFileKind.Prg, bytes(600))
    free_before = len(disk.get_free_sectors(image))

    image = disk.delete_entry(image, "FILE")

    assert len(disk.read_directory(image)) == 0
    assert len(disk.get_free_sectors(image)) > free_before

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_delete_entry_leaves_other_entries_intact(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    image = disk.add_entry(image, "KEEP", C64UFileKind.Prg, b"KEEPME")
    image = disk.add_entry(image, "GONE", C64UFileKind.Prg, b"BYE")

    image = disk.delete_entry(image, "GONE")
    entries = disk.read_directory(image)
    assert len(entries) == 1
    assert entries[0].name == "KEEP"
    assert entries[0].content == b"KEEPME"

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_delete_entry_missing_name_throws(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    with pytest.raises(ValueError):
        disk.delete_entry(image, "NOSUCH")

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_get_free_sectors_decreases_as_files_are_added(geometry):
    disk = DiskImage(geometry)
    blank = disk.create_blank_image("TEST")
    free_blank = len(disk.get_free_sectors(blank))

    with_file = disk.add_entry(blank, "FILE", C64UFileKind.Prg, bytes(600))
    free_after = len(disk.get_free_sectors(with_file))

    assert free_after < free_blank

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_get_free_sectors_never_includes_reserved_header_or_directory_sectors(geometry):
    disk = DiskImage(geometry)
    image = disk.create_blank_image("TEST")
    free = disk.get_free_sectors(image)

    assert (geometry.directory_track, 0) not in free
    assert (geometry.directory_track, geometry.directory_sector) not in free

@pytest.mark.parametrize("geometry", BOTH_FORMATS)
def test_read_directory_wrong_size_throws(geometry):
    disk = DiskImage(geometry)
    with pytest.raises(ValueError):
        disk.read_directory(b'\x00' * 100)

def test_for_kind_d64_uses_d64_geometry():
    image = DiskImage.for_kind(C64UFileKind.D64).create_blank_image("TEST")
    assert len(image) == DiskGeometry.D64.standard_image_size

def test_for_kind_d81_uses_d81_geometry():
    image = DiskImage.for_kind(C64UFileKind.D81).create_blank_image("TEST")
    assert len(image) == DiskGeometry.D81.standard_image_size

def test_for_kind_non_disk_image_kind_throws():
    with pytest.raises(ValueError):
        DiskImage.for_kind(C64UFileKind.Prg)
