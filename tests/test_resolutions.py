import os
import re
from os.path import join, dirname

import pytest

from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.images import ImageIterator

GOOD_TEST_COORDS_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels
MOCK_TIME_STEP = 1

RESOLUTION_IMAGES_FOLDER = join(dirname(__file__), "resolution_tests")


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_resolution_folder", os.listdir(RESOLUTION_IMAGES_FOLDER))
def test_different_resolutions(test_resolution_folder):
    mini_iter = ImageIterator(os.path.join(RESOLUTION_IMAGES_FOLDER, test_resolution_folder),
                              MOCK_TIME_STEP)
    match = PUBGISMatch(mini_iter)
    match.initial_match_found = True

    for _, _, img in mini_iter:
        scaled_pos, _, _ = match.find_scaled_player_position(img)
        assert scaled_pos is not None
