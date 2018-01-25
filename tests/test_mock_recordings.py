import os


import pytest
from pytest import param

from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.images import ImageIterator
from tests.common_test_functions import MOCK_TIME_STEP, generate_expected_positions

# pylint: disable=invalid-name
pytestmark = pytest.mark.skip()

try:
    MOCK_FOLDER = os.path.join(os.path.dirname(__file__), "mock_matches")

    MOCK_VIDEO_CASES = [param(dir_entry.path,
                              generate_expected_positions(dir_entry.path),
                              id=dir_entry.name) for dir_entry in os.scandir(MOCK_FOLDER)]
except FileNotFoundError:
    MOCK_FOLDER = None
    MOCK_VIDEO_CASES = []


@pytest.mark.parametrize("input_minimap_folder, expected_positions", MOCK_VIDEO_CASES)
def test_mock_video(input_minimap_folder, expected_positions):
    mini_iter = ImageIterator(input_minimap_folder, MOCK_TIME_STEP, just_minimaps=True)
    match = PUBGISMatch(mini_iter)

    _, _, unscaled_positions = zip(*match.process_match())

    assert list(unscaled_positions) == list(expected_positions)
