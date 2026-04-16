from pytest_mock.plugin import MockerFixture

from pyeeprom.common.region import Region


def test_region_validate_constraints_called(mocker: MockerFixture) -> None:
    mock_validate = mocker.patch("pyeeprom.common.region.validate_constraints")
    region = Region(offset=0, length=1)
    mock_validate.assert_called_once_with(region)
