from pyeeprom.common import OffsetLength
from pyeeprom.eeprom import I2CEEPROM
from pyeeprom.eeprom.i2c import I2CEEPROMFactory


@I2CEEPROMFactory.register
class CAT24C32F(I2CEEPROM):
    num_offsets: int = 4 * 1024
    page_size: int = 32

    offset_length: OffsetLength = OffsetLength.TWO_BYTE
    write_cycle_delay_ms: float = 5.0
