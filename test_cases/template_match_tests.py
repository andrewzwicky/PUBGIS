import pytest
import os
from recorder import template_match_minimap, markup_image_debug
import cv2

GRAY_MAP = cv2.imread(r"../Erangel_Minimap_scaled.jpg", 0)
PLAYER_INDICATOR_IMG = cv2.imread(r"../circle_mask.jpg", 0)
_, PLAYER_INDICATOR_MASK = cv2.threshold(PLAYER_INDICATOR_IMG, 10, 255, cv2.THRESH_BINARY)


@pytest.mark.parametrize("test_image", os.listdir('bad'))
def test_bad_images(test_image):
    match_found,\
    max_val,\
    coords,\
    ind_color,\
    ind_in_range,\
    minimap = template_match_minimap(cv2.imread(os.path.join('bad', test_image)),
                                     GRAY_MAP,
                                     PLAYER_INDICATOR_MASK)
    assert not match_found


@pytest.mark.parametrize("test_image", os.listdir('good'))
def test_good_images(test_image):
    match_found,\
    max_val,\
    coords,\
    ind_color,\
    ind_in_range,\
    minimap = template_match_minimap(cv2.imread(os.path.join('good', test_image)),
                                     GRAY_MAP,
                                     PLAYER_INDICATOR_MASK)
    if not match_found:
        debug_minimap = markup_image_debug(minimap, max_val, ind_in_range, ind_color)
        cv2.imwrite(f"failed/{test_image}_failed.jpg", debug_minimap)

    assert match_found
