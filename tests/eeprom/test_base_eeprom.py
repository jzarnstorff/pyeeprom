from dataclasses import dataclass

import pytest
from pytest_mock.plugin import MockerFixture

from pyeeprom.common import Region
from pyeeprom.eeprom import EEPROM


@dataclass
class FooEEPROM(EEPROM):
    num_offsets: int = 1024

    def _write(self, region: Region, data: bytes) -> None:
        return None

    def _read(self, region: Region) -> bytes:
        return b"\xff" * region.length


@pytest.fixture
def foo_eeprom() -> FooEEPROM:
    return FooEEPROM()


def test_base_eeprom_write_no_data(foo_eeprom: EEPROM) -> None:
    empty_data = b""
    region = Region(offset=0x00, length=foo_eeprom.num_offsets)

    with pytest.raises(RuntimeError, match="No data given for write operation"):
        foo_eeprom.write(region=region, data=empty_data)


def test_base_eeprom_write_outside_range(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    data = b"\xff"
    mocker.patch("pyeeprom.common.region.validate_constraints")
    negative_region = Region(offset=-1, length=foo_eeprom.num_offsets)
    num_offsets_region = Region(offset=foo_eeprom.num_offsets, length=foo_eeprom.num_offsets)

    with pytest.raises(ValueError, match="Starting offset must be within range:"):
        foo_eeprom.write(region=negative_region, data=data)

    with pytest.raises(ValueError, match="Starting offset must be within range:"):
        foo_eeprom.write(region=num_offsets_region, data=data)


def test_base_eeprom_write_region_too_large(foo_eeprom: EEPROM) -> None:
    data = b"\xff"
    region = Region(offset=0x00, length=(foo_eeprom.num_offsets + 1))

    with pytest.raises(ValueError, match="Region is greater than total number of offsets"):
        foo_eeprom.write(region=region, data=data)


def test_base_eeprom_write_data_length_greater_than_region_length(foo_eeprom: EEPROM) -> None:
    data = b"\xff" * (foo_eeprom.num_offsets + 1)
    region = Region(offset=0x00, length=foo_eeprom.num_offsets)

    with pytest.raises(ValueError, match="Data too large to fit within specified region"):
        foo_eeprom.write(region=region, data=data)


def test_base_eeprom_write_data_length_less_than_region_length(foo_eeprom: EEPROM) -> None:
    data = b"\xff"
    region = Region(offset=0x00, length=foo_eeprom.num_offsets)
    foo_eeprom.write(region=region, data=data)


def test_base_eeprom_write_entire_eeprom(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    data = b"\xff" * foo_eeprom.num_offsets
    region = Region(offset=0x00, length=foo_eeprom.num_offsets)

    mocker.patch.object(foo_eeprom, "_write")
    foo_eeprom.write(region=region, data=data)
    foo_eeprom._write.assert_called_once_with(region, data)


def test_base_eeprom_write_partial_region(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    data = b"\xff"
    region = Region(offset=0x00, length=foo_eeprom.num_offsets)

    mocker.patch.object(foo_eeprom, "_write")
    foo_eeprom.write(region=region, data=data)
    foo_eeprom._write.assert_called_once_with(region, data)


def test_base_eeprom_read_outside_range(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    mocker.patch("pyeeprom.common.region.validate_constraints")
    negative_region = Region(offset=-1, length=foo_eeprom.num_offsets)
    num_offsets_region = Region(offset=foo_eeprom.num_offsets, length=foo_eeprom.num_offsets)

    with pytest.raises(ValueError, match="Starting offset must be within range:"):
        foo_eeprom.read(negative_region)

    with pytest.raises(ValueError, match="Starting offset must be within range:"):
        foo_eeprom.read(num_offsets_region)


def test_base_eeprom_read_region(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    region = Region(offset=0x00, length=foo_eeprom.num_offsets)

    mocker.patch.object(foo_eeprom, "_read")
    foo_eeprom.read(region)
    foo_eeprom._read.assert_called_once_with(region)


def test_base_eeprom_read_region_max_length(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    double_offsets = foo_eeprom.num_offsets * 2
    region = Region(offset=0x00, length=double_offsets)

    mocker.patch.object(foo_eeprom, "_read")
    foo_eeprom.read(region)
    foo_eeprom._read.assert_called_once_with(region)

    modified_region: Region = foo_eeprom._read.call_args.args[0]
    assert modified_region.length < double_offsets


def test_base_eeprom_erase(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    region = Region(offset=0x00, length=foo_eeprom.num_offsets)

    mocker.patch.object(foo_eeprom, "write")
    foo_eeprom.erase(region)
    foo_eeprom.write.assert_called_once_with(region=region, data=b"\xff" * region.length)


def test_base_eeprom_len(foo_eeprom: EEPROM) -> None:
    assert len(foo_eeprom) == foo_eeprom.num_offsets


def test_base_eeprom_getitem_index(foo_eeprom: EEPROM) -> None:
    assert len(foo_eeprom[0]) == 1


def test_base_eeprom_getitem_index_equal_num_offsets(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    mock_read = mocker.patch.object(foo_eeprom, "read")

    with pytest.raises(IndexError, match="Offset out of range"):
        foo_eeprom[foo_eeprom.num_offsets]

    mock_read.assert_not_called()


def test_base_eeprom_getitem_index_greater_than_num_offsets(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    mock_read = mocker.patch.object(foo_eeprom, "read")

    with pytest.raises(IndexError, match="Offset out of range"):
        foo_eeprom[foo_eeprom.num_offsets + 1]

    mock_read.assert_not_called()


def test_base_eeprom_getitem_index_is_negative(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    mock_read = mocker.patch.object(foo_eeprom, "read")

    with pytest.raises(IndexError, match="Offset out of range"):
        foo_eeprom[-1]

    mock_read.assert_not_called()


def test_base_eeprom_getitem_slice(foo_eeprom: EEPROM) -> None:
    assert len(foo_eeprom[:]) == foo_eeprom.num_offsets


def test_base_eeprom_getitem_slice_negative_stop(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.stop must be greater than both"):
        foo_eeprom[0:-1]


def test_base_eeprom_getitem_slice_stop_equals_start(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.stop must be greater than both"):
        foo_eeprom[0:0]


def test_base_eeprom_getitem_slice_stop_less_than_start(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.stop must be greater than both"):
        foo_eeprom[10:1]


def test_base_eeprom_getitem_slice_step(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    start = 0
    stop = 256  # Max byte value
    mocker.patch.object(foo_eeprom, "_read", return_value=bytes(range(stop)))
    contents = foo_eeprom[start:stop:2]
    assert all([value % 2 == 0 for value in contents])

    contents = foo_eeprom[start:stop:3]
    assert all([value % 3 == 0 for value in contents])


def test_base_eeprom_getitem_type_error(foo_eeprom: EEPROM) -> None:
    with pytest.raises(TypeError, match="Offset must be of types int or slice"):
        foo_eeprom[None]


def test_base_eeprom_delitem_index(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    offset = 0
    mock_erase = mocker.patch.object(foo_eeprom, "erase")
    del foo_eeprom[offset]

    mock_erase.assert_called_once()
    erase_region: Region = mock_erase.call_args.args[0]

    assert erase_region.offset == offset
    assert erase_region.length == 1


def test_base_eeprom_delitem_index_equal_num_offsets(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    mock_erase = mocker.patch.object(foo_eeprom, "erase")

    with pytest.raises(IndexError, match="Offset out of range"):
        del foo_eeprom[foo_eeprom.num_offsets]

    mock_erase.assert_not_called()


def test_base_eeprom_delitem_index_greater_than_num_offsets(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    mock_erase = mocker.patch.object(foo_eeprom, "erase")

    with pytest.raises(IndexError, match="Offset out of range"):
        del foo_eeprom[foo_eeprom.num_offsets + 1]

    mock_erase.assert_not_called()


def test_base_eeprom_delitem_index_is_negative(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    mock_erase = mocker.patch.object(foo_eeprom, "erase")

    with pytest.raises(IndexError, match="Offset out of range"):
        del foo_eeprom[-1]

    mock_erase.assert_not_called()


def test_base_eeprom_delitem_slice_step_not_available(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice stepping is not available"):
        del foo_eeprom[0 : foo_eeprom.num_offsets : 2]


def test_base_eeprom_delitem_slice_start_is_None(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.start cannot be None"):
        del foo_eeprom[: foo_eeprom.num_offsets]


def test_base_eeprom_delitem_slice_start_less_than_zero(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.start must be within range"):
        del foo_eeprom[-1 : foo_eeprom.num_offsets]


def test_base_eeprom_delitem_slice_start_equal_to_num_offsets(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.start must be within range"):
        del foo_eeprom[foo_eeprom.num_offsets : 1]


def test_base_eeprom_delitem_slice_start_greater_than_num_offsets(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.start must be within range"):
        del foo_eeprom[foo_eeprom.num_offsets + 1 : 1]


def test_base_eeprom_delitem_slice_negative_stop(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.stop must be greater than both"):
        del foo_eeprom[0:-1]


def test_base_eeprom_delitem_slice_stop_equals_start(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.stop must be greater than both"):
        del foo_eeprom[0:0]


def test_base_eeprom_delitem_slice_stop_less_than_start(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.stop must be greater than both"):
        del foo_eeprom[10:1]


def test_base_eeprom_delitem_slice(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    start = 100
    mock_erase = mocker.patch.object(foo_eeprom, "erase")
    del foo_eeprom[start : foo_eeprom.num_offsets]

    mock_erase.assert_called_once()
    erase_region: Region = mock_erase.call_args.args[0]

    assert erase_region.offset == start
    assert erase_region.length == (foo_eeprom.num_offsets - start)


def test_base_eeprom_del_type_error(foo_eeprom: EEPROM) -> None:
    with pytest.raises(TypeError, match="Offset must be of types int or slice"):
        del foo_eeprom[None]


def test_base_eeprom_setitem_index(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    offset = 0
    data = b"H"

    mock_write = mocker.patch.object(foo_eeprom, "write")
    foo_eeprom[offset] = data

    mock_write.assert_called_once()
    write_region: Region = mock_write.call_args.args[0]
    write_data: bytes = mock_write.call_args.args[1]

    assert write_region.offset == offset
    assert write_region.length == 1
    assert write_data == data


def test_base_eeprom_setitem_index_equal_num_offsets(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    mock_write = mocker.patch.object(foo_eeprom, "write")

    with pytest.raises(IndexError, match="Offset out of range"):
        foo_eeprom[foo_eeprom.num_offsets] = b"H"

    mock_write.assert_not_called()


def test_base_eeprom_setitem_index_greater_than_num_offsets(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    mock_write = mocker.patch.object(foo_eeprom, "write")

    with pytest.raises(IndexError, match="Offset out of range"):
        foo_eeprom[foo_eeprom.num_offsets + 1] = b"H"

    mock_write.assert_not_called()


def test_base_eeprom_setitem_index_is_negative(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    mock_write = mocker.patch.object(foo_eeprom, "write")

    with pytest.raises(IndexError, match="Offset out of range"):
        foo_eeprom[-1] = b"H"

    mock_write.assert_not_called()


def test_base_eeprom_setitem_data_too_large(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    data = b"Hello world"
    mock_write = mocker.patch.object(foo_eeprom, "write")

    with pytest.raises(ValueError, match=f"Cannot write {len(data)} bytes to offset"):
        foo_eeprom[0] = data

    mock_write.assert_not_called()


def test_base_eeprom_setitem_slice_step_not_available(foo_eeprom: EEPROM) -> None:
    data = b"Hello world"

    with pytest.raises(ValueError, match="Slice stepping is not available"):
        foo_eeprom[0:6:2] = data


def test_base_eeprom_setitem_slice_start_is_None(foo_eeprom: EEPROM) -> None:
    data = b"Hello world"

    with pytest.raises(ValueError, match="Both slice.start and slice.stop must be specified"):
        foo_eeprom[: len(data)] = data


def test_base_eeprom_setitem_slice_stop_is_None(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Both slice.start and slice.stop must be specified"):
        foo_eeprom[0:] = b"Hello world"


def test_base_eeprom_setitem_slice_start_less_than_zero(foo_eeprom: EEPROM) -> None:
    data = b"Hello world"

    with pytest.raises(ValueError, match="Slice.start must be within range"):
        foo_eeprom[-1 : foo_eeprom.num_offsets] = data


def test_base_eeprom_setitem_slice_start_equal_to_num_offsets(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.start must be within range"):
        foo_eeprom[foo_eeprom.num_offsets : 1] = b"H"


def test_base_eeprom_setitem_slice_start_greater_than_num_offsets(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.start must be within range"):
        foo_eeprom[foo_eeprom.num_offsets + 1 : 1] = b"H"


def test_base_eeprom_setitem_slice_negative_stop(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.stop must be within range"):
        foo_eeprom[0:-1] = b""


def test_base_eeprom_setitem_slice_stop_equals_start(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.stop must be within range"):
        foo_eeprom[0:0] = b""


def test_base_eeprom_setitem_slice_stop_less_than_start(foo_eeprom: EEPROM) -> None:
    with pytest.raises(ValueError, match="Slice.stop must be within range"):
        foo_eeprom[10:1] = b"H"


@pytest.mark.parametrize(
    "start,stop,data",
    [
        pytest.param(0, 1, b"Hello World"),
        pytest.param(0, 100, b"H"),
    ],
)
def test_base_eeprom_setitem_unequal_slice_and_data_length(
    start: int, stop: int, data: bytes, foo_eeprom: EEPROM
) -> None:
    length = stop - start
    with pytest.raises(ValueError, match=f"Length of data: {len(data)} doesn't match specified range: {length}"):
        foo_eeprom[start:stop] = data


def test_base_eeprom_setitem_slice(mocker: MockerFixture, foo_eeprom: EEPROM) -> None:
    start = 100
    data = b"Hello World"
    stop = start + len(data)
    mock_write = mocker.patch.object(foo_eeprom, "write")
    foo_eeprom[start:stop] = data

    mock_write.assert_called_once()
    write_region: Region = mock_write.call_args.args[0]
    write_data: bytes = mock_write.call_args.args[1]

    assert write_region.offset == start
    assert write_region.length == (stop - start)
    assert write_data == data


def test_base_eeprom_set_type_error(foo_eeprom: EEPROM) -> None:
    with pytest.raises(TypeError, match="Offset must be of types int or slice"):
        foo_eeprom[None] = b"H"
