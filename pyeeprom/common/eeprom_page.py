from dataclasses import dataclass
from enum import Enum, auto
from typing import Annotated

from pyeeprom.common.constraints import NumberConstraints, validate_constraints


class OffsetLength(Enum):
    ONE_BYTE = auto()
    TWO_BYTE = auto()


@dataclass(kw_only=True)
class EEPROMPage:
    """Represents one internal page of an EEPROM.

    Attributes:
        offset (int): The starting offset that is desired - may or may not be page-aligned.
        byte_count (int): Amount of bytes until the end of the page from `self.offset`.
    """

    offset: Annotated[int, NumberConstraints(ge=0)]
    byte_count: int

    def __post_init__(self) -> None:
        validate_constraints(self)


@dataclass(kw_only=True)
class I2CEEPROMPage(EEPROMPage):
    """Represents one internal page of an I2C EEPROM.

    Attributes:
        i2c_address (int): The hardware address of the I2C EEPROM.
        offset_length (OffsetLength): Number of bytes of the EEPROM's internal address pointer.
    """

    i2c_address: int
    offset_length: OffsetLength
