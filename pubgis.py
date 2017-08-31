import cv2
import numpy as np
from matplotlib import pyplot as plt
import argparse
import os
from tqdm import tqdm
from enum import IntFlag

DEFAULT_MAP = "full_map_scaled.jpg"
DEFAULT_INDICATOR_MASK = "player_indicator_mask.jpg"
DEFAULT_OUTPUT_FILE = "{}_path.jpg"

DEFAULT_TEMP_MATCH_THRESHOLD = 10000000

DEFAULT_START_DELAY = 10  # seconds
DEFAULT_TIME_STEP = 1  # seconds

CROP_BORDER = 30

MAX_SPEED = 130  # km/h, motorcycle
PIXELS_PER_100M = 64
PIXELS_PER_KM = PIXELS_PER_100M * 10
MAX_PIXELS_PER_H = MAX_SPEED * PIXELS_PER_KM
MAX_PIXELS_PER_SEC = MAX_PIXELS_PER_H / 3600

PATH_WIDTH = 8
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
    FAILED_IND_COLOR = 1
    FAILED_THRESHOLD = 2


class PUBGIS:
    def __init__(self,
                 video_file=None,
                 full_map_file=DEFAULT_MAP,
                 mask_file=DEFAULT_INDICATOR_MASK,
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
    def markup_minimap_debug(minimap, max_val, ind_in_range, ind_color):
        text_color = MATCH_COLOR if max_val > DEFAULT_TEMP_MATCH_THRESHOLD else NO_MATCH_COLOR
        rect_color = MATCH_COLOR if ind_in_range else NO_MATCH_COLOR

        blue, green, red, _ = tuple(map(int, ind_color))

        cv2.rectangle(minimap, (200, 200), (250, 250), ind_color, thickness=-1)
        cv2.rectangle(minimap, (200, 200), (250, 250), rect_color, thickness=2)
        cv2.putText(minimap, '{:>12}'.format(int(max_val)), (20, 50), DEFAULT_FONT, DEBUG_FONT_SIZE, text_color)
        cv2.putText(minimap, f'{blue}', (208, 212), DEFAULT_FONT, 0.3, (0, 0, 0))
        cv2.putText(minimap, f'{green}', (208, 227), DEFAULT_FONT, 0.3, (0, 0, 0))
        cv2.putText(minimap, f'{red}', (208, 242), DEFAULT_FONT, 0.3, (0, 0, 0))

        return minimap

    def template_match(self,
                       minimap,
                       last_coords=None,
                       ind_min_color=DEFAULT_IND_COLOR_MIN,
                       ind_max_color=DEFAULT_IND_COLOR_MAX,
                       template_threshold=DEFAULT_TEMP_MATCH_THRESHOLD,
                       method=cv2.TM_SQDIFF):
        match_found = MatchResult.SUCCESFUL

        ind_color = cv2.mean(minimap, self.indicator_mask)
        ind_in_range = all(ind_min < color < ind_max for ind_min, color, ind_max in
                           zip(ind_min_color, ind_color, ind_max_color))

        gray_minimap = cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY)
        h, w = gray_minimap.shape

        # apply template matching to find most likely minimap location on the entire map
        if last_coords:
            last_x, last_y = last_coords
            min_x = last_x - w - int(MAX_PIXELS_PER_SEC * self.step_time)
            max_x = last_x + w + int(MAX_PIXELS_PER_SEC * self.step_time)
            min_y = last_y - h - int(MAX_PIXELS_PER_SEC * self.step_time)
            max_y = last_y + h + int(MAX_PIXELS_PER_SEC * self.step_time)

            res = cv2.matchTemplate(self.gray_full_map[min_y:max_y, min_x:max_x],
                                    gray_minimap,
                                    cv2.TM_CCOEFF)
            _, match_val, _, (trim_x, trim_y) = cv2.minMaxLoc(res)

            y = min_y + trim_y
            x = min_x + trim_x
        else:
            res = cv2.matchTemplate(self.gray_full_map, gray_minimap, method)

            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                match_val, _, (x, y), _ = cv2.minMaxLoc(res)
            else:
                _, match_val, _, (x, y) = cv2.minMaxLoc(res)

        if match_val < template_threshold:
            match_found |= MatchResult.FAILED_THRESHOLD

        if not ind_in_range:
            match_found |= MatchResult.FAILED_IND_COLOR

        if self.debug:
            cv2.imshow("debug minimap", self.markup_minimap_debug(minimap, match_val, ind_in_range, ind_color))
            if match_found == MatchResult.SUCCESFUL:
                cv2.imshow("matched area", self.full_map[y:y + h, x:x + w])
            cv2.waitKey(10)

        return match_found, (x + w // 2, y + h // 2)

    def video_iterator(self, return_frames=False):
        frame_count = 0
        # noinspection PyArgumentList
        cap = cv2.VideoCapture(self.video_file)
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
        last_coords = None

        for frame_count, minimap in self.video_iterator():
            match_found, coords = self.template_match((frame_count, minimap), last_coords=last_coords)
            if match_found == MatchResult.SUCCESFUL:
                self.all_coords.append(coords)
                if last_coords is not None:
                    cv2.line(self.output_map, last_coords, coords, MATCH_COLOR, thickness=PATH_WIDTH)
                last_coords = coords

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
    parser.add_argument('--color', default=MATCH_COLOR, help="Must be either an html hex string e.x. '#eeefff' or a "
                                                             "legal html name like ‘red’, ‘chartreuse’, etc.")
    parser.add_argument('--debug', action='store_true')
    pubgis = PUBGIS(**vars(parser.parse_args()))

    pubgis.process_match()
