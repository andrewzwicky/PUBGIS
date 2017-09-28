import argparse
import os

import cv2
import numpy as np

from pubgis.minimap_iterators.video import VideoIterator
from pubgis.match import PUBGISMatch

J = 106
K = 107
L = 108


def generate_test_minimaps(video_file):
    video_name = os.path.splitext(os.path.basename(video_file))[0]
    video_iter = VideoIterator(video_file=video_file)
    match = PUBGISMatch()

    for i, (_, minimap) in enumerate(video_iter):
        raw_minimap = np.copy(minimap)
        _, coords, _, _ = match.find_map_section(minimap, debug=True)
        found_x, found_y = coords
        key = cv2.waitKey(-1)

        if key == J:
            cv2.imwrite(os.path.join('bad', f"{video_name}_{i}.jpg"), raw_minimap)
        elif key == K:
            cv2.imwrite(os.path.join('good', f"{video_name}_{i}_0_0.jpg"), raw_minimap)
        elif key == L:
            cv2.imwrite(os.path.join('good', f"{video_name}_{i}_{found_x}_{found_y}.jpg"),
                        raw_minimap)
        else:
            pass


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('video_files', nargs='+')
    ARGS = PARSER.parse_args()

    for video in ARGS.video_files:
        generate_test_minimaps(video)
