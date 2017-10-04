import os
import re
from os.path import join, dirname

import pytest
from matplotlib import pyplot as plt

from pubgis.match import PUBGISMatch, MatchResult
from pubgis.minimap_iterators.images import ImageIterator

plt.switch_backend('Agg')

GOOD_TEST_COORDS_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels

RESOLUTION_IMAGES_FOLDER = join(dirname(__file__), "resolution_tests")


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_resolution_folder", os.listdir(RESOLUTION_IMAGES_FOLDER))
def test_different_resolutions(test_resolution_folder):
    mini_iter = ImageIterator(os.path.join(RESOLUTION_IMAGES_FOLDER, test_resolution_folder))
    match = PUBGISMatch(minimap_iterator=mini_iter)

    for _, img in mini_iter:
        match_found, _, _, _ = match.find_map_section(img)
        assert match_found == MatchResult.SUCCESSFUL
