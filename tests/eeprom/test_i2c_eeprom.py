from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from pytest_mock.plugin import MockerFixture

from pyeeprom.common import I2CEEPROMPage, OffsetLength, Region
from pyeeprom.eeprom.i2c_eeprom import I2CEEPROM, Transport


@pytest.fixture
def mock_transport(mocker: MockerFixture) -> MagicMock:
    return mocker.MagicMock(Transport)


@dataclass
class MockI2CEEPROM(I2CEEPROM):
    num_offsets: int = 1024
    page_size: int = 16
    offset_length: OffsetLength = OffsetLength.ONE_BYTE
    write_cycle_delay_ms: float = 10
    num_blocks: int = 1


@pytest.fixture
def i2c_eeprom(mock_transport: MagicMock) -> I2CEEPROM:
    return MockI2CEEPROM(address=0x50, i2c_transport=mock_transport)


def test_post_init_conversion(i2c_eeprom: I2CEEPROM) -> None:
    assert i2c_eeprom.write_cycle_delay_ms == 0.01  # 10 ms -> 0.01 s


def test_num_pages_and_pages_per_block(i2c_eeprom: I2CEEPROM) -> None:
    i2c_eeprom.num_offsets = 128
    assert i2c_eeprom.num_pages == 128 // 16
    assert i2c_eeprom.pages_per_block == (128 // 16) // 1


def test_adjust_device_address(i2c_eeprom: I2CEEPROM) -> None:
    assert i2c_eeprom.adjust_device_address(10) == 0x50


@pytest.mark.parametrize(
    "offset,length,expected_num_pages,num_offsets",
    [
        pytest.param(0, 16, 1, 64),
        pytest.param(0, 32, 2, 64),
        pytest.param(8, 16, 2, 64),
        pytest.param(0, 64, 4, 64),
        pytest.param(0, 128, None, 64),  # should raise ValueError
    ],
)
def test_calculate_num_pages_parameterized(
    i2c_eeprom: I2CEEPROM, offset: int, length: int, expected_num_pages: int, num_offsets: int
) -> None:
    i2c_eeprom.num_offsets = num_offsets
    if expected_num_pages is None:
        with pytest.raises(ValueError, match=r"Attempting to read or write to more than \d+ pages is not allowed!"):
            i2c_eeprom._calculate_num_pages(offset, length)

    else:
        assert i2c_eeprom._calculate_num_pages(offset, length) == expected_num_pages


@pytest.mark.parametrize(
    "offset,length,page_size,expected_byte_count",
    [
        pytest.param(0, 10, 16, 10),
        pytest.param(10, 10, 16, 6),
        pytest.param(15, 10, 16, 1),
        pytest.param(0, 16, 16, 16),
        pytest.param(16, 5, 16, 5),
    ],
)
def test_adjust_byte_count_parameterized(
    offset: int, length: int, page_size: int, expected_byte_count: int, mock_transport: MagicMock
) -> None:
    eeprom = I2CEEPROM(
        num_offsets=1024,
        address=0x50,
        i2c_transport=mock_transport,
        page_size=page_size,
        offset_length=OffsetLength.ONE_BYTE,
        write_cycle_delay_ms=10,
        num_blocks=1,
    )
    assert eeprom.adjust_byte_count(offset, length) == expected_byte_count


@pytest.mark.parametrize(
    "offset,num_offsets,num_blocks,expected_recalc",
    [
        pytest.param(0, 64, 1, 0),
        pytest.param(63, 64, 1, 63),
        pytest.param(64, 128, 2, 0),
        pytest.param(70, 128, 2, 6),
        pytest.param(127, 128, 2, 63),
        pytest.param(5, 128, 4, 5),
        pytest.param(35, 128, 4, 3),
    ],
)
def test_recalculate_offset_parameterized(
    offset: int, num_offsets: int, num_blocks: int, expected_recalc: int, mock_transport: MagicMock
) -> None:
    eeprom = I2CEEPROM(
        num_offsets=1024,
        address=0x50,
        i2c_transport=mock_transport,
        page_size=16,
        offset_length=OffsetLength.ONE_BYTE,
        write_cycle_delay_ms=10,
        num_blocks=num_blocks,
    )
    eeprom.num_offsets = num_offsets
    assert eeprom.recalculate_offset(offset) == expected_recalc


@pytest.mark.parametrize(
    "offset,num_blocks,address,expected_address",
    [
        pytest.param(0, 1, 0x50, 0x50),
        pytest.param(16, 1, 0x50, 0x50),
        pytest.param(0, 2, 0x50, 0x50),
        pytest.param(32, 2, 0x50, 0x50),
    ],
)
def test_adjust_device_address_parameterized(
    offset: int, num_blocks: int, address: int, expected_address: int, mock_transport: MagicMock
) -> None:
    eeprom = I2CEEPROM(
        num_offsets=1024,
        address=address,
        i2c_transport=mock_transport,
        page_size=16,
        offset_length=OffsetLength.ONE_BYTE,
        write_cycle_delay_ms=10,
        num_blocks=num_blocks,
    )
    # Base class always returns base address
    assert eeprom.adjust_device_address(offset) == expected_address


def test_write_calls_transport(mocker: MockerFixture, i2c_eeprom: I2CEEPROM) -> None:
    i2c_eeprom.num_offsets = 32
    region = Region(offset=0, length=20)
    data = bytes(range(20))

    mocker.patch("pyeeprom.eeprom.i2c_eeprom.time.sleep")
    mocker.patch.object(i2c_eeprom.i2c_transport, "write", new_callable=MagicMock)
    i2c_eeprom._write(region, data)

    total_bytes_written = sum(call_args[0][1].__len__() for call_args in i2c_eeprom.i2c_transport.write.call_args_list)
    assert total_bytes_written == 20


def test_read_calls_transport(mocker: MockerFixture, i2c_eeprom: I2CEEPROM) -> None:
    i2c_eeprom.num_offsets = 32
    region = Region(offset=0, length=20)

    def mock_read(page: I2CEEPROMPage) -> bytes:
        return bytes([page.offset + i for i in range(page.byte_count)])

    mocker.patch.object(i2c_eeprom.i2c_transport, "read", new_callable=MagicMock, side_effect=mock_read)
    result = i2c_eeprom._read(region)
    assert len(result) == 20
    assert result[0] == 0


def test_write_and_read_consistency(mocker: MockerFixture, i2c_eeprom: I2CEEPROM) -> None:
    i2c_eeprom.num_offsets = 32
    region = Region(offset=0, length=16)
    data = bytes(range(16))
    memory = {}

    def mock_write(page: I2CEEPROMPage, page_data: bytes) -> None:
        memory[page.offset] = page_data

    def mock_read(page: I2CEEPROMPage) -> bytes:
        return memory[page.offset]

    mocker.patch("pyeeprom.eeprom.i2c_eeprom.time.sleep")
    mocker.patch.object(i2c_eeprom.i2c_transport, "write", new_callable=MagicMock, side_effect=mock_write)
    mocker.patch.object(i2c_eeprom.i2c_transport, "read", new_callable=MagicMock, side_effect=mock_read)

    i2c_eeprom._write(region, data)
    read_back = i2c_eeprom._read(region)
    assert read_back == data
