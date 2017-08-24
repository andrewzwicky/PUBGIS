import pytest
import os
from recorder import template_match
import cv2

gray_map = cv2.imread(r"../Erangel_Minimap_scaled.jpg", 0)


@pytest.mark.parametrize("test_image", os.listdir('bad'))
def test_bad_images(test_image):
    max_val, coords = template_match(cv2.imread(os.path.join('bad', test_image)), gray_map)
    assert coords is None


@pytest.mark.parametrize("test_image", os.listdir('good'))
def test_good_images(test_image):
    max_val, coords = template_match(cv2.imread(os.path.join('good', test_image)), gray_map)
    assert coords is not None
