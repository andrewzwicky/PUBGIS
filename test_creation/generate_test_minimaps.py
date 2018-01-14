import argparse
import os

import cv2
import numpy as np

from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.video import VideoIterator
from pubgis.support import unscale_coords

J = 106
K = 107
L = 108


def generate_test_minimaps(video_file):
    video_name = os.path.splitext(os.path.basename(video_file))[0]
    video_iter = VideoIterator(video_file=video_file, time_step=1)
    match = PUBGISMatch(video_iter, debug=True)

    test_name = "long_boat_test"

    for i, (_, _, minimap) in enumerate(video_iter):
        raw_minimap = np.copy(minimap)
        scaled_map_pos = match._find_scaled_player_position(minimap)
        if scaled_map_pos:
            found_x, found_y = unscale_coords(scaled_map_pos, match.scale)
        key = cv2.waitKey(-1)

        if key == J:
            output_name = f"{video_name}_{i:0>5}.jpg"
        elif key == K:
            output_name = f"{video_name}_{i:0>5}_0_0.jpg"
            match.missed_frames += 1
        elif key == L:
            match.last_known_position = (found_x, found_y)
            match.missed_frames = 0
            output_name = f"{video_name}_{i:0>5}_{found_x}_{found_y}.jpg"
        else:
            output_name = ""

        if output_name:
            cv2.imwrite(os.path.join("mock_matches", test_name, output_name), raw_minimap)


if __name__ == "__main__":
    VIDEO_FILES = [r'E:\Movies\OBS\2017-12-09_20-04-41.mp4']

    for video in VIDEO_FILES:
        generate_test_minimaps(video)
