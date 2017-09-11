import argparse
import os

import cv2
import numpy as np

from pubgis.pubgis_match import PUBGISMatch

J = 106
K = 107
L = 108


def generate_test_minimaps(video_file):
    video_name = os.path.splitext(os.path.basename(video_file))[0]
    match = PUBGISMatch(video_file=video_file,
                        debug=True,
                        step_interval=10,
                        start_delay=60)

    for frames, minimap in match.minimap_iterator():
        raw_minimap = np.copy(minimap)
        match_found, coords, _, _, _, _ = match.template_match((None, minimap))
        x, y = coords
        key = cv2.waitKey(-1)

        if key == J:
            cv2.imwrite(os.path.join('bad', f"{video_name}_{frames}.jpg"), raw_minimap)
        elif key == K:
            cv2.imwrite(os.path.join('good', f"{video_name}_{frames}_0_0.jpg"), raw_minimap)
        elif key == L:
            cv2.imwrite(os.path.join('good', f"{video_name}_{frames}_{x}_{y}.jpg"), raw_minimap)
        else:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('video_files', nargs='+')
    args = parser.parse_args()

    for video in args.video_files:
        generate_test_minimaps(video)
