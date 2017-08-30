from multiprocessing import Pool
import cv2
import os
import argparse
from pubgis import PUBGIS

G = 103
B = 98

# no start skip to get failing images on purpose
GENERATE_START_DELAY = 0
# less frequent for test cases
GENERATE_STEP_TIME = 30  # seconds


def generate_test_minimaps(video_file):
    video_name = os.path.splitext(video_file)[0]
    match = PUBGIS(video_file=video_file,
                   start_delay=GENERATE_START_DELAY,
                   step_time=GENERATE_STEP_TIME)

    for frame_count, minimap in match.video_iterator():
        coords_str = ""
        cv2.imshow("test image", minimap)
        key = cv2.waitKey(-1)
        if key == G:
            match_found, (x, y), debug_minimap = match.template_match_minimap((None, minimap))
            if match_found:
                w, h = minimap.shape[::-1]
                cv2.imshow("match", match.full_map[y - (h // 2):y + (h // 2), x - (w // 2):x + (h // 2)])
                key = cv2.waitKey(-1)
                if key == G:
                    coords_str = f"_{x}_{y}"
            cv2.imwrite(os.path.join('good', f"{video_name}_{frame_count}{coords_str}.jpg"), minimap)
        elif key == B:
            cv2.imwrite(os.path.join('bad', f"{video_name}_{frame_count}.jpg"), minimap)
        else:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('video_files', nargs='+')
    args = parser.parse_args()

    p = Pool(3)
    p.map(generate_test_minimaps, args.video_files)
