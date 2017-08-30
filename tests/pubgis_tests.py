import pytest
import os
from pubgis import PUBGIS
import cv2


@pytest.fixture(scope='module')
def pubgis_fixture():
    return PUBGIS(full_map_file=r"../Erangel_Minimap_scaled.jpg", mask_file=r"../circle_mask.jpg")


@pytest.mark.parametrize("test_image", os.listdir('bad'))
def test_bad_images(test_image, pubgis_fixture):
    match_found, coords, _ = pubgis_fixture.template_match_minimap(cv2.imread(os.path.join('bad', test_image)))
    assert not match_found


@pytest.mark.parametrize("test_image", os.listdir('good'))
def test_good_images(test_image, pubgis_fixture):
    match_found, coords, _ = pubgis_fixture.template_match_minimap(cv2.imread(os.path.join('good', test_image)))
    assert match_found
