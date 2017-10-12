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

    for i, (_, minimap) in enumerate(video_iter):
        raw_minimap = np.copy(minimap)
        scaled_map_pos, color_diff, result = match.find_scaled_player_position(minimap)
        if scaled_map_pos:
            found_x, found_y = unscale_coords(scaled_map_pos, match.scale)
        key = cv2.waitKey(-1)

        if key == J:
            cv2.imwrite(os.path.join('water_test', f"{video_name}_{i:0>4}.jpg"), raw_minimap)
        elif key == K:
            cv2.imwrite(os.path.join('water_test', f"{video_name}_{i:0>4}_0_0.jpg"), raw_minimap)
        elif key == L:
            cv2.imwrite(os.path.join('water_test', f"{video_name}_{i:0>4}_{found_x}_{found_y}.jpg"),
                        raw_minimap)
            match.last_scaled_position = scaled_map_pos
        else:
            pass


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('video_files', nargs='+')
    ARGS = PARSER.parse_args()

    for video in ARGS.video_files:
        generate_test_minimaps(video)
