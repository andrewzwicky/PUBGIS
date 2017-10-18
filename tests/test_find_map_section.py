import os
from math import sqrt
from os.path import join, dirname

import cv2
import pytest

from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.images import ImageIterator
from tests.common_test_functions import TEST_COORD_RE, ALLOWED_VARIATION, MOCK_TIME_STEP, \
    generate_expected_positions

MAX_COLOR_DIFF = int(sqrt(255 ** 2 + 255 ** 2 + 255 ** 2))  # diff between white and black

BAD_IMAGES_FOLDER = join(dirname(__file__), "bad")
GOOD_IMAGES_FOLDER = join(dirname(__file__), "good")


@pytest.fixture(scope='module')
def bad_match_fixture():
    bad_iter = ImageIterator(BAD_IMAGES_FOLDER, MOCK_TIME_STEP, just_minimaps=True)
    return PUBGISMatch(bad_iter)


@pytest.fixture(scope='module')
def good_match_fixture():
    good_iter = ImageIterator(GOOD_IMAGES_FOLDER, MOCK_TIME_STEP, just_minimaps=True)
    return PUBGISMatch(good_iter)


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.scandir(BAD_IMAGES_FOLDER))
def test_bad_images(test_image, bad_match_fixture):
    img = cv2.imread(test_image.path)
    assert bad_match_fixture._find_scaled_player_position(img) is None


GOOD_IMAGES = zip(os.scandir(GOOD_IMAGES_FOLDER),
                  generate_expected_positions(GOOD_IMAGES_FOLDER))


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image, expected_position", GOOD_IMAGES)
def test_good_images(test_image, expected_position, good_match_fixture):
    img = cv2.imread(test_image.path)
    scaled_position = good_match_fixture._find_scaled_player_position(img)
    assert scaled_position == expected_position
