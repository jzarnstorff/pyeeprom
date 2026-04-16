from unittest.mock import MagicMock, call, patch

import pytest

from pyeeprom.common.eeprom_page import I2CEEPROMPage, OffsetLength
from pyeeprom.transports.smbus_transport import I2cFunc, SMBusTransport


class DummyPage:
    def __init__(self, i2c_address: int, offset: int, offset_length: OffsetLength, byte_count: int = 0):
        self.i2c_address = i2c_address
        self.offset = offset
        self.offset_length = offset_length
        self.byte_count = byte_count


@pytest.fixture
def mock_bus() -> MagicMock:
    bus = MagicMock()
    bus.funcs = 0
    return bus


@pytest.fixture
def transport(mock_bus: MagicMock) -> SMBusTransport:
    return SMBusTransport(bus=mock_bus)


@pytest.fixture
def page_one_byte() -> I2CEEPROMPage:
    return I2CEEPROMPage(i2c_address=0x50, offset=0x10, offset_length=OffsetLength.ONE_BYTE, byte_count=4)


@pytest.fixture
def page_two_byte() -> I2CEEPROMPage:
    return I2CEEPROMPage(i2c_address=0x50, offset=0x123, offset_length=OffsetLength.TWO_BYTE, byte_count=4)


def test_write_byte_data_called_for_one_byte_offset(transport: SMBusTransport, mock_bus: MagicMock) -> None:
    page = DummyPage(0x50, 0x10, OffsetLength.ONE_BYTE)
    data = [1, 2, 3]

    transport.write(page, data)

    expected_calls = [call(i2c_addr=0x50, register=0x10 + i, value=v) for i, v in enumerate(data)]
    mock_bus.write_byte_data.assert_has_calls(expected_calls)


def test_write_word_data_called_for_two_byte_offset(transport: SMBusTransport, mock_bus: MagicMock) -> None:
    page = DummyPage(0x50, 0x1234, OffsetLength.TWO_BYTE)
    data = [0xAA]

    transport.write(page, data)

    register = (0x1234 >> 8) & 0xFF
    value = (0xAA << 8) | (0x1234 & 0xFF)

    mock_bus.write_word_data.assert_called_once_with(
        i2c_addr=0x50,
        register=register,
        value=value,
    )


def test_write_uses_page_write_when_block_supported(transport: SMBusTransport, mock_bus: MagicMock) -> None:
    page = DummyPage(0x50, 0x10, OffsetLength.ONE_BYTE)
    data = [1, 2]

    mock_bus.funcs = I2cFunc.SMBUS_WRITE_I2C_BLOCK

    with patch.object(transport, "_page_write") as mock_page_write:
        transport.write(page, data)
        mock_page_write.assert_called_once_with(page, data)


def test_write_invalid_offset_length_raises(transport: SMBusTransport) -> None:
    class FakeOffset:
        name = "INVALID"

    page = DummyPage(0x50, 0x00, FakeOffset())

    with pytest.raises(RuntimeError, match="No write operation available for offset length"):
        transport.write(page, [1])


def test_read_byte_data(transport: SMBusTransport, mock_bus: MagicMock) -> None:
    page = DummyPage(0x50, 0x10, OffsetLength.ONE_BYTE, byte_count=3)

    mock_bus.read_byte.side_effect = [1, 2, 3]

    result = transport.read(page)

    mock_bus.write_byte.assert_called_once_with(0x50, 0x10)
    assert result == bytes([1, 2, 3])


def test_read_word_data(transport: SMBusTransport, mock_bus: MagicMock) -> None:
    page = DummyPage(0x50, 0x1234, OffsetLength.TWO_BYTE, byte_count=2)

    mock_bus.read_byte.side_effect = [0xAA, 0xBB]

    result = transport.read(page)

    mock_bus.write_byte_data.assert_called_once_with(
        0x50,
        register=(0x1234 >> 8) & 0xFF,
        value=0x1234 & 0xFF,
    )
    assert result == bytes([0xAA, 0xBB])


def test_read_uses_page_read_when_block_supported(transport: SMBusTransport, mock_bus: MagicMock) -> None:
    page = DummyPage(0x50, 0x10, OffsetLength.ONE_BYTE, byte_count=2)
    mock_bus.funcs = I2cFunc.SMBUS_READ_I2C_BLOCK

    with patch.object(transport, "_page_read", return_value=b"\x01\x02") as mock_page_read:
        result = transport.read(page)

    mock_page_read.assert_called_once_with(page)
    assert result == b"\x01\x02"


