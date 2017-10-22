import os

import pytest

from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.video import VideoIterator

TEST_VIDEOS_FOLDER = os.path.join(os.path.dirname(__file__), "test_videos")

VIDEO_CASES = [(os.path.join(TEST_VIDEOS_FOLDER, 'test_video.mp4'),
                ((3079, 4034), (3095, 4061), (3108, 4082), (3123, 4108), (3140, 4138), (3160, 4170),
                 (3178, 4201), (3194, 4228), (3208, 4251), (3228, 4285), (3247, 4318), (3265, 4348),
                 (3281, 4374), (3298, 4402), (3314, 4429), (3330, 4459), (3350, 4491), (3371, 4525),
                 (3387, 4551), (3400, 4574), (3413, 4598)))]


@pytest.mark.parametrize("test_video, expected_positions", VIDEO_CASES)
def test_video_file(test_video, expected_positions):
    video_iter = VideoIterator(test_video, time_step=0.25)
    match = PUBGISMatch(video_iter)

    _, _, unscaled_positions = zip(*match.process_match())

    assert unscaled_positions == expected_positions
