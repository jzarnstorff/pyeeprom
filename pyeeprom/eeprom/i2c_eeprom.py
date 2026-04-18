import time
from dataclasses import dataclass
from typing import cast

from pyeeprom.common import I2CEEPROMPage, OffsetLength, Region
from pyeeprom.eeprom import EEPROM
from pyeeprom.transports import Transport


@dataclass(kw_only=True)
class I2CEEPROM(EEPROM):
    """Concrete EEPROM implementation using an I2C transport layer.

    This class handles EEPROM devices that are accessed over I2C,
    including logic for page-aligned reads/writes and multi-block
    (stacked device) configurations.

    Attributes:
        address (int): Base I2C address of the EEPROM.
        i2c_transport (Transport): Transport used for I2C communication.
        page_size (int): Size of a single EEPROM page in bytes.
        offset_length (OffsetLength): Number of bytes used for the internal address pointer.
        write_cycle_delay_ms (float): Delay required after each page write.
        num_blocks (int): Number of stacked EEPROMs (number of I2C addresses consumed).
    """

    address: int
    i2c_transport: Transport

    page_size: int
    offset_length: OffsetLength  # Number of bytes of the internal address pointer

    write_cycle_delay_ms: float
    num_blocks: int = 1  # Equivalent to the number of stacked EEPROMs (I2C addresses consumed)

    def __post_init__(self) -> None:
        self.write_cycle_delay_ms /= 1000  # Convert to milliseconds

    @property
    def num_pages(self) -> int:
        """Total number of pages in the EEPROM.

        Returns:
            int: Number of pages derived from total size and page size.
        """

        return self.num_offsets // self.page_size

    @property
    def pages_per_block(self) -> int:
        """Number of pages per EEPROM block.

        Useful for devices that internally segment memory across
        multiple I2C addresses.

        Returns:
            int: Pages per block.
        """

        return self.num_pages // self.num_blocks

    def adjust_device_address(self, offset: int) -> int:
        """Adjust the I2C device address based on the memory offset.

        Args:
            offset (int): EEPROM's array-like index desired to be accessed: [0,`num_offsets`)

        Returns:
            int: Calculated I2C address to use for this operation.

        Notes:
            - Default implementation assumes a single device.
            - Override for multi-block EEPROMs where offset
              crosses multi-address boundary.
        """

        return self.address

    def recalculate_offset(self, offset: int) -> int:
        """Recalculate offset relative to a specific EEPROM block.

        Args:
            offset (int): EEPROM's array-like index desired to be accessed: [0,`num_offsets`)

        Returns:
            int: Block-local offset.

        Notes:
            - Required for devices with multiple addressable blocks.
        """

        return offset % (self.num_offsets // self.num_blocks)

    def adjust_byte_count(self, offset: int, length: int) -> int:
        """Determine how many bytes can be read/written in the current page.

        Args:
            offset (int): EEPROM's array-like index desired to be accessed: [0,`num_offsets`)
            length (int): Remaining length of bytes to process.

        Returns:
            int: Number of bytes to process without crossing a page boundary.
        """

        return min(length, self.page_size - (offset % self.page_size))

    def _calculate_num_pages(self, starting_offset: int, length: int) -> int:
        """Calculate how many pages are required for an operation with a given length.

        Args:
            starting_offset (int): Starting EEPROM offset desired to be accessed: [0,`num_offsets`)
            length (int): Total number of bytes to process.

        Returns:
            int: Number of pages involved.

        Raises:
            ValueError: If operation exceeds total available pages.
        """

        start_page = starting_offset // self.page_size
        end_page = ((starting_offset + length) - 1) // self.page_size
        num_pages = end_page - start_page + 1

        if num_pages > self.num_pages:
            raise ValueError(f"Attempting to read or write to more than {self.num_pages} pages is not allowed!")

        return num_pages

    def _write(self, region: Region, data: bytes) -> None:
        """Perform a page-aware write operation over I2C.

        Splits the write into page-sized chunks and ensures that
        no write crosses a page boundary. Applies required write
        cycle delays between page writes.

        Args:
            region (Region): Target region.
            data (bytes): Data to write.
        """

        current_index = 0  # Tracks position within `data`
        length = len(data)
        offset = region.offset

        # Determine how many pages this write will span
        num_pages = self._calculate_num_pages(offset, length)

        for _ in range(num_pages):
            # Adjust address and offset for current block/page
            adjusted_i2c_address = self.adjust_device_address(offset)
            adjusted_offset = self.recalculate_offset(offset)

            # Determine how much we can write without crossing a page boundary
            byte_count = self.adjust_byte_count(offset, length)

            # Construct page descriptor for transport layer
            page = I2CEEPROMPage(
                offset=adjusted_offset,
                byte_count=byte_count,
                i2c_address=adjusted_i2c_address,
                offset_length=self.offset_length,
            )

            # Perform the actual write
            self.i2c_transport.write(page, data[current_index : current_index + byte_count])

            # EEPROMs require a delay after each page write cycle
            time.sleep(self.write_cycle_delay_ms)

            # Advance pointers for next iteration
            offset += byte_count
            current_index += byte_count
            length -= byte_count

        return None

    def _read(self, region: Region) -> bytes:
        """Perform a page-aware read operation over I2C.

        Splits the read into page-sized chunks as needed.

        Args:
            region (Region): Target region.

        Returns:
            bytes: Data read from EEPROM.
        """

        data: bytes = b""
        length = region.length
        offset = region.offset

        # Determine how many pages this read will span
        num_pages = self._calculate_num_pages(offset, length)

        for _ in range(num_pages):
            # Adjust address and offset for current block/page
            adjusted_i2c_address = self.adjust_device_address(offset)
            adjusted_offset = self.recalculate_offset(offset)

            # Determine how much we can read from this page
            byte_count = self.adjust_byte_count(offset, length)

            # Construct page descriptor for transport layer
            page = I2CEEPROMPage(
                offset=adjusted_offset,
                byte_count=byte_count,
                i2c_address=adjusted_i2c_address,
                offset_length=self.offset_length,
            )

            # Perform read and append result
            data += cast(bytes, self.i2c_transport.read(page))

            # Advance pointers
            offset += byte_count
            length -= byte_count

        return data
