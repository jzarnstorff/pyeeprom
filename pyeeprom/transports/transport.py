from collections.abc import Sequence
from typing import Protocol

from pyeeprom.common import EEPROMPage


class Transport(Protocol):
    """Protocol defining the interface used to communicate with EEPROM pages.

    Any class implementing this protocol must provide methods for
    reading from and writing to an EEPROM page.
    """

    def write(self, page: EEPROMPage, data: Sequence[int]) -> None:
        """Write a sequence of integer data to a specific EEPROM page.

        Args:
            page (EEPROMPage): The target EEPROM page to write to.
            data (Sequence[int]): A sequence of integer values (typically
                bytes in the range 0-255) to be written to the page.

        Returns:
            None

        Notes:
            - Implementations may impose constraints on the size of `data`
              based on the EEPROM page size.
            - This method is expected to overwrite existing data in the page.
        """

    def read(self, page: EEPROMPage) -> Sequence[int]:
        """Read data from a specific EEPROM page.

        Args:
            page (EEPROMPage): The EEPROM page to read from.

        Returns:
            Sequence[int]: A sequence of integer values representing the
            data stored in the page (typically bytes in the range 0-255).

        Notes:
            - The length of the returned sequence is typically determined
              by the EEPROM page size.
            - The returned data should reflect the current contents of the page.
        """
