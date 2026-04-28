Usage
=====

Getting Started
---------------

The CAT24C32F EEPROM is found at address ``0x50``:

.. code-block::

    pi@raspberrypi:~/pyeeprom $ i2cdetect -y 1
        0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
    00:                         -- -- -- -- -- -- -- -- 
    10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    50: 50 -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    70: -- -- -- -- -- -- -- --                         
    pi@raspberrypi:~/pyeeprom $ 


Example I2C communication with CAT24C32F EEPROM:

.. code-block:: python

    >>> from pyeeprom import I2CEEPROMFactory, Region, SMBusTransport
    >>> from smbus3 import SMBus
    >>>
    >>> transport = SMBusTransport(bus=SMBus(1))
    >>> factory = I2CEEPROMFactory()
    >>> eeprom = factory.get(i2c_eeprom="cat24c32f", address=0x50, transport=transport)
    >>>
    >>> region = Region(offset=0x00, length=32)
    >>> eeprom.write(region, b"Hello from pyeeprom")
    >>> data = eeprom.read(region)
    >>> data
    b'Hello from pyeeprom\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    >>> 
    >>> eeprom.erase(region)
    >>> data = eeprom.read(region)
    >>> data
    b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    >>> 

EEPROMs also have an array-like syntax where you can index or slice
into an EEPROM object for read, write, and erase operations:

.. code-block:: python

    >>> eeprom[0] = b"h"  # write byte to offset 0
    >>> read_data = eeprom[0:10]  # read 10 bytes starting from offset 0
    >>> read_data
    b'h\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    >>>
    >>> del eeprom[0]  # perform erase operation at offset 0
    >>> read_data = eeprom[0:10]
    >>> read_data
    b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    >>>
    >>> write_data = b"Hello world"
    >>> data_slice = slice(0, len(write_data))
    >>> eeprom[data_slice] = write_data
    >>>
    >>> read_data = eeprom[data_slice]
    >>> read_data
    b'Hello world'
    >>>

Register your own I2C EEPROM with the ``I2CEEPROMFactory``
----------------------------------------------------------

If there isn't a definition for an I2C EEPROM for a
desired EEPROM, add your own I2C EEPROM to your project:

.. code-block::

    (venv) pi@raspberrypi:~/project $ cat eeproms/foo.py
    from pyeeprom import I2CEEPROM, OffsetLength 


    class FooEEPROM(I2CEEPROM):
        num_offsets: int = 128
        page_size: int = 8

        offset_length: OffsetLength = OffsetLength.ONE_BYTE
        write_cycle_delay_ms: float = 5.0

    (venv) pi@raspberrypi:~/project $ 

and register it with the ``I2CEEPROMFactory``:

.. code-block:: python

    >>> from pyeeprom import I2CEEPROMFactory
    >>> 
    >>> factory = I2CEEPROMFactory()
    >>> factory.eeproms
    ['at24c32f']
    >>> 
    >>> from eeproms.foo import FooEEPROM
    >>> 
    >>> factory.register(FooEEPROM)
    >>> factory.eeproms
    ['at24c32f', 'fooeeprom']
    >>> 

Register an entire directory of I2C EEPROMs with the ``I2CEEPROMFactory``
-------------------------------------------------------------------------

If you have an entire directory of I2C EEPROM definitions:

.. code-block::

    (venv) pi@raspberrypi:~/project $ tree
    .
    └── eeproms
        ├── bar.py
        ├── foo.py
        └── __init__.py

    2 directories, 3 files
    (venv) pi@raspberrypi:~/project $ 

simply decorate each concrete ``I2CEEPROM`` with the ``I2CEEPROMFactory``'s
``register`` method:

.. code-block:: python

    from pyeeprom import I2CEEPROM, I2CEEPROMFactory, OffsetLength 


    @I2CEEPROMFactory.register
    class BarEEPROM(I2CEEPROM):
        num_offsets: int = 512
        page_size: int = 32

        offset_length: OffsetLength = OffsetLength.ONE_BYTE
        write_cycle_delay_ms: float = 5.0

.. code-block:: python

    from pyeeprom import I2CEEPROM, I2CEEPROMFactory, OffsetLength


    @I2CEEPROMFactory.register
    class FooEEPROM(I2CEEPROM):
        num_offsets: int = 128
        page_size: int = 8

        offset_length: OffsetLength = OffsetLength.ONE_BYTE
        write_cycle_delay_ms: float = 5.0

and then pass a ``pathlib.Path`` which points to the top directory where your
``I2CEEPROM`` definitions exist on your file system into the ``I2CEEPROMFactory``'s
``load_eeproms_from_path`` method:

.. code-block:: python

    >>> from pyeeprom import I2CEEPROMFactory
    >>> 
    >>> factory = I2CEEPROMFactory()
    >>> factory.eeproms
    ['at24c32f']
    >>> 
    >>> from pathlib import Path
    >>> 
    >>> eeproms_dir = Path("eeproms")
    >>> factory.load_eeproms_from_path(eeproms_dir)
    >>> factory.eeproms
    ['at24c32f', 'bareeprom', 'fooeeprom']
    >>> 

.. warning:: Modules are dynamically imported to trigger registration when using ``load_eeproms_from_path``
