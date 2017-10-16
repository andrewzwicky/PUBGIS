import re

TEST_COORD_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels
MOCK_TIME_STEP = 1


def get_test_image_coords(filename):
    coords_match = TEST_COORD_RE.match(filename)
    return tuple(map(int, coords_match.groups()))
