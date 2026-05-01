from pyeeprom.common import OffsetLength
from pyeeprom.eeprom import I2CEEPROM
from pyeeprom.eeprom.i2c import I2CEEPROMFactory


@I2CEEPROMFactory.register
class AT24C08D(I2CEEPROM):
    num_offsets: int = 1024
    page_size: int = 16

    offset_length: OffsetLength = OffsetLength.ONE_BYTE
    write_cycle_delay_ms: float = 5.0

    num_blocks: int = 4

    def adjust_device_address(self, offset: int) -> int:
        offset_a8 = (offset >> 8) & 0x1
        offset_a9 = (offset >> 9) & 0x1
        return self.address | (offset_a9 << 1) | (offset_a8 << 0)
