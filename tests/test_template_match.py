import os
import re
from math import sqrt
from os.path import join, dirname

import cv2
from matplotlib.patches import Polygon, Rectangle
import pytest
from matplotlib import pyplot as plt

from pubgis.match import PUBGISMatch, MatchResult, COLOR_DIFF_THRESHS, TEMPLATE_MATCH_THRESHS,\
    MMAP_HEIGHT, MMAP_WIDTH

plt.switch_backend('Agg')

GOOD_TEST_COORDS_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels
MAX_COLOR_DIFF = int(sqrt(255 ** 2 + 255 ** 2 + 255 ** 2))  # diff between white and black

BAD_IMAGES_FOLDER = join(dirname(__file__), "bad")
GOOD_IMAGES_FOLDER = join(dirname(__file__), "good")


@pytest.fixture(scope='module')
def match_fixture():
    return PUBGISMatch()


@pytest.fixture(scope='module')
def template_match_plot_axes():
    fig, ax = plt.subplots(figsize=(12, 10))
    points_list = []
    yield points_list
    for color_diff, match_val, c in points_list:
        ax.scatter(color_diff, match_val, facecolor=c, edgecolor="none", s=10, alpha=0.2)
    ax.set_ylim(0, 1)
    ax.set_xlim(0, MAX_COLOR_DIFF)

    x_coords = [val for val in COLOR_DIFF_THRESHS + [MAX_COLOR_DIFF] for _ in (0, 1)]
    x_coords2 = [val for val in COLOR_DIFF_THRESHS + [0] for _ in (0, 1)]
    y_coords = [1] + [val for val in TEMPLATE_MATCH_THRESHS for _ in (0, 1)] + [1]

    ax.add_patch(Polygon(list(zip(x_coords, y_coords)), alpha=0.1, edgecolor='none', facecolor='g'))
    ax.add_patch(Polygon(list(zip(x_coords2, y_coords)), alpha=0.1, edgecolor='none', facecolor='r'))
    ax.add_patch(Rectangle((0, 0),
                           MAX_COLOR_DIFF,
                           min(TEMPLATE_MATCH_THRESHS),
                           edgecolor="none",
                           facecolor='r',
                           alpha=0.1))
    fig.savefig("summary_plot.png")


@pytest.fixture(scope='module')
def map_coverage_axes():
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)
    ax.imshow(cv2.cvtColor(PUBGISMatch.map, cv2.COLOR_BGR2RGB))
    yield ax
    fig.savefig("map_coverage.png")


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(BAD_IMAGES_FOLDER))
def test_bad_images(test_image, match_fixture, template_match_plot_axes):
    img = cv2.imread(os.path.join(BAD_IMAGES_FOLDER, test_image))
    match_found, (_, _), color_diff, result = match_fixture.find_map_section(img)
    template_match_plot_axes.append((color_diff, result, 'r'))
    assert match_found != MatchResult.SUCCESSFUL


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(GOOD_IMAGES_FOLDER))
def test_good_images(test_image, match_fixture, template_match_plot_axes, map_coverage_axes):
    img = cv2.imread(os.path.join(GOOD_IMAGES_FOLDER, test_image))
    match_found, (f_x, f_y), color_diff, result = match_fixture.find_map_section(img)
    template_match_plot_axes.append((color_diff, result, 'g'))
    map_coverage_axes.add_patch(Rectangle((f_x - (MMAP_WIDTH // 2), f_y - (MMAP_HEIGHT // 2)),
                                          MMAP_WIDTH,
                                          MMAP_HEIGHT,
                                          edgecolor="none",
                                          facecolor='white',
                                          alpha=0.1))
    coords_match = GOOD_TEST_COORDS_RE.match(test_image)
    if coords_match is not None:
        (e_x, e_y) = tuple(map(int, coords_match.groups()))
    else:
        (e_x, e_y) = (None, None)

    assert (match_found, f_x, f_y) == (MatchResult.SUCCESSFUL,
                                       pytest.approx(e_x, abs=ALLOWED_VARIATION),
                                       pytest.approx(e_y, abs=ALLOWED_VARIATION))
