import pytest
import os
from recorder import template_match_minimap
import cv2

MAP = cv2.imread(r"../Erangel_Minimap_scaled.jpg")
GRAY_MAP = cv2.cvtColor(MAP, cv2.COLOR_RGB2GRAY)
PLAYER_INDICATOR_IMG = cv2.imread(r"../circle_mask.jpg", 0)
_, PLAYER_INDICATOR_MASK = cv2.threshold(PLAYER_INDICATOR_IMG, 10, 255, cv2.THRESH_BINARY)


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
    cv2.imshow("mini", minimap)
    s = 253
    cv2.imshow("match", MAP[coords[1]-s//2:coords[1]+s//2, coords[0]-s//2:coords[0]+s//2])
    cv2.waitKey(1000)

