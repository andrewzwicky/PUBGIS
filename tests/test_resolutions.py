import os

import pytest

from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.images import ImageIterator
from tests.common_test_functions import MOCK_TIME_STEP

RESOLUTION_IMAGES_FOLDER = os.path.join(os.path.dirname(__file__), "resolution_tests")


@pytest.mark.parametrize("test_resolution_folder", os.scandir(RESOLUTION_IMAGES_FOLDER))
def test_different_resolutions(test_resolution_folder):
    mini_iter = ImageIterator(test_resolution_folder.path, MOCK_TIME_STEP)
    match = PUBGISMatch(mini_iter)
    match.initial_match_found = True

    for _, _, img in mini_iter:
        scaled_pos = match._find_scaled_player_position(img)  # pylint: disable=protected-access
        assert scaled_pos is not None
