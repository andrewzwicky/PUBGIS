from os.path import join, dirname

import cv2
import pytest

from pubgis.minimap_iterators.images import ImageIterator
from pubgis.match import PUBGISMatch

WATER_IMAGES_FOLDER = join(dirname(__file__), "water_test")


@pytest.mark.skip(reason="test not finished")
def test_water_path():
    image_iter = ImageIterator(WATER_IMAGES_FOLDER)
    match = PUBGISMatch(minimap_iterator=image_iter)

    for percent, minimap in match.process_match():
        cv2.imshow("test", cv2.resize(minimap,
                                      (0, 0),
                                      fx=600 / minimap.shape[0],
                                      fy=600 / minimap.shape[0]))
        cv2.waitKey(10)
        print(f"{percent:2.2}")
