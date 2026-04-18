from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from pyeeprom.common import Region


@dataclass(kw_only=True)
class EEPROM(ABC):
    """Abstract base class representing an EEPROM device.

    This class provides a high-level interface for reading, writing,
    and erasing data using logical regions. Concrete implementations
    must define the low-level `_read` and `_write` methods.

    Attributes:
        num_offsets (int): Total number of addressable offsets in the EEPROM.
        name (ClassVar[str | None]): Optional human-readable name of the EEPROM.
    """

    num_offsets: int
    name: ClassVar[str | None] = None

    @abstractmethod
    def _write(self, region: Region, data: bytes) -> None:
        """Low-level write implementation to be provided by subclasses.

        Args:
            region (Region): Target region to write to.
            data (bytes): Data to write.
        """

    def write(self, region: Region, data: bytes) -> None:
        """Validate and write data to a specified region of the EEPROM.

        Args:
            region (Region): Target region to write to.
            data (bytes): Data to write.

        Raises:
            RuntimeError: If no data is provided.
            ValueError: If the region is invalid or data does not fit.
        """

        # Ensure data is not empty
        if not data:
            raise RuntimeError("No data given for write operation")

        # Validate starting offset
        if not (0 <= region.offset < self.num_offsets):
            raise ValueError(f"Starting offset must be within range: [0, {self.num_offsets})")

        # Ensure region does not exceed EEPROM bounds
        if (region.offset + region.length) > self.num_offsets:
            raise ValueError(
                f"Region is greater than total number of offsets: ({region.offset=} + {region.length=}) > num_offsets={self.num_offsets}"
            )

        # Ensure data fits within the specified region
        if len(data) > (region.offset + region.length):
            raise ValueError(
                f"Data too large to fit within specified region: {len(data)=} > ({region.offset=} + {region.length=})"
            )

        self._write(region, data)

    @abstractmethod
    def _read(self, region: Region) -> bytes:
        """Low-level read implementation to be provided by subclasses.

        Args:
            region (Region): Region to read from.

        Returns:
            bytes: Data read from the EEPROM.
        """

    def read(self, region: Region) -> bytes:
        """Validate and read data from a specified region.

        Args:
            region (Region): Region to read from.

        Returns:
            bytes: Data read from the EEPROM.

        Raises:
            ValueError: If the region offset is invalid.
        """

        # Validate starting offset
        if not (0 <= region.offset < self.num_offsets):
            raise ValueError(f"Starting offset must be within range: [0, {self.num_offsets})")

        # Do not allow caller to attempt to read greater than `eeprom.num_offsets`
        region.length = min(region.length, self.num_offsets - region.offset)

        return self._read(region)

    def erase(self, region: Region) -> None:
        """Erase a region of the EEPROM by writing 0xFF bytes.

        Args:
            region (Region): Region to erase.
        """

        self.write(region=region, data=b"\xff" * region.length)

    def __len__(self) -> int:
        """Return the total size of the EEPROM.

        Returns:
            int: Number of addressable offsets.
        """

        return self.num_offsets

    def __getitem__(self, offset: int | slice) -> bytes:
        """Read data using index or slice notation.

        Args:
            offset (int | slice): Offset or slice to read.

        Returns:
            bytes: Data read from the EEPROM.

        Raises:
            IndexError: If offset is out of bounds.
            ValueError: If slice parameters are invalid.
            TypeError: If offset type is unsupported.
        """

        if isinstance(offset, int):

            # Single-byte read
            if (offset < 0) or (offset >= self.num_offsets):
                raise IndexError(f"Offset out of range: [0, {self.num_offsets})")

            region = Region(offset=offset, length=1)
            return self.read(region)

        elif isinstance(offset, slice):
            start = offset.start or 0
            stop = self.num_offsets if offset.stop is None else offset.stop

            # Validate slice bounds
            if (stop <= 0) or (stop <= start):
                raise ValueError(f"Slice.stop must be greater than both: {start} and 0")

            length = stop - start
            region = Region(offset=start, length=length)
            contents = self.read(region)

            # Handle optional slicing step
            step = 1
            if isinstance(offset.step, int):
                step = offset.step

            # Return full contents or stepped slice
            if step in {0, 1}:
                return contents
            return contents[::step]

        raise TypeError("Offset must be of types int or slice")

    def __setitem__(self, offset: int | slice, data: bytes) -> None:
        """Write data using index or slice notation.

        Args:
            offset (int | slice): Offset or slice to write to.
            data (bytes): Data to write.

        Raises:
            IndexError: If offset is out of bounds.
            ValueError: If slice parameters are invalid.
            TypeError: If offset type is unsupported.
        """

        # Single-byte write
        if isinstance(offset, int):
            if (offset < 0) or (offset >= self.num_offsets):
                raise IndexError(f"Offset out of range: [0, {self.num_offsets})")

            if len(data) > 1:
                raise ValueError(f"Cannot write {len(data)} bytes to offset")

            region = Region(offset=offset, length=1)
            return self.write(region, data)

        elif isinstance(offset, slice):
            start = offset.start
            stop = offset.stop

            # Disallow stepped writes
            if (offset.step is not None) and (offset.step != 1):
                raise ValueError("Slice stepping is not available")

            # Require explicit bounds
            if (start is None) or (stop is None):
                raise ValueError("Both slice.start and slice.stop must be specified")

            # Validate bounds
            if not (0 <= start < self.num_offsets):
                raise ValueError(f"Slice.start must be within range: [0, {self.num_offsets})")

            if (stop <= 0) or (stop <= start) or (stop > self.num_offsets):
                raise ValueError(f"Slice.stop must be within range: ({start}, {self.num_offsets}]")

            length = stop - start

            if len(data) != length:
                raise ValueError(f"Length of data: {len(data)} doesn't match specified range: {length}")

            region = Region(offset=start, length=length)
            return self.write(region, data)

        else:
            raise TypeError("Offset must be of types int or slice")

    def __delitem__(self, offset: int | slice) -> None:
        """
        Erase data using index or slice notation.

        Args:
            offset (int | slice): Offset or slice to erase.

        Raises:
            IndexError: If offset is out of bounds.
            ValueError: If slice parameters are invalid.
            TypeError: If offset type is unsupported.
        """

        if isinstance(offset, int):
            # Single-byte erase
            if (offset < 0) or (offset >= self.num_offsets):
                raise IndexError(f"Offset out of range: [0, {self.num_offsets})")

            region = Region(offset=offset, length=1)
            return self.erase(region)

        elif isinstance(offset, slice):
            start = offset.start
            stop = self.num_offsets if offset.stop is None else offset.stop

            # Disallow stepped erase
            if (offset.step is not None) and (offset.step != 1):
                raise ValueError("Slice stepping is not available")

            if start is None:
                raise ValueError("Slice.start cannot be None")

            # Validate bounds
            if not (0 <= start < self.num_offsets):
                raise ValueError(f"Slice.start must be within range: [0, {self.num_offsets})")

            if (stop <= 0) or (stop <= start):
                raise ValueError(f"Slice.stop must be greater than both: {start} and 0")

            length = stop - start
            region = Region(offset=start, length=length)
            return self.erase(region)

        else:
            raise TypeError("Offset must be of types int or slice")
