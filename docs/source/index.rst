.. PyEEPROM documentation master file, created by
   sphinx-quickstart on Mon Apr 13 20:43:46 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

PyEEPROM documentation
======================

``PyEEPROM`` is a package for reading bytes from and writing bytes to an EEPROM
using Python. It provides:

- multiple ways to interact with an EEPROM by:
   - the EEPROM object's read, write, and erase methods.
   - an array-like syntax to index or slice into an EEPROM object for read, write,
     and erase operations.
- access to all offsets within an EEPROM even those which consume multiple I2C
  addresses.
- a method to allow users to define their own library of EEPROMs and register them
  for use with the ``PyEEPROM`` package.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   user_guide
   api_reference
   changelog
