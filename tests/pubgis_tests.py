import pytest
import os
from pubgis import PUBGIS
import cv2


@pytest.fixture(scope='module')
def pubgis_fixture():
    return PUBGIS(full_map_file=r"../full_map_scaled.jpg", mask_file=r"../player_indicator_mask.jpg")


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(r'bad'))
def test_bad_images(test_image, pubgis_fixture):
    match_found, coords, = pubgis_fixture.template_match(cv2.imread(os.path.join(r'bad', test_image)))
    assert not match_found


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(r'good'))
def test_good_images(test_image, pubgis_fixture):
    match_found, coords, = pubgis_fixture.template_match(cv2.imread(os.path.join(r'good', test_image)))
    assert match_found
