import pytest

from pubgis.match import PUBGISMatch


@pytest.fixture(scope='module')
def pubgis_fixture():
    return PUBGISMatch()


CASES = [
    # no coordinates should return full map size
    (None, (0, 0, 5079, 5079)),

    ([(500, 500)], (200, 200, 600, 600)),
    ([(500, 499)], (200, 199, 600, 600)),
    ([(500, 501)], (200, 201, 600, 600)),
    ([(600, 600), (700, 1200)], (320, 570, 660, 660)),
    ([(300, 300), (1300, 300)], (270, 0, 1060, 1060)),

    # along the sides of the map, should push square towards the center
    ([(5069, 2000), (5069, 3000)], (4020, 1970, 1060, 1060)),
    ([(10, 2000), (10, 3000)], (0, 1970, 1060, 1060)),
    ([(2000, 10), (3000, 10)], (1970, 0, 1060, 1060)),
    ([(2000, 5069), (3000, 5069)], (1970, 4020, 1060, 1060)),

    # corners
    ([(0, 0), (600, 600)], (0, 0, 630, 630)),
    ([(5079, 5079), (4479, 4479)], (4449, 4449, 630, 630)),
    ([(0, 5079), (600, 4479)], (0, 4449, 630, 630)),
    ([(5079, 0), (4479, 600)], (4449, 0, 630, 630)),

    # entire width
    ([(1000, 0), (1000, 5079)], (0, 0, 5079, 5079)),

    # entire height
    ([(0, 1000), (5079, 1000)], (0, 0, 5079, 5079)),

    # entire area
    ([(0, 0), (5079, 5079)], (0, 0, 5079, 5079)),
]


# noinspection PyShadowingNames
@pytest.mark.parametrize("input_coords, expected_bounds", CASES)
def test_find_path_bounds(input_coords, expected_bounds, pubgis_fixture):
    pubgis_fixture.all_coords = input_coords
    assert pubgis_fixture.find_path_bounds() == expected_bounds
