from .common import EEPROMPage, I2CEEPROMPage, OffsetLength, Region
from .eeprom import EEPROM, I2CEEPROM
from .eeprom.i2c import I2CEEPROMFactory
from .transports import Transport

__all__ = [
    "EEPROMPage",
    "I2CEEPROMPage",
    "OffsetLength",
    "Region",
    "EEPROM",
    "I2CEEPROM",
    "I2CEEPROMFactory",
    "Transport",
]


try:
    import smbus3

except ImportError:  # pragma: nocover
    pass

else:
    from .transports.smbus_transport import SMBusTransport

    __all__ += [
        "SMBusTransport",
    ]
