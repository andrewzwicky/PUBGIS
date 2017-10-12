import os
import re
from os.path import join, dirname
import shutil

import pytest

from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.images import ImageIterator

GOOD_TEST_COORDS_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels
MOCK_TIME_STEP = 1

MOCK_WATER_VIDEO = join(dirname(__file__), "water_test")
MOCK_PLANE_VIDEO = join(dirname(__file__), "plane_test")


def test_water_mock():
    mini_iter = ImageIterator(MOCK_WATER_VIDEO, MOCK_TIME_STEP, just_minimaps=True)
    match = PUBGISMatch(mini_iter, debug=False)

    for (_, full_position), test_image in zip(match.process_match(), os.listdir(MOCK_WATER_VIDEO)):
        coords_match = GOOD_TEST_COORDS_RE.match(test_image)
        (e_x, e_y) = tuple(map(int, coords_match.groups()))
        if (e_x, e_y) == (0, 0):
            assert full_position is None
        else:
            assert full_position == (pytest.approx(e_x, abs=ALLOWED_VARIATION),
                                     pytest.approx(e_y, abs=ALLOWED_VARIATION))


def test_plane_mock():
    mini_iter = ImageIterator(MOCK_PLANE_VIDEO, MOCK_TIME_STEP, just_minimaps=True)
    match = PUBGISMatch(mini_iter, debug=False)

    for (_, full_position), test_image in zip(match.process_match(), os.listdir(MOCK_PLANE_VIDEO)):
        coords_match = GOOD_TEST_COORDS_RE.match(test_image)
        (e_x, e_y) = tuple(map(int, coords_match.groups()))
        if (e_x, e_y) == (0, 0):
            assert full_position is None
        else:
            assert full_position == (pytest.approx(e_x, abs=ALLOWED_VARIATION),
                                     pytest.approx(e_y, abs=ALLOWED_VARIATION))
