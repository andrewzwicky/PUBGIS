import os
import re
from math import sqrt
from os.path import join, dirname

import cv2
import pytest

from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.images import ImageIterator

GOOD_TEST_COORDS_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels
MAX_COLOR_DIFF = int(sqrt(255 ** 2 + 255 ** 2 + 255 ** 2))  # diff between white and black

BAD_IMAGES_FOLDER = join(dirname(__file__), "bad")
GOOD_IMAGES_FOLDER = join(dirname(__file__), "good")


@pytest.fixture(scope='module')
def bad_match_fixture():
    bad_iter = ImageIterator(BAD_IMAGES_FOLDER, just_minimaps=True)
    return PUBGISMatch(bad_iter)


@pytest.fixture(scope='module')
def good_match_fixture():
    good_iter = ImageIterator(GOOD_IMAGES_FOLDER, just_minimaps=True)
    return PUBGISMatch(good_iter)


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(BAD_IMAGES_FOLDER))
def test_bad_images(test_image, bad_match_fixture):
    img = cv2.imread(os.path.join(BAD_IMAGES_FOLDER, test_image))
    scaled_pos, color_diff, result = bad_match_fixture.find_scaled_player_position(img)
    assert scaled_pos is None


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(GOOD_IMAGES_FOLDER))
def test_good_images(test_image, good_match_fixture):
    img = cv2.imread(os.path.join(GOOD_IMAGES_FOLDER, test_image))
    scaled_pos, color_diff, result = good_match_fixture.find_scaled_player_position(img)
    coords_match = GOOD_TEST_COORDS_RE.match(test_image)
    (e_x, e_y) = tuple(map(int, coords_match.groups()))
    assert scaled_pos == (pytest.approx(e_x, abs=ALLOWED_VARIATION),
                          pytest.approx(e_y, abs=ALLOWED_VARIATION))
