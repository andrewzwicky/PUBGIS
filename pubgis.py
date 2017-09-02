import cv2
import numpy as np
from matplotlib import pyplot as plt
from multiprocessing import Pool
import argparse
import os
from math import sqrt
from tqdm import tqdm
from enum import IntFlag

DEFAULT_MAP = "full_map_scaled.jpg"
DEFAULT_INDICATOR_MASK = "player_indicator_mask.jpg"
DEFAULT_INDICATOR_AREA_MASK = "player_indicator_area_mask.jpg"
DEFAULT_OUTPUT_FILE = "{}_path.jpg"

DEFAULT_START_DELAY = 10  # seconds
DEFAULT_TIME_STEP = 1  # seconds

CROP_BORDER = 30

MAX_SPEED = 130  # km/h, motorcycle
PIXELS_PER_100M = 64
PIXELS_PER_KM = PIXELS_PER_100M * 10
MAX_PIXELS_PER_H = MAX_SPEED * PIXELS_PER_KM
MAX_PIXELS_PER_SEC = MAX_PIXELS_PER_H / 3600

COLOR_DIFF_THRESHOLD = 95  # basically a guess until I get more test cases

PATH_WIDTH = 4
PATH_ALPHA = 0.7

DEFAULT_FONT = cv2.FONT_HERSHEY_SIMPLEX
DEBUG_FONT_SIZE = 0.75

NO_MATCH_COLOR = (0, 0, 255)
MATCH_COLOR = (0, 255, 0)

DEFAULT_IND_COLOR_MIN = [120, 145, 140]
DEFAULT_IND_COLOR_MAX = [225, 225, 225]


# when indexing an image the format is image[y,x]
# but coords are passed as (x,y)

class MatchResult(IntFlag):
    SUCCESFUL = 0
    WRONG_IND_COLOR = 1
    COLOR_DIFF = 2


