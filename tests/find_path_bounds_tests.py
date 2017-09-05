import pytest
from pubgis import PUBGISMatch


@pytest.fixture(scope='module')
def pubgis_fixture():
    return PUBGISMatch()

CASES = [
    (None, (0, 0, 5079, 5079)),
    ([(500, 500)], (200, 200, 600, 600)),
    ([(500, 499)], (200, 199, 600, 600)),
    ([(500, 501)], (200, 201, 600, 600)),
    ([(600, 600), (700, 1200)], (320, 570, 660, 660)),
    ([(300, 300), (1300, 300)], (270, 0, 1060, 1060)),
         ]


# noinspection PyShadowingNames
@pytest.mark.parametrize("input_coords, expected_bounds", CASES)
def test_find_path_bounds(input_coords, expected_bounds, pubgis_fixture):
    pubgis_fixture.all_coords = input_coords
    assert pubgis_fixture.find_path_bounds() == expected_bounds
