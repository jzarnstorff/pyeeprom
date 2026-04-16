from pytest_mock.plugin import MockerFixture

from pyeeprom.common.eeprom_page import EEPROMPage


def test_eeprom_page_validate_constraints_called(mocker: MockerFixture) -> None:
    mock_validate = mocker.patch("pyeeprom.common.eeprom_page.validate_constraints")
    eeprom_page = EEPROMPage(offset=0, byte_count=1)
    mock_validate.assert_called_once_with(eeprom_page)
