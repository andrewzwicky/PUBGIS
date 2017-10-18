import os
import re

import pytest

TEST_COORD_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels
MOCK_TIME_STEP = 1


def get_test_image_coords(filename):
    coords_match = TEST_COORD_RE.match(filename)
    coords = tuple(map(int, coords_match.groups()))
    if coords == (0, 0):
        coords = None

    return coords


def generate_expected_positions(test_image_dir):
    coords = []
    for img in os.listdir(test_image_dir):
        coords.append(pytest.approx(get_test_image_coords(img), abs=ALLOWED_VARIATION))

    return coords
