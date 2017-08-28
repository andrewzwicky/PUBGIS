import cv2
import multiprocessing
from pubgis import template_match_minimap, template_match_minimap_wrapper, video_iterator, markup_image_debug
from pubgis import MATCH_COLOR, NO_MATCH_COLOR, TRAIL_SIZE, CROP_BORDER, FONT
import itertools

START_SKIP = 32000
SKIP = 60
GOOD = 103

full_map_file = r"Erangel_Minimap_scaled.jpg"
player_indicator_mask_file = r"circle_mask.jpg"

players = ["breaK", "aimpr", "viss", "smak"]

videos = {"breaK": "E:\Movies\OBS\gamescom_squads_g1_tsm_break.mkv",
          "aimpr": "E:\Movies\OBS\gamescom_squads_g1_tsm_aimpr.mkv",
          "viss": "E:\Movies\OBS\gamescom_squads_g1_tsm_viss.mkv",
          "smak": "E:\Movies\OBS\gamescom_squads_g1_tsm_smak.mkv"}

plane_start_frames = {"breaK": 610,
                      "aimpr": 560,
                      "viss": 585,
                      "smak": 585}

jump_frames = {"breaK": 1850,
               "aimpr": 1790,
               "viss": 1790,
               "smak": 1790}

landing_frames = {"breaK": 5000,
                  "aimpr": 5270,
                  "viss": 4970,
                  "smak": 5270}

death_frames = {"breaK": 53000,
                "aimpr": 54400,
                "viss": 34000,
                "smak": 52500}

colors = {"breaK": (255, 255, 255),
          "aimpr": (255, 0, 0),
          "viss": (0, 255, 0),
          "smak": (0, 0, 255)}


def process_match():
    last_coords = {player: None for player in players}

    full_map = cv2.imread(full_map_file)
    player_indicator_mask = cv2.imread(player_indicator_mask_file, 0)
    gray_map = cv2.cvtColor(full_map, cv2.COLOR_RGB2GRAY)

    for minimaps in itertools.zip_longest(
            *[video_iterator(videos[player], plane_start_frames[player], SKIP) for player in players], fillvalue=(0, None)):
        for player, (frame_count, minimap) in zip(players, minimaps):
            if death_frames[player] >= frame_count >= landing_frames[player]:
                match_found, max_val, coords, ind_color, ind_in_range, minimap = template_match_minimap(
                    (frame_count, minimap), gray_map, player_indicator_mask)

                if match_found:
                    if last_coords[player] is not None:
                        cv2.line(full_map, last_coords[player], coords, colors[player], thickness=TRAIL_SIZE)
                    last_coords[player] = coords

                    # debug_minimap = markup_image_debug(minimap, max_val, ind_in_range, ind_color)
                    # cv2.imshow(player, debug_minimap)

        cv2.imshow("map", cv2.resize(full_map, (0, 0), fx=0.2, fy=0.2))
        cv2.waitKey(10)

    cv2.imwrite("squads_map_path.jpg", full_map)


def find_delays():
    for player, video in videos.items():
        total = 0
        found = False
        cap = cv2.VideoCapture(video)

        # skip the first frames (plane, etc.)
        for i in range(START_SKIP):
            cap.grab()
        total += START_SKIP

        while not found:
            ret, frame = cap.read()
            if frame is None:
                break
            else:
                cv2.putText(frame, str(total), (50, 50), FONT, 0.5, MATCH_COLOR)
                cv2.imshow("start", cv2.resize(frame, (0, 0), fx=0.5, fy=0.5))
                key = cv2.waitKey(-1)
                if key == GOOD:
                    print(player, total)
                    found = True
                else:
                    pass
                for i in range(SKIP):
                    cap.grab()
                total += SKIP


if __name__ == "__main__":
    process_match()
