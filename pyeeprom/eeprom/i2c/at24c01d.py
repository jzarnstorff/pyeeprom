from pyeeprom.common import OffsetLength
from pyeeprom.eeprom import I2CEEPROM
from pyeeprom.eeprom.i2c import I2CEEPROMFactory


@I2CEEPROMFactory.register
class AT24C01D(I2CEEPROM):
    num_offsets: int = 128
    page_size: int = 8

    offset_length: OffsetLength = OffsetLength.ONE_BYTE
    write_cycle_delay_ms: float = 5.0
