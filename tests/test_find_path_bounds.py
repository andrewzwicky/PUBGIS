import pytest

from pubgis.match import PUBGISMatch

CASES = [
    # no coordinates should return full map size
    (None, (0, 0, 5079)),

    ([(0, 0)], (0, 0, 600)),
    ([(0, 5079)], (0, 5079 - 600, 600)),
    ([(5079, 0)], (5079 - 600, 0, 600)),
    ([(5079, 5079)], (5079 - 600, 5079 - 600, 600)),

    ([(500, 500)], (200, 200, 600)),
    ([(500, 499)], (200, 199, 600)),
    ([(500, 501)], (200, 201, 600)),
    ([(600, 600), (700, 1200)], (320, 570, 660)),
    ([(300, 300), (1300, 300)], (270, 0, 1060)),

    # along the sides of the map, should push square towards the center
    ([(5079, 2000), (5079, 3000)], (5079 - 1060, 1970, 1060)),
    ([(10, 2000), (10, 3000)], (0, 1970, 1060)),
    ([(2000, 10), (3000, 10)], (1970, 0, 1060)),
    ([(2000, 5079), (3000, 5079)], (1970, 5079 - 1060, 1060)),

    # corners
    ([(0, 0), (600, 600)], (0, 0, 660)),
    ([(5079, 5079), (4479, 4479)], (5079 - 660, 5079 - 660, 660)),
    ([(0, 5079), (600, 4479)], (0, 5079 - 660, 660)),
    ([(5079, 0), (4479, 600)], (5079 - 660, 0, 660)),

    # entire width
    ([(1000, 0), (1000, 5079)], (0, 0, 5079)),

    # entire height
    ([(0, 1000), (5079, 1000)], (0, 0, 5079)),

    # entire area
    ([(0, 0), (5079, 5079)], (0, 0, 5079)),
]


# noinspection PyShadowingNames
@pytest.mark.parametrize("input_coords, expected_bounds", CASES)
def test_find_path_bounds(input_coords, expected_bounds):
    assert PUBGISMatch.find_path_bounds(input_coords) == expected_bounds
