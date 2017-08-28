import cv2
import multiprocessing
import itertools

TEMPLATE_THRESHOLD = 15000000
START_SKIP = 2000
SKIP = 30

CROP_BORDER = 30

TRAIL_SIZE = 8
TRAIL_ALPHA = 0.6

FONT = cv2.FONT_HERSHEY_SIMPLEX

NO_MATCH_COLOR = (0, 0, 255)
MATCH_COLOR = (0, 255, 0)

IND_MIN = [130, 150, 150]
IND_MAX = [225, 225, 225]


def template_match_minimap_wrapper(args):
    return template_match_minimap(*args)


def template_match_minimap(frame_minimap, gray_map, player_indicator_mask):
    frame, minimap = frame_minimap
    match_found = False

    ind_color = cv2.mean(minimap, player_indicator_mask)
    ind_in_range = all(ind_min < color < ind_max for ind_min, color, ind_max in zip(IND_MIN, ind_color, IND_MAX))

    gray_minimap = cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY)

    w, h = gray_minimap.shape[::-1]

    # apply template matching to find most likely minimap location
    # on the entire map
    res = cv2.matchTemplate(gray_map, gray_minimap, cv2.TM_CCOEFF)
    _, max_val, _, (max_y, max_x) = cv2.minMaxLoc(res)

    if max_val > TEMPLATE_THRESHOLD and ind_in_range:
        match_found = True

    return match_found, max_val, (max_y + h // 2, max_x + w // 2), ind_color, ind_in_range, minimap


def video_iterator(video_file, start_delay, skip):
    frame_count = 0
    cap = cv2.VideoCapture(video_file)

    # skip the first frames (plane, etc.)
    for i in range(start_delay):
        cap.grab()
    frame_count += start_delay

    while True:
        ret, frame = cap.read()
        if frame is None:
            break
        else:
            if frame.shape == (720, 1280, 3):
                minimap = frame[532:700, 1087:1255]
            elif frame.shape == (1080, 1920, 3):
                minimap = frame[798:1051, 1630:1882]
            else:
                raise ValueError
            yield frame_count, minimap
            for i in range(skip):
                cap.grab()
            frame_count += skip


def markup_image_debug(minimap, max_val, ind_in_range, ind_color):
    if max_val > TEMPLATE_THRESHOLD:
        text_color = MATCH_COLOR
    else:
        text_color = NO_MATCH_COLOR

    if ind_in_range:
        rect_color = MATCH_COLOR
    else:
        rect_color = NO_MATCH_COLOR

    b, g, r, _ = tuple(map(int, ind_color))

    cv2.rectangle(minimap, (200, 200), (250, 250), ind_color, thickness=-1)
    cv2.rectangle(minimap, (200, 200), (250, 250), rect_color, thickness=2)
    cv2.putText(minimap, '{:>12}'.format(int(max_val)), (50, 50), FONT, 3, text_color)
    cv2.putText(minimap, f'{b}', (208, 212), FONT, 0.3, (0, 0, 0))
    cv2.putText(minimap, f'{g}', (208, 227), FONT, 0.3, (0, 0, 0))
    cv2.putText(minimap, f'{r}', (208, 242), FONT, 0.3, (0, 0, 0))

    return minimap


def process_match(video_file, full_map_file, player_indicator_mask_file):
    full_map = cv2.imread(full_map_file)
    player_indicator_mask = cv2.imread(player_indicator_mask_file, 0)
    gray_map = cv2.cvtColor(full_map, cv2.COLOR_RGB2GRAY)

    p = multiprocessing.Pool(3)

    last_coords = None
    min_x = max_x = min_y = max_y = None

    for match_found,\
        max_val,\
        coords,\
        ind_color,\
        ind_in_range,\
        minimap in p.imap(template_match_minimap_wrapper,
                          zip(video_iterator(video_file, START_SKIP, SKIP),
                              itertools.repeat(gray_map),
                              itertools.repeat(player_indicator_mask))):

        if match_found:
            # trail_color = MATCH_COLOR
            if last_coords is not None:
                cv2.line(full_map, last_coords, coords, MATCH_COLOR, thickness=TRAIL_SIZE)
            last_coords = coords

            x, y = coords

            if min_x is None or x < min_x:
                min_x = x
            if max_x is None or x > max_x:
                max_x = x
            if min_y is None or y < min_y:
                min_y = y
            if max_y is None or y > max_y:
                max_y = y
        else:
            # trail_color = NO_MATCH_COLOR
            pass

        debug_minimap = markup_image_debug(minimap, max_val, ind_in_range, ind_color)
        # cv2.circle(full_map, coords, TRAIL_SIZE, trail_color, -1)

        cv2.imshow("mini", debug_minimap)
        if max_x is not None:
            cropped_map = full_map[min_y-CROP_BORDER:max_y+CROP_BORDER,
                                   min_x-CROP_BORDER:max_x+CROP_BORDER]
            cv2.imshow("map", cropped_map)
        cv2.waitKey(10)

    cv2.imwrite("map_path.jpg", full_map)
