import cv2

from pubgis.image_iterator import ImageIterator
from pubgis.match import PUBGISMatch


def test_water_path():
    image_iter = ImageIterator("water_test")
    match = PUBGISMatch(minimap_iterator=image_iter)

    for percent, minimap in match.process_match():
        cv2.imshow("test", cv2.resize(minimap, (0,0), fx=600/minimap.shape[0], fy=600/minimap.shape[0]))
        cv2.waitKey(10)
        print(f"{percent:2.2}")
