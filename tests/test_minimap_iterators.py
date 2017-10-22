import os

import pytest

from pubgis.minimap_iterators.video import VideoIterator

TEST_VIDEO = os.path.join(os.path.dirname(__file__), "test_videos", 'test_video.mp4')


def test_noexistant_video_file():
    with pytest.raises(FileNotFoundError):
        VideoIterator(r"doesnt_exist")


def test_negative_landing_time():
    with pytest.raises(ValueError):
        VideoIterator(TEST_VIDEO, landing_time=-1)


def test_death_before_landing():
    with pytest.raises(ValueError):
        VideoIterator(TEST_VIDEO, landing_time=15, death_time=10)
