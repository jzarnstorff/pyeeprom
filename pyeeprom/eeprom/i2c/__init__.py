from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import ClassVar, dataclass_transform

from pyeeprom.eeprom import I2CEEPROM
from pyeeprom.transports import Transport


@dataclass
class I2CEEPROMFactory:
    """Factory and registry for I2C EEPROM implementations.

    This class is responsible for:
        - Discovering EEPROM implementations from Python modules on disk
        - Registering EEPROM classes via a decorator-style interface
        - Providing lookup and instantiation of EEPROM objects by name

    Registered EEPROM classes must subclass `I2CEEPROM` and are stored
    in a class-level registry (`i2c_eeproms`).

    Attributes:
        i2c_eeproms (ClassVar[dict[str, type[I2CEEPROM]]): Dictionary of
            registered I2C EEPROM devices

    Notes:
        - Modules are dynamically imported to trigger registration.
    """

    i2c_eeproms: ClassVar[dict[str, type[I2CEEPROM]]] = {}

    def __post_init__(self) -> None:
        # Automatically load and register EEPROM implementations
        # from the current directory when the factory is instantiated.
        self.load_eeproms_from_path(eeproms_path=Path(__file__).resolve().parent)

    @property
    def eeproms(self) -> list[str]:
        """List all registered EEPROM names.

        Returns:
            list[str]: A list of string keys representing registered EEPROM types.
        """
        return list(self.i2c_eeproms.keys())

    @classmethod
    @dataclass_transform()
    def register(cls, i2c_eeprom: type[I2CEEPROM]) -> None:
        """Register an I2C EEPROM class in the factory.

        If `i2c_eeprom.name` is defined, it is used as the registry key.
        Otherwise, the lowercase class name is used.

        The class is:
            - Validated to ensure it subclasses `I2CEEPROM`
            - Optionally assigned a custom name via `i2c_eeprom.name`
            - Converted into a dataclass before being stored

        Args:
            i2c_eeprom: The EEPROM class to register.

        Returns:
            None
        """

        if not issubclass(i2c_eeprom, I2CEEPROM):
            return

        # Allow custom names to avoid naming collisions
        key = i2c_eeprom.name or i2c_eeprom.__name__.lower()
        cls.i2c_eeproms[key] = dataclass(i2c_eeprom)

    @staticmethod
    def load_module(path: Path) -> None:
        """Dynamically load a Python module from a file path.

        This executes the module, which is expected to trigger
        EEPROM class registration via decorators.

        Args:
            path (Path): Path to the Python file to load.

        Returns:
            None
        """

        spec = spec_from_file_location(path.name, path)
        if spec is None:
            return

        module = module_from_spec(spec)
        if spec.loader is None:
            return

        # Execute the module to trigger any registration side-effects
        spec.loader.exec_module(module)

    def load_eeproms_from_path(self, eeproms_path: Path) -> None:
        """Recursively discover and load EEPROM modules from a directory.

        All `.py` files (except `__init__.py`) are imported to trigger
        registration of EEPROM classes. Non-existent or non-directory paths
        are ignored. This method relies on module import side-effects for
        registration.

        Args:
            eeproms_path: Directory containing EEPROM implementation modules.

        Returns
            None
        """

        if not (eeproms_path.exists() and eeproms_path.is_dir()):
            return None

        for path in eeproms_path.rglob("*.py"):
            if path.name == "__init__.py":
                continue

            self.load_module(path)

    def get(self, i2c_eeprom: str, address: int, transport: Transport) -> I2CEEPROM:
        """Retrieve and instantiate a registered EEPROM by name.

        Args:
            i2c_eeprom (str): Name of the registered EEPROM (case-insensitive).
            address (int): I2C device address.
            transport (Transport): Transport interface used for I2C communication.

        Returns:
            I2CEEPROM: An initialized instance of the requested EEPROM class.

        Raises:
            KeyError: If no EEPROM is registered under the given name.
        """
        if (eeprom := self.i2c_eeproms.get(i2c_eeprom.lower())) is not None:
            return eeprom(address=address, i2c_transport=transport)  # type: ignore

        raise KeyError(f"There are no I2C EEPROMs registered with name: {i2c_eeprom}")
