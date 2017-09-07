import os
import re

import cv2
import matplotlib.patches as patches
import pytest
from matplotlib import pyplot as plt

from pubgis.pubgis_match import PUBGISMatch, MatchResult, COLOR_DIFF_THRESHOLD, TEMPLATE_MATCH_THRESHOLD

GOOD_TEST_COORDS_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels
MAX_COLOR_DIFF = 450  # approx sqrt(255**2 + 255**2 + 255**2), between white and black


@pytest.fixture(scope='module')
def pubgis_fixture():
    return PUBGISMatch(video_file=r"C:\Users\test.mp4")


@pytest.fixture(scope='module')
def summary_plot_axes():
    fig, ax = plt.subplots(figsize=(12, 10))
    yield ax
    ax.set_ylim(0, 1)
    ax.set_xlim(left=0)
    ax.add_patch(patches.Rectangle((0, 0), COLOR_DIFF_THRESHOLD, 1, edgecolor="none", facecolor='r', alpha=0.1))
    ax.add_patch(patches.Rectangle((COLOR_DIFF_THRESHOLD, 0), MAX_COLOR_DIFF-COLOR_DIFF_THRESHOLD, TEMPLATE_MATCH_THRESHOLD, edgecolor="none", facecolor='r', alpha=0.1))
    ax.add_patch(patches.Rectangle((COLOR_DIFF_THRESHOLD, TEMPLATE_MATCH_THRESHOLD), MAX_COLOR_DIFF-COLOR_DIFF_THRESHOLD, 1-TEMPLATE_MATCH_THRESHOLD, edgecolor="none", facecolor='g', alpha=0.1))
    fig.savefig("summary_plot.png")


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(r'bad'))
def test_bad_images(test_image, pubgis_fixture, summary_plot_axes):
    img = cv2.imread(os.path.join(r'bad', test_image))
    match_found, coords, ind_color, color_diff, match_val, this_percent = pubgis_fixture.template_match((None, img))
    summary_plot_axes.scatter(color_diff, match_val, color="r", s=10)
    assert match_found != MatchResult.SUCCESFUL


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(r'good'))
def test_good_images(test_image, pubgis_fixture, summary_plot_axes):
    img = cv2.imread(os.path.join(r'good', test_image))
    match_found, coords, ind_color, color_diff, match_val, _ = pubgis_fixture.template_match((None, img))
    f_x, f_y = coords
    summary_plot_axes.scatter(color_diff, match_val, color="g", s=10)
    coords_match = GOOD_TEST_COORDS_RE.match(test_image)
    if coords_match is not None:
        (e_x, e_y) = tuple(map(int, coords_match.groups()))
    else:
        (e_x, e_y) = (None, None)

    assert (match_found, f_x, f_y) == (MatchResult.SUCCESFUL,
                                       pytest.approx(e_x, abs=ALLOWED_VARIATION),
                                       pytest.approx(e_y, abs=ALLOWED_VARIATION))
