import pytest

from pubgis.support import *

FIND_PATH_BOUND_CASES = [
    # no coordinates should return full map size
    (5079, None, ((0, 0), 5079)),

    (5079, [(0, 0)], ((0, 0), 600)),
    (5079, [(0, 5079)], ((0, 5079 - 600), 600)),
    (5079, [(5079, 0)], ((5079 - 600, 0), 600)),
    (5079, [(5079, 5079)], ((5079 - 600, 5079 - 600), 600)),

    (5079, [(500, 500)], ((200, 200), 600)),
    (5079, [(500, 499)], ((200, 199), 600)),
    (5079, [(500, 501)], ((200, 201), 600)),
    (5079, [(600, 600), (700, 1200)], ((320, 570), 660)),
    (5079, [(300, 300), (1300, 300)], ((270, 0), 1060)),

    # along the sides of the map, should push square towards the center
    (5079, [(5079, 2000), (5079, 3000)], ((5079 - 1060, 1970), 1060)),
    (5079, [(10, 2000), (10, 3000)], ((0, 1970), 1060)),
    (5079, [(2000, 10), (3000, 10)], ((1970, 0), 1060)),
    (5079, [(2000, 5079), (3000, 5079)], ((1970, 5079 - 1060), 1060)),

    # corners
    (5079, [(0, 0), (600, 600)], ((0, 0), 660)),
    (5079, [(5079, 5079), (4479, 4479)], ((5079 - 660, 5079 - 660), 660)),
    (5079, [(0, 5079), (600, 4479)], ((0, 5079 - 660), 660)),
    (5079, [(5079, 0), (4479, 600)], ((5079 - 660, 0), 660)),

    # entire width
    (5079, [(1000, 0), (1000, 5079)], ((0, 0), 5079)),

    # entire height
    (5079, [(0, 1000), (5079, 1000)], ((0, 0), 5079)),

    # entire area
    (5079, [(0, 0), (5079, 5079)], ((0, 0), 5079)),
]


@pytest.mark.parametrize("map_size, input_coords, expected_bounds", FIND_PATH_BOUND_CASES)
def test_find_path_bounds(map_size, input_coords, expected_bounds):
    assert find_path_bounds(map_size, input_coords) == expected_bounds


UNSCALED_COORD_CASES = [
    ((0, 0), 1, (0, 0)),
    ((0, 0), .25, (0, 0)),
    ((0, 0), .5, (0, 0)),
    ((100, 100), .5, (200, 200)),
    (None, .5, None),
    (None, .15, None),
]


@pytest.mark.parametrize("input_coords, scale, expected_coords", UNSCALED_COORD_CASES)
def test_unscale_coords(input_coords, scale, expected_coords):
    assert unscale_coords(input_coords, scale) == expected_coords


COORDINATE_SUM_CASES = [
    ((0, 0), (100, 100), (100, 100)),
    ((240, 0), (100, 100), (340, 100)),
    ((400, 600), (100, 300), (500, 900)),
    ((0, 0), (0, 0), (0, 0)),
]


@pytest.mark.parametrize("coords_a, coords_b, expected_coords", COORDINATE_SUM_CASES)
def test_coordinate_sum(coords_a, coords_b, expected_coords):
    assert coordinate_sum(coords_a, coords_b) == expected_coords


COORDINATE_OFFSET_CASES = [
    ((0, 0), 100, (100, 100)),
    ((240, 0), 100, (340, 100)),
    ((400, 600), 100, (500, 700)),
    ((0, 0), 0, (0, 0)),
]


@pytest.mark.parametrize("coords_a, offset, expected_coords", COORDINATE_OFFSET_CASES)
def test_coordinate_offset(coords_a, offset, expected_coords):
    assert coordinate_offset(coords_a, offset) == expected_coords


GET_COORDS_TEST_CASES = [
    ((0, 0), 100, (slice(0, 100), slice(0, 100))),
    ((240, 600), 200, (slice(600, 800), slice(240, 440))),
    ((300, 0), 150, (slice(0, 150), slice(300, 450))),
]


@pytest.mark.parametrize("coords, size, expected_slice", GET_COORDS_TEST_CASES)
def test_create_slice(coords, size, expected_slice):
    assert create_slice(coords, size) == expected_slice


GET_COORDS_TEST_CASES = [
    ((0, 0), (slice(0, 100), slice(0, 100))),
    ((240, 600), (slice(600, 800), slice(240, 440))),
    ((300, 0), (slice(0, 150), slice(300, 450))),
    ((300, 0), (slice(None, 150), slice(300, 450))),
    ((0, 0), slice(None, None, None)),
]


@pytest.mark.parametrize("expected_coords, slice_tuple", GET_COORDS_TEST_CASES)
def test_get_coords_from_slices(expected_coords, slice_tuple):
    assert get_coords_from_slices(slice_tuple) == expected_coords
