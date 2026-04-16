import atexit
from collections.abc import Sequence
from dataclasses import dataclass

from smbus3 import I2cFunc, SMBus, i2c_msg

from pyeeprom.common import I2CEEPROMPage, OffsetLength


@dataclass
class SMBusTransport:
    """Transport layer for communicating with an I2C EEPROM device over SMBus.

    This class abstracts different read/write strategies depending on:
        - The EEPROM's offset length (1-byte or 2-byte addressing)
        - The capabilities of the underlying SMBus implementation

    It automatically selects the most efficient available method.

    Attributes:
        bus (SMBus): smbus3.SMBus object
    """

    bus: SMBus

    def __post_init__(self) -> None:
        atexit.register(self._close)

    def _write_byte_data(self, page: I2CEEPROMPage, data: Sequence[int]) -> None:
        """Write data using SMBus byte data transactions.

        Each byte is written individually to consecutive registers.

        Args:
            page (I2CEEPROMPage): EEPROM page descriptor (address, offset, etc.)
            data (Sequence[int]): Sequence of byte values to write

        Returns:
            None
        """

        for register, value in enumerate(data, start=page.offset):
            # Write one byte at a time to incrementing register addresses
            self.bus.write_byte_data(i2c_addr=page.i2c_address, register=register, value=value)

    def _write_word_data(self, page: I2CEEPROMPage, data: Sequence[int]) -> None:
        """Write data using SMBus word data transactions.

        This is used for EEPROMs with 2-byte internal addressing,
        where part of the address is encoded in the register and part
        in the value.

        Args:
            page (I2CEEPROMPage): EEPROM page descriptor (address, offset, etc.)
            data (Sequence[int]): Sequence of byte values to write

        Returns:
            None
        """

        for register, value in enumerate(data, start=page.offset):
            self.bus.write_word_data(
                i2c_addr=page.i2c_address,
                register=((register >> 8) & 0xFF),  # Send MSB of EEPROM's internal offset first
                value=((value << 8) | (register & 0xFF)),  # Combine LSB of EEPROM's internal offset with byte
            )

    def _page_write(self, page: I2CEEPROMPage, data: Sequence[int]) -> None:
        """Perform a page write using raw I2C block transaction.

        This is the most efficient method when supported, allowing
        multiple bytes to be written in a single operation.

        Args:
            page (I2CEEPROMPage): EEPROM page descriptor (address, offset, etc.)
            data (Sequence[int]): Sequence of byte values to write

        Returns:
            None
        """
        # Default to 1-byte offset
        internal_offset: list[int] = [page.offset & 0xFF]

        # If EEPROM uses 2-byte addressing, split into MSB and LSB
        if page.offset_length is OffsetLength.TWO_BYTE:
            msb, lsb = ((page.offset >> 8) & 0xFF), page.offset & 0xFF
            internal_offset = [msb, lsb]

        write_message = i2c_msg.write(page.i2c_address, internal_offset + list(data))
        self.bus.i2c_rdwr(write_message)

    def write(self, page: I2CEEPROMPage, data: Sequence[int]) -> None:
        """Write data to the EEPROM using the best available method.

        Strategy:
            1. Prefer block/page write if supported
            2. Fall back to byte or word writes depending on offset size

        Args:
            page (I2CEEPROMPage): EEPROM page descriptor (address, offset, etc.)
            data (Sequence[int]): Sequence of byte values to write

        Returns:
            None

        Raises:
            RuntimeError: If offset length is unsupported
        """
        if page.offset_length not in {OffsetLength.ONE_BYTE, OffsetLength.TWO_BYTE}:
            raise RuntimeError(f"No write operation available for offset length: {page.offset_length.name}")

        # Prefer block write if supported by the bus
        if self.bus.funcs & I2cFunc.SMBUS_WRITE_I2C_BLOCK:
            return self._page_write(page, data)

        if page.offset_length is OffsetLength.ONE_BYTE:
            return self._write_byte_data(page, data)

        elif page.offset_length is OffsetLength.TWO_BYTE:
            return self._write_word_data(page, data)

    def _read_byte_data(self, page: I2CEEPROMPage) -> bytes:
        """Read data using SMBus byte operations (1-byte offset).

        Args:
            page (I2CEEPROMPage): EEPROM page descriptor (address, offset, etc.)

        Returns:
            bytes: Bytes read from EEPROM
        """
        # Set the EEPROM's internal address pointer
        self.bus.write_byte(page.i2c_address, page.offset)

        data: bytes = b""
        for _ in range(page.byte_count):
            # Read one byte at a time
            value = self.bus.read_byte(page.i2c_address)
            data += value.to_bytes()

        return data

    def _read_word_data(self, page: I2CEEPROMPage) -> bytes:
        """Read data using SMBus word-style addressing (2-byte offset).

        Args:
            page (I2CEEPROMPage): EEPROM page descriptor (address, offset, etc.)

        Returns:
            bytes: Bytes read from EEPROM
        """
        msb, lsb = ((page.offset >> 8) & 0xFF), page.offset & 0xFF
        self.bus.write_byte_data(page.i2c_address, register=msb, value=lsb)

        data: bytes = b""
        for _ in range(page.byte_count):
            value = self.bus.read_byte(page.i2c_address)
            data += value.to_bytes()

        return data

    def _page_read(self, page: I2CEEPROMPage) -> bytes:
        """
        Perform a block read using raw I2C transactions.

        This is the most efficient read method when supported.

        Args:
            page (I2CEEPROMPage): EEPROM page descriptor (address, offset, etc.)

        Returns:
            bytes: Bytes read from EEPROM
        """
        # Default to 1-byte offset
        internal_offset: list[int] = [page.offset & 0xFF]

        # If EEPROM uses 2-byte addressing, split into MSB and LSB
        if page.offset_length is OffsetLength.TWO_BYTE:
            msb, lsb = ((page.offset >> 8) & 0xFF), page.offset & 0xFF
            internal_offset = [msb, lsb]

        # First write the offset, then read the data
        write_message = i2c_msg.write(page.i2c_address, internal_offset)
        read_message = i2c_msg.read(page.i2c_address, page.byte_count)
        self.bus.i2c_rdwr(write_message, read_message)

        return bytes(read_message)

    def read(self, page: I2CEEPROMPage) -> bytes:
        """
        Read data from the EEPROM using the best available method.

        Strategy:
            1. Prefer block/page read if supported
            2. Fall back to byte or word reads depending on offset size

        Args:
            page (I2CEEPROMPage): EEPROM page descriptor (address, offset, etc.)

        Returns:
            bytes: Bytes read from EEPROM

        Raises:
            RuntimeError: If offset length is unsupported
        """
        if page.offset_length not in {OffsetLength.ONE_BYTE, OffsetLength.TWO_BYTE}:
            raise RuntimeError(f"No read operation available for offset length: {page.offset_length.name}")

        # Prefer block read if supported by the bus
        if self.bus.funcs & I2cFunc.SMBUS_READ_I2C_BLOCK:
            return self._page_read(page)

        if page.offset_length is OffsetLength.ONE_BYTE:
            return self._read_byte_data(page)

        elif page.offset_length is OffsetLength.TWO_BYTE:
            return self._read_word_data(page)

    def _close(self) -> None:
        """Close the underlying SMBus connection.

        This is automatically called at program exit via atexit.

        Returns:
            None
        """
        self.bus.close()
