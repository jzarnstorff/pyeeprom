from dataclasses import dataclass
from typing import Annotated

from pyeeprom.common.constraints import NumberConstraints, validate_constraints


@dataclass
class Region:
    """Represents a contiguous number of offsets within an EEPROM.

    Attributes:
        offset (int): The starting offset that is desired - may or may not be page-aligned.
        length (int): Length of the region starting from `self.offset`.
    """

    offset: Annotated[int, NumberConstraints(ge=0)]
    length: Annotated[int, NumberConstraints(ge=1)]

    def __post_init__(self) -> None:
        validate_constraints(self)