class PUBGIS:
    def __init__(self,
                 video_file=None,
                 full_map_file=DEFAULT_MAP,
                 mask_file=DEFAULT_INDICATOR_MASK,
                 area_mask_file=DEFAULT_INDICATOR_AREA_MASK,
                 start_delay=DEFAULT_START_DELAY,
                 step_time=DEFAULT_TIME_STEP,
                 death_time=None,
                 output_file=None,
                 color=MATCH_COLOR,
                 debug=False):
        self.video_file = video_file
        self.full_map = cv2.imread(full_map_file)
        self.output_map = np.copy(self.full_map)
        _, self.indicator_mask = cv2.threshold(cv2.imread(mask_file, 0), 10, 255, cv2.THRESH_BINARY)
        _, self.indicator_area_mask = cv2.threshold(cv2.imread(area_mask_file, 0), 10, 255, cv2.THRESH_BINARY)
        self.gray_full_map = cv2.cvtColor(self.full_map, cv2.COLOR_BGR2GRAY)
        self.start_delay = start_delay
        self.step_time = step_time
        self.death_time = death_time
        self.debug = debug
        if output_file is None:
            self.output_file = DEFAULT_OUTPUT_FILE.format("match_path.jpg")
        else:
            video_name = os.path.splitext(video_file)[0]
            self.output_file = DEFAULT_OUTPUT_FILE.format(video_name)
        self.color = color
        self.full_map_h, self.full_map_w = self.gray_full_map.shape
        self.all_coords = []

    @staticmethod
    def markup_minimap_debug(minimap, ind_in_range, ind_color, ind_area_color, color_diff):
        ind_rect_loc_UL = (200, 200)
        ind_rect_area_loc_UL = (120, 200)
        rect_size = 50
        text_inset = (8, 15)
        test_spacing = 15

        cv2.putText(minimap, f"{color_diff}", (25, 25), DEFAULT_FONT, 0.3, MATCH_COLOR)

        rect_color = MATCH_COLOR if ind_in_range else NO_MATCH_COLOR

        blue, green, red, _ = tuple(map(int, ind_color))

        cv2.rectangle(minimap, ind_rect_loc_UL, tuple(c+rect_size for c in ind_rect_loc_UL), ind_color, thickness=-1)
        cv2.rectangle(minimap, ind_rect_loc_UL, tuple(c+rect_size for c in ind_rect_loc_UL), rect_color, thickness=2)
        for i, color in enumerate([blue, green, red]):
            x = ind_rect_loc_UL[0] + text_inset[0]
            y = ind_rect_loc_UL[1] + text_inset[1] + i*test_spacing
            cv2.putText(minimap, f'{color}', (x, y), DEFAULT_FONT, 0.3, (0, 0, 0))

        blue, green, red, _ = tuple(map(int, ind_area_color))

        cv2.rectangle(minimap, ind_rect_area_loc_UL, tuple(c+rect_size for c in ind_rect_area_loc_UL), ind_area_color, thickness=-1)
        cv2.rectangle(minimap, ind_rect_area_loc_UL, tuple(c+rect_size for c in ind_rect_area_loc_UL), rect_color, thickness=2)
        for i, color in enumerate([blue, green, red]):
            x = ind_rect_area_loc_UL[0] + text_inset[0]
            y = ind_rect_area_loc_UL[1] + text_inset[1] + i*test_spacing
            cv2.putText(minimap, f'{color}', (x, y), DEFAULT_FONT, 0.3, (0, 0, 0))

        return minimap

    def template_match(self,
                       minimap,
                       ind_min_color=DEFAULT_IND_COLOR_MIN,
                       ind_max_color=DEFAULT_IND_COLOR_MAX,
                       method=cv2.TM_CCOEFF_NORMED):
        match_found = MatchResult.SUCCESFUL

        ind_color = cv2.mean(minimap, self.indicator_mask)
        ind_in_range = all(ind_min < color < ind_max for ind_min, color, ind_max in
                           zip(ind_min_color, ind_color, ind_max_color))

        ind_area_color = cv2.mean(minimap, self.indicator_area_mask)
        color_diff = sqrt(sum([(c1-c2)**2 for c1, c2 in zip(ind_color, ind_area_color)]))

        gray_minimap = cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY)
        h, w = gray_minimap.shape

        res = cv2.matchTemplate(self.gray_full_map, gray_minimap, method)

        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            _, _, (x, y), _ = cv2.minMaxLoc(res)
        else:
            _, _, _, (x, y) = cv2.minMaxLoc(res)

        if not ind_in_range:
            match_found |= MatchResult.WRONG_IND_COLOR

        if not color_diff > COLOR_DIFF_THRESHOLD:
            match_found |= MatchResult.COLOR_DIFF

        if self.debug:
            cv2.imshow("debug", np.concatenate((self.markup_minimap_debug(minimap,
                                                                          ind_in_range,
                                                                          ind_color,
                                                                          ind_area_color,
                                                                          color_diff),
                                                self.full_map[y:y + h, x:x + w]),
                                               axis=1))
            cv2.waitKey(10)

        return match_found, (x + w // 2, y + h // 2)

    def video_iterator(self, return_frames=False):
        frame_count = 0
        # noinspection PyArgumentList
        if os.path.isfile(self.video_file):
                cap = cv2.VideoCapture(self.video_file)
        else:
            raise FileNotFoundError("{} cannot be found".format(self.video_file))

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        start_delay_frames = int(self.start_delay * fps)
        # need to at least increment by 1 each iteration
        time_step_frames = max(int(self.step_time * fps), 1)
        death_frame = int(self.death_time * fps) if self.death_time is not None else total_frames

        pbar = tqdm(total=death_frame)

        # skip the first frames (plane, etc.)
        for i in range(start_delay_frames):
            cap.grab()
        frame_count += start_delay_frames
        pbar.update(start_delay_frames)

        while True and frame_count <= death_frame:
            ret, frame = cap.read()
            if frame is None:
                break
            else:
                if frame.shape == (1080, 1920, 3):
                    minimap_min_y = 798
                    minimap_max_y = 1051
                    minimap_min_x = 1630
                    minimap_max_x = 1882
                else:
                    raise ValueError

                minimap = frame[minimap_min_y:minimap_max_y, minimap_min_x:minimap_max_x]

                if return_frames:
                    yield frame_count, minimap
                else:
                    yield minimap
                for i in range(time_step_frames):
                    cap.grab()
                frame_count += time_step_frames
                pbar.update(time_step_frames)

        pbar.close()

    def find_path_bounds(self):
        if self.all_coords:
            xs, ys = zip(*self.all_coords)
            return (min(ys) - CROP_BORDER,
                    max(ys) + CROP_BORDER,
                    min(xs) - CROP_BORDER,
                    max(xs) + CROP_BORDER)
        else:
            return (0,
                    self.full_map_h,
                    0,
                    self.full_map_w)

    def process_match(self):
        p = Pool(1)

        for match_found, coords in p.imap(self.template_match, self.video_iterator()):
            if match_found == MatchResult.SUCCESFUL:
                try:
                    cv2.line(self.output_map,
                             self.all_coords[-1],
                             coords,
                             MATCH_COLOR,
                             thickness=PATH_WIDTH,
                             lineType=cv2.LINE_AA)

                    l_x, l_y = self.all_coords[-1]
                    x, y = coords

                    travel_dist = sqrt((x-l_x)**2 + (l_y - y)**2)

                    if travel_dist > 2*MAX_PIXELS_PER_SEC:
                        print(coords)

                except IndexError:
                    pass

                if self.debug:
                    min_y, max_y, min_x, max_x = self.find_path_bounds()

                    max_size = 900
                    biggest = max(max_size, max_x - min_x, max_y - min_y)
                    scale = max_size / biggest

                    cv2.imshow("debug map", cv2.resize(self.output_map[min_y:max_y, min_x:max_x],
                                                       (0, 0),
                                                       fx=scale,
                                                       fy=scale))
                    cv2.waitKey(10)

                self.all_coords.append(coords)

        self.create_output()

    def create_output(self):
        fig, ax = plt.subplots(figsize=(20, 20))
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        ax.axes.xaxis.set_visible(False)
        ax.axes.yaxis.set_visible(False)
        ax.imshow(cv2.cvtColor(self.full_map, cv2.COLOR_BGR2RGB))
        min_y, max_y, min_x, max_x = self.find_path_bounds()
        ax.axes.set_xlim(min_x, max_x)
        ax.axes.set_ylim(max_y, min_y)
        ax.plot(*zip(*self.all_coords), color=self.color, linewidth=PATH_WIDTH, alpha=PATH_ALPHA)
        fig.savefig(self.output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--video_file', required=True)
    parser.add_argument('--full_map_file', default=DEFAULT_MAP)
    parser.add_argument('--death_time', type=int, default=None)
    parser.add_argument('--mask_file', default=DEFAULT_INDICATOR_MASK)
    parser.add_argument('--start_delay', type=int, default=DEFAULT_START_DELAY)
    parser.add_argument('--step_time', type=int, default=DEFAULT_TIME_STEP)
    parser.add_argument('--output_file', default=None)
    parser.add_argument('--color', default='Lime', help="Must be either an html hex string e.x. '#eeefff' or a "
                                                         "legal html name like ‘red’, ‘chartreuse’, etc.")
    parser.add_argument('--debug', action='store_true')
    pubgis = PUBGIS(**vars(parser.parse_args()))

    pubgis.process_match()
