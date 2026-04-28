Installation
============

Install the ``PyEEPROM`` package into your project using ``pip``::

    pip install git+https://github.com/jzarnstorff/pyeeprom.git

If using ``SMBusTransport`` as an I2C communication transport layer
to communicate with I2C EEPROM devices, use the ``smbus3`` extra when
installing the ``PyEEPROM`` package::

    pip install git+https://github.com/jzarnstorff/pyeeprom.git[smbus3]
