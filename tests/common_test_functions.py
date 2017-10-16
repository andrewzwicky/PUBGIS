import re

TEST_COORD_RE = re.compile(r".*_\d+_(\d+)_(\d+)\.jpg")
ALLOWED_VARIATION = 2  # pixels
MOCK_TIME_STEP = 1