def test_read_invalid_offset_length_raises(transport: SMBusTransport) -> None:
    class FakeOffset:
        name = "INVALID"

    page = DummyPage(0x50, 0x00, FakeOffset())

    with pytest.raises(RuntimeError, match="No read operation available for offset length"):
        transport.read(page)


def test_page_write_one_byte(transport: SMBusTransport, mock_bus: MagicMock, page_one_byte: I2CEEPROMPage) -> None:
    data = [1, 2, 3, 4]
    mock_write_msg = MagicMock()
    with patch("pyeeprom.transports.smbus_transport.i2c_msg.write", return_value=mock_write_msg) as mock_i2c_write:
        transport._page_write(page_one_byte, data)

    # Verify i2c_msg.write called with correct address and data
    mock_i2c_write.assert_called_once()
    addr, buf = mock_i2c_write.call_args[0]
    assert addr == page_one_byte.i2c_address
    # First byte is offset, followed by data
    assert list(buf) == [page_one_byte.offset] + data

    # Verify i2c_rdwr called with the write message
    mock_bus.i2c_rdwr.assert_called_once_with(mock_write_msg)


def test_page_write_two_byte(transport: SMBusTransport, mock_bus: MagicMock, page_two_byte: I2CEEPROMPage) -> None:
    data = [0xAA, 0xBB]
    mock_write_msg = MagicMock()
    with patch("pyeeprom.transports.smbus_transport.i2c_msg.write", return_value=mock_write_msg) as mock_i2c_write:
        transport._page_write(page_two_byte, data)

    mock_i2c_write.assert_called_once()
    addr, buf = mock_i2c_write.call_args[0]
    assert addr == page_two_byte.i2c_address
    # Two-byte offset: [MSB, LSB] + data
    msb, lsb = (page_two_byte.offset >> 8) & 0xFF, page_two_byte.offset & 0xFF
    assert list(buf) == [msb, lsb] + data
    mock_bus.i2c_rdwr.assert_called_once_with(mock_write_msg)


def test_page_read_one_byte(transport: SMBusTransport, mock_bus: MagicMock, page_one_byte: I2CEEPROMPage) -> None:
    mock_read_msg = MagicMock()
    mock_write_msg = MagicMock()

    expected_bytes = bytes([10, 20, 30, 40])

    with (
        patch("pyeeprom.transports.smbus_transport.i2c_msg.write", return_value=mock_write_msg) as mock_i2c_write,
        patch("pyeeprom.transports.smbus_transport.i2c_msg.read", return_value=expected_bytes) as mock_i2c_read,
    ):

        result = transport._page_read(page_one_byte)

    # Verify i2c_msg.write called with correct internal offset
    mock_i2c_write.assert_called_once()
    addr, buf = mock_i2c_write.call_args[0]
    assert addr == page_one_byte.i2c_address
    assert list(buf) == [page_one_byte.offset]

    # Verify i2c_msg.read called with correct length
    # mock_i2c_read.assert_called_once_with(page_one_byte.i2c_address, page_one_byte.byte_count)

    # Verify i2c_rdwr called with write + read message
    # mock_bus.i2c_rdwr.assert_called_once_with(mock_write_msg, mock_read_msg)

    # Verify the returned bytes
    assert result == expected_bytes


def test_page_read_two_byte(transport: SMBusTransport, mock_bus: MagicMock, page_two_byte: I2CEEPROMPage) -> None:
    mock_read_msg = MagicMock()
    mock_write_msg = MagicMock()

    expected_bytes = bytes([0x01, 0x02, 0x03, 0x04])

    with (
        patch("pyeeprom.transports.smbus_transport.i2c_msg.write", return_value=mock_write_msg) as mock_i2c_write,
        patch("pyeeprom.transports.smbus_transport.i2c_msg.read", return_value=expected_bytes) as mock_i2c_read,
    ):

        result = transport._page_read(page_two_byte)

    # Verify two-byte internal offset
    msb, lsb = (page_two_byte.offset >> 8) & 0xFF, page_two_byte.offset & 0xFF
    addr, buf = mock_i2c_write.call_args[0]
    assert list(buf) == [msb, lsb]

    # mock_i2c_read.assert_called_once_with(page_two_byte.i2c_address, page_two_byte.byte_count)
    # mock_bus.i2c_rdwr.assert_called_once_with(mock_write_msg, mock_read_msg)
    assert result == expected_bytes


def test_close_calls_bus_close(transport: SMBusTransport, mock_bus: MagicMock) -> None:
    transport._close()
    mock_bus.close.assert_called_once()
