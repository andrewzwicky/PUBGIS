import pytest
import os
from recorder import template_match_minimap
import cv2

GRAY_MAP = cv2.imread(r"../Erangel_Minimap_scaled.jpg", 0)
PLAYER_INDICATOR_IMG = cv2.imread(r"../circle_mask.jpg", 0)
_, PLAYER_INDICATOR_MASK = cv2.threshold(PLAYER_INDICATOR_IMG, 10, 255, cv2.THRESH_BINARY)


@pytest.mark.parametrize("test_image", os.listdir('bad'))
def test_bad_images(test_image):
    coords_found, coords = template_match_minimap(cv2.imread(os.path.join('bad', test_image)),
                                                  GRAY_MAP,
                                                  PLAYER_INDICATOR_MASK)
    assert not coords_found


@pytest.mark.parametrize("test_image", os.listdir('good'))
def test_good_images(test_image):
    coords_found, coords = template_match_minimap(cv2.imread(os.path.join('good', test_image)),
                                                  GRAY_MAP,
                                                  PLAYER_INDICATOR_MASK)
    assert coords_found
