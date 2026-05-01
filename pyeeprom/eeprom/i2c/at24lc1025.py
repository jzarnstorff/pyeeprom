from pyeeprom.common import OffsetLength
from pyeeprom.eeprom import I2CEEPROM
from pyeeprom.eeprom.i2c import I2CEEPROMFactory


@I2CEEPROMFactory.register
class AT24LC1025(I2CEEPROM):
    num_offsets: int = 64 * 1024 * 2
    page_size: int = 128

    offset_length: OffsetLength = OffsetLength.TWO_BYTE
    write_cycle_delay_ms: float = 5.0

    num_blocks: int = 2
    _page_bit: int = 1 << 2

    def adjust_device_address(self, offset: int) -> int:
        if offset >= (self.num_offsets // self.num_blocks):
            return self.address | self._page_bit
        return self.address
