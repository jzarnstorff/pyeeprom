# PyEEPROM

## Overview

PyEEPROM is a package for reading bytes from and writing bytes to an EEPROM using Python.

It provides:
  - multiple ways to interact with an EEPROM by:
    - the EEPROM object's read, write, and erase methods.
    - an array-like syntax to index or slice into an EEPROM object for read, write, and erase operations.
  - access to all offsets within an EEPROM even those which consume multiple I2C addresses.
  - a method to allow users to define their own library of EEPROMs and register them for use with the PyEEPROM package.

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
