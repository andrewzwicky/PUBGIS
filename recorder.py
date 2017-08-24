import cv2
import numpy as np

TEMPLATE_THRESHOLD = 20000000
START_SKIP = 2000
SKIP = 120

TRAIL_SIZE = 5

FONT = cv2.FONT_HERSHEY_SIMPLEX

NO_MATCH_COLOR = (0, 0, 255)
MATCH_COLOR = (0, 255, 0)

IND_MIN = [155, 155, 155]
IND_MAX = [220, 220, 220]

def template_match_minimap(minimap, gray_map, player_indicator_mask):
    player_indicator_color = cv2.mean(minimap, player_indicator_mask)
    ind_in_range = all(ind_min < color < ind_max for ind_min, color, ind_max in zip(IND_MIN, ind_color, IND_MAX))

    if ind_in_range:

    gray_minimap = cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY)

    w, h = gray_minimap.shape[::-1]

    # apply template matching to find most likely minimap location
    # on the entire map
    res = cv2.matchTemplate(gray_map, gray_minimap, cv2.TM_CCOEFF)
    _, max_val, _, (max_y, max_x) = cv2.minMaxLoc(res)


    return max_val, (max_y + h // 2, max_x + w // 2), player_indicator_color



def process_match(video_file, full_map_file, player_indicator_mask_file):
    full_map = cv2.imread(full_map_file)
    player_indicator_mask = cv2.imread(player_indicator_mask_file, 0)
    gray_map = cv2.cvtColor(full_map, cv2.COLOR_RGB2GRAY)
    cap = cv2.VideoCapture(video_file)

    # skip the first frames (plane, etc.)
    for i in range(START_SKIP):
        cap.grab()

    ret, frame = cap.read()

    while frame is not None:
        if frame.shape == (720, 1280, 3):
            minimap = frame[532:700, 1087:1255]
        elif frame.shape == (1080, 1920, 3):
            minimap = frame[798:1051, 1630:1882]
        else:
            raise ValueError

        max_val, coords, ind_color = template_match(minimap, gray_map, player_indicator_mask)

        if max_val < TEMPLATE_THRESHOLD:
            text_color = NO_MATCH_COLOR
        else:
            text_color = MATCH_COLOR

        ind_in_range = all(ind_min < color < ind_max for ind_min, color, ind_max in zip(IND_MIN, ind_color, IND_MAX))

        cv2.rectangle(minimap, (200, 200), (250, 250), ind_color, thickness=-1)

        if ind_in_range:
            cv2.rectangle(minimap, (200, 200), (250, 250), MATCH_COLOR, thickness=2)
        else:
            cv2.rectangle(minimap, (200, 200), (250, 250), NO_MATCH_COLOR, thickness=2)

        if max_val > TEMPLATE_THRESHOLD and ind_in_range:
            cv2.circle(full_map, coords, TRAIL_SIZE, MATCH_COLOR, -1)
        else:
            cv2.circle(full_map, coords, TRAIL_SIZE, NO_MATCH_COLOR, -1)

        print(int(max_val), coords, tuple(map(int,ind_color)))

        cv2.putText(minimap, '{:>12}'.format(int(max_val)), (50, 50), FONT, 0.5, text_color)

        cv2.imshow("mini", minimap)
        cv2.imshow("map", cv2.resize(full_map, (0, 0), fx=0.2, fy=0.2))
        cv2.waitKey(10)

        for i in range(SKIP):
            cap.grab()

        ret, frame = cap.read()

    cv2.imwrite("map_path.jpg", full_map)
