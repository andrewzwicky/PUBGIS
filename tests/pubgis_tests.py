import pytest
import os
from pubgis import PUBGIS, MatchResult
import cv2
import re

GOOD_TEST_COORDS_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels


@pytest.fixture(scope='module')
def pubgis_fixture():
    return PUBGIS(full_map_file=r"../full_map_scaled.jpg",
                  mask_file=r"../player_indicator_mask.jpg",
                  debug=False)


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(r'bad'))
def test_bad_images(test_image, pubgis_fixture):
    match_found, coords = pubgis_fixture.template_match(cv2.imread(os.path.join(r'bad', test_image)))
    assert match_found != MatchResult.SUCCESFUL


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(r'good'))
def test_good_images(test_image, pubgis_fixture):
    match_found, (f_x, f_y) = pubgis_fixture.template_match(cv2.imread(os.path.join(r'good', test_image)))
    coords_match = GOOD_TEST_COORDS_RE.match(test_image)
    if coords_match is not None:
        (e_x, e_y) = tuple(map(int, coords_match.groups()))
    else:
        (e_x, e_y) = (None, None)

    assert (match_found, f_x, f_y) == (MatchResult.SUCCESFUL,
                                       pytest.approx(e_x, abs=ALLOWED_VARIATION),
                                       pytest.approx(e_y, abs=ALLOWED_VARIATION))
