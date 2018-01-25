import os

import cv2
import pytest

from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.images import ImageIterator
from tests.common_test_functions import MOCK_TIME_STEP, generate_expected_positions

# pylint: disable=invalid-name
pytestmark = pytest.mark.skip()

try:
    BAD_IMAGES_FOLDER = os.path.join(os.path.dirname(__file__), "bad")
    GOOD_IMAGES_FOLDER = os.path.join(os.path.dirname(__file__), "good")
    GOOD_IMAGES = zip(os.scandir(GOOD_IMAGES_FOLDER), generate_expected_positions(GOOD_IMAGES_FOLDER))
except FileNotFoundError:
    BAD_IMAGES_FOLDER = None
    GOOD_IMAGES_FOLDER = None
    GOOD_IMAGES = []


@pytest.fixture(scope='module')
def _bad_match_fixture():
    bad_iter = ImageIterator(BAD_IMAGES_FOLDER, MOCK_TIME_STEP, just_minimaps=True)
    return PUBGISMatch(bad_iter)


@pytest.fixture(scope='module')
def _good_match_fixture():
    good_iter = ImageIterator(GOOD_IMAGES_FOLDER, MOCK_TIME_STEP, just_minimaps=True)
    return PUBGISMatch(good_iter)


@pytest.mark.parametrize("test_image", os.scandir(BAD_IMAGES_FOLDER))
def test_bad_images(test_image, _bad_match_fixture):
    img = cv2.imread(test_image.path)
    scaled_pos = _bad_match_fixture._find_scaled_player_position(img)  # pylint: disable=protected-access
    assert scaled_pos is None


@pytest.mark.parametrize("test_image, expected_position", GOOD_IMAGES)
def test_good_images(test_image, expected_position, _good_match_fixture):
    img = cv2.imread(test_image.path)
    scaled_position = _good_match_fixture._find_scaled_player_position(img)  # pylint: disable=protected-access
    assert scaled_position == expected_position
