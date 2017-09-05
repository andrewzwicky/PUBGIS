import cv2
import os
import argparse
from pubgis import PUBGISMatch
import numpy as np

J = 106
K = 107
L = 108

# no start skip to get failing images on purpose
GENERATE_START_DELAY = 395
# less frequent for test cases
GENERATE_STEP_TIME = 0.25  # seconds


# generated from movies:
# E:\Movies\OBS\shroud_2.mp4
# E:\Movies\OBS\shroud_1.mp4
# E:\Movies\OBS\duos_dinner_pat_groza.mp4
# E:\Movies\OBS\gamescom_squads_g1_tsm_viss.mp4
# E:\Movies\OBS\gamescom_squads_g1_tsm_smak.mp4


def generate_test_minimaps(video_file):
    video_name = os.path.splitext(os.path.basename(video_file))[0]
    match = PUBGISMatch(video_file=video_file,
                        start_delay=GENERATE_START_DELAY,
                        step_time=GENERATE_STEP_TIME,
                        debug=True)

    for frame_count, minimap in match.video_iterator():
        raw_minimap = np.copy(minimap)
        match_found, coords, _, _, _, _ = match.template_match(minimap)
        x, y = coords
        key = cv2.waitKey(-1)

        if key == J:
            cv2.imwrite(os.path.join('bad', f"{video_name}_{frame_count}.jpg"), raw_minimap)
        elif key == K:
            cv2.imwrite(os.path.join('good', f"{video_name}_{frame_count}_0_0.jpg"), raw_minimap)
        elif key == L:
            cv2.imwrite(os.path.join('good', f"{video_name}_{frame_count}_{x}_{y}.jpg"), raw_minimap)
        else:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('video_files', nargs='+')
    args = parser.parse_args()

    for video in args.video_files:
        generate_test_minimaps(video)
