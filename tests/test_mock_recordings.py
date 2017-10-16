import os
from os.path import join, dirname

import pytest

from common_test_functions import ALLOWED_VARIATION, MOCK_TIME_STEP, TEST_COORD_RE
from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.images import ImageIterator

MOCK_WATER_VIDEO = join(dirname(__file__), "water_test")
MOCK_PLANE_VIDEO = join(dirname(__file__), "plane_test")

MOCK_VIDEO_FOLDERS = [MOCK_WATER_VIDEO, MOCK_PLANE_VIDEO]


@pytest.mark.parametrize("input_minimap_folder", MOCK_VIDEO_FOLDERS)
def test_mock_video(input_minimap_folder):
    mini_iter = ImageIterator(input_minimap_folder, MOCK_TIME_STEP, just_minimaps=True)
    match = PUBGISMatch(mini_iter)

    for (_, _, unscaled_position), test_image in zip(match.process_match(),
                                                     os.scandir(input_minimap_folder)):
        coords_match = TEST_COORD_RE.match(test_image.name)
        expected_position = tuple(map(int, coords_match.groups()))
        if expected_position == (0, 0):
            assert unscaled_position is None
        else:
            assert unscaled_position == pytest.approx(expected_position, abs=ALLOWED_VARIATION)
