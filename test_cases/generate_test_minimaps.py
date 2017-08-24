import os
import cv2

TEMPLATE_THRESHOLD = 22000000
# no start skip to get failing images on purpose
START_SKIP = 0
# less frequent for test cases
SKIP = 300


def generate_minimap_captures(video_file):
    cap = cv2.VideoCapture(video_file)

    # skip the first frames (plane, etc.)
    frame_num = START_SKIP
    for i in range(START_SKIP):
        cap.grab()

    ret, frame = cap.read()

    while frame is not None:

        minimap = frame[798:1051, 1630:1882]

        base = os.path.basename(video_file)
        cv2.imwrite("{}_{}.jpg".format(os.path.splitext(base)[0], frame_num), minimap)

        for i in range(SKIP):
            cap.grab()
        frame_num += SKIP
        ret, frame = cap.read()

REC_FOLDER = r"E:\Movies\OBS"

for video in ["2017-08-03 17-58-17.mkv",
              "2017-08-03 17-29-40.mkv"]:
    generate_minimap_captures(os.path.join(REC_FOLDER, video))
