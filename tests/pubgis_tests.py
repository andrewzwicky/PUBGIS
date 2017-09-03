import pytest
import os
from pubgis import PUBGIS, MatchResult, M, B
import cv2
import re
from matplotlib import pyplot as plt

GOOD_TEST_COORDS_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels


@pytest.fixture(scope='module')
def pubgis_fixture():
    return PUBGIS(full_map_file=r"../full_map_scaled.jpg",
                  mask_file=r"../player_indicator_mask.jpg",
                  debug=False)


@pytest.fixture(scope='module')
def summary_plot_axes():
    fig, ax = plt.subplots(figsize=(12, 10))
    yield ax
    ax.set_xlabel("")
    xs = [0, 200]
    ys = [M*x + B for x in xs]
    plt.plot(xs, ys, color='k')
    ax.set_ylim(0, 1)
    ax.set_xlim(left=0)
    fig.savefig("summary_plot.png")


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(r'bad'))
def test_bad_images(test_image, pubgis_fixture, summary_plot_axes):
    match_found, _, ind_color_ok, _, _, c_diff, _, match_val, _ = pubgis_fixture.template_match(cv2.imread(os.path.join(r'bad', test_image)))
    summary_plot_axes.scatter(c_diff, match_val, color="g" if ind_color_ok else "r", s=10)
    summary_plot_axes.scatter(c_diff, match_val, color="r", s=8)
    assert match_found != MatchResult.SUCCESFUL


# noinspection PyShadowingNames
@pytest.mark.parametrize("test_image", os.listdir(r'good'))
def test_good_images(test_image, pubgis_fixture, summary_plot_axes):
    match_found, (f_x, f_y), ind_color_ok, _, _, c_diff, _, match_val, _ = pubgis_fixture.template_match(cv2.imread(os.path.join(r'good', test_image)))
    summary_plot_axes.scatter(c_diff, match_val, color="g" if ind_color_ok else "r", s=10)
    summary_plot_axes.scatter(c_diff, match_val, color="g", s=8)
    coords_match = GOOD_TEST_COORDS_RE.match(test_image)
    if coords_match is not None:
        (e_x, e_y) = tuple(map(int, coords_match.groups()))
    else:
        (e_x, e_y) = (None, None)

    assert (match_found, f_x, f_y) == (MatchResult.SUCCESFUL,
                                       pytest.approx(e_x, abs=ALLOWED_VARIATION),
                                       pytest.approx(e_y, abs=ALLOWED_VARIATION))
