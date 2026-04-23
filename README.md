# PyEEPROM

## Overview

PyEEPROM is a package for reading bytes from and writing bytes to an EEPROM using Python.

It provides:
  - multiple ways to interact with an EEPROM by:
    - the EEPROM object's read, write, and erase methods.
    - an array-like syntax to index or slice into an EEPROM object for read, write, and erase operations.
  - access to all offsets within an EEPROM even those which consume multiple I2C addresses.
  - a method to allow users to define their own library of EEPROMs and register them for use with the PyEEPROM package.

## Installation

Install the PyEEPROM package into your project using `pip`:

    pip install git+https://github.com/jzarnstorff/pyeeprom.git

If using `SMBusTransport` as an I2C communication transport layer to communicate with I2C EEPROM devices, use the `smbus3` extra when installing the PyEEPROM package:

    pip install git+https://github.com/jzarnstorff/pyeeprom.git[smbus3]

## Getting Started

```python
>>> from pyeeprom import I2CEEPROMFactory, Region, SMBusTransport
>>> from smbus3 import SMBus
>>>
>>> factory = I2CEEPROMFactory()
>>> factory.eeproms  # the I2C EEPROM devices registered with the factory
['cat24c32f']
>>>
>>> transport = SMBusTransport(bus=SMBus(1))
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
```

EEPROMs also have an array-like syntax where you can index or slice into an EEPROM object for read, write, and erase operations:

```python
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
```

## Developer Requirements

`Poetry` is used to manage the project's dependencies and can be installed using the installer directly from [install.python-poetry.org](https://install.python-poetry.org/). The script can be executed directly using `curl` and `python` from your Linux environment.

    curl -sSL https://install.python-poetry.org | python3 -

After successfully installing `Poetry`, clone the repository and install the project's dependencies:

    poetry install --with dev,docs

If using `SMBusTransport`, install the optional dependency:

    poetry install --extras smbus3

Source the virtual environment:

    source .venv/bin/activate

Install `pre-commit` to set up the git hook scripts to run linters on the source code when making commits. More information on `pre-commit` can be found at [pre-commit.com](https://pre-commit.com/)

    pre-commit install

The project's documentation can be built using `Sphinx` by running:

    poetry run sphinx-build -aTE docs/source/ docs/build/html/

Open `docs/build/html/index.rst` with a web browser to read the project's documentation.
