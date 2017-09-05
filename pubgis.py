import cv2
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import to_rgb
from multiprocessing import Pool
import argparse
import os
from math import sqrt, ceil
from pubgis_match_result import MatchResult
from typing import Sequence, Optional

Color = Sequence[int]

MAP_FILE = "full_map_scaled.jpg"
INDICATOR_MASK_FILE = "player_indicator_mask.jpg"
INDICATOR_AREA_MASK_FILE = "player_indicator_area_mask.jpg"
DEFAULT_OUTPUT_FILE = "{}_path.jpg"

DEFAULT_START_DELAY = 10  # seconds
DEFAULT_TIME_STEP = 1  # seconds

CROP_BORDER = 30

MAX_SPEED = 130  # km/h, motorcycle
PIXELS_PER_100M = 64
PIXELS_PER_KM = PIXELS_PER_100M * 10
MAX_PIXELS_PER_H = MAX_SPEED * PIXELS_PER_KM
MAX_PIXELS_PER_SEC = MAX_PIXELS_PER_H / 3600

M = -.009
B = 1.62

COLOR_DIFF_THRESHOLD = 100  # basically a guess until I get more test cases
TEMPLATE_MATCH_THRESHOLD = .45  # basically a guess until I get more test cases

PATH_WIDTH = 4
PATH_ALPHA = 0.7

MIN_PROGRESS_MAP_SIZE = 600

DEFAULT_FONT = cv2.FONT_HERSHEY_SIMPLEX
DEBUG_FONT_SIZE_BIG = 0.6
DEBUG_FONT_SIZE_SMALL = 0.3

NO_MATCH_COLOR = (0, 0, 255)
MATCH_COLOR = (0, 255, 0)

DEFAULT_PATH_COLOR = (208, 224, 64)

IND_COLOR_MIN = (120, 145, 140)
IND_COLOR_MAX = (225, 225, 225)


# when indexing an image the format is image[y,x]
# but coords are passed as (x,y)


class PUBGISMatch:
    def __init__(self,
                 video_file: str = None,
                 start_delay: float = DEFAULT_START_DELAY,
                 step_time: float = DEFAULT_TIME_STEP,
                 death_time: Optional[int] = None,
                 output_file: Optional[int] = None,
                 path_color: Color = DEFAULT_PATH_COLOR,
                 debug: bool = False):
        self.video_file = video_file
        self.full_map = cv2.imread(MAP_FILE)
        self.output_map = np.copy(self.full_map)
        _, self.indicator_mask = cv2.threshold(cv2.imread(INDICATOR_MASK_FILE, 0), 10, 255, cv2.THRESH_BINARY)
        _, self.indicator_area_mask = cv2.threshold(cv2.imread(INDICATOR_AREA_MASK_FILE, 0), 10, 255, cv2.THRESH_BINARY)
        self.gray_full_map = cv2.cvtColor(self.full_map, cv2.COLOR_BGR2GRAY)
        self.start_delay = start_delay
        self.step_time = step_time
        self.death_time = death_time
        self.debug = debug
        if output_file is None:
            video_name = os.path.splitext(video_file)[0]
            self.output_file = DEFAULT_OUTPUT_FILE.format(video_name)

        red, green, blue = to_rgb(path_color)
        self.path_color = [int(c * 255) for c in (blue, green, red)]
        self.full_map_h, self.full_map_w = self.gray_full_map.shape
        self.all_coords = []

    @staticmethod
    def markup_minimap_debug(minimap: np.array,
                             ind_color_ok: bool,
                             ind_color: Color,
                             ind_area_color: Color,
                             color_diff: float,
                             color_diff_ok: bool,
                             match_val: float,
                             match_val_ok: bool) -> np.array:
        ind_rect_corner = (200, 200)
        ind_rect_area_corner = (120, 200)
        rect_size = 50
        text_inset = (8, 15)
        test_spacing = 15

        cv2.putText(minimap, f"{int(color_diff)}", (25, 25), DEFAULT_FONT, DEBUG_FONT_SIZE_BIG,
                    MATCH_COLOR if color_diff_ok else NO_MATCH_COLOR)
        cv2.putText(minimap, f"{match_val:.2f}", (25, 60), DEFAULT_FONT, DEBUG_FONT_SIZE_BIG,
                    MATCH_COLOR if match_val_ok else NO_MATCH_COLOR)

        rect_color = MATCH_COLOR if ind_color_ok else NO_MATCH_COLOR

        blue, green, red, _ = tuple(map(int, ind_color))

        cv2.rectangle(minimap, ind_rect_corner, tuple(c + rect_size for c in ind_rect_corner), ind_color, thickness=-1)
        cv2.rectangle(minimap, ind_rect_corner, tuple(c + rect_size for c in ind_rect_corner), rect_color, thickness=2)
        for i, color in enumerate([blue, green, red]):
            x = ind_rect_corner[0] + text_inset[0]
            y = ind_rect_corner[1] + text_inset[1] + i * test_spacing
            cv2.putText(minimap, f'{color}', (x, y), DEFAULT_FONT, DEBUG_FONT_SIZE_SMALL, (0, 0, 0))

        blue, green, red, _ = tuple(map(int, ind_area_color))

        cv2.rectangle(minimap, ind_rect_area_corner, tuple(c + rect_size for c in ind_rect_area_corner), ind_area_color,
                      thickness=-1)
        for i, color in enumerate([blue, green, red]):
            x = ind_rect_area_corner[0] + text_inset[0]
            y = ind_rect_area_corner[1] + text_inset[1] + i * test_spacing
            cv2.putText(minimap, f'{color}', (x, y), DEFAULT_FONT, DEBUG_FONT_SIZE_SMALL, (0, 0, 0))

        return minimap

    def template_match(self, percent_minimap: tuple):
        """
        
        :param percent_minimap: a tuple consisting of the current percentage progress and the current minimap  
        :return: 
        """
        this_percent, minimap = percent_minimap
        match_found = MatchResult.SUCCESFUL

        gray_minimap = cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY)
        h, w = gray_minimap.shape

        res = cv2.matchTemplate(self.gray_full_map, gray_minimap, cv2.TM_CCOEFF_NORMED)
        _, match_val, _, (x, y) = cv2.minMaxLoc(res)

        coords = (x + w // 2, y + h // 2)

        ind_color = cv2.mean(minimap, self.indicator_mask)
        ind_color_ok = all(ind_min < color < ind_max for ind_min, color, ind_max in
                           zip(IND_COLOR_MIN, ind_color, IND_COLOR_MAX))

        ind_area_color = cv2.mean(minimap, self.indicator_area_mask)
        color_diff = sqrt(sum([(c1 - c2) ** 2 for c1, c2 in zip(ind_color, ind_area_color)]))
        color_diff_ok = color_diff > COLOR_DIFF_THRESHOLD

        match_val_ok = match_val > TEMPLATE_MATCH_THRESHOLD

        if not ind_color_ok:
            match_found |= MatchResult.IND_COLOR

        if not color_diff_ok:
            match_found |= MatchResult.COLOR_DIFF

        if not match_val_ok:
            match_found |= MatchResult.TEMPLATE_THRESHOLD

        if self.debug:
            cv2.imshow("debug", np.concatenate((self.markup_minimap_debug(minimap,
                                                                          ind_color_ok,
                                                                          ind_color,
                                                                          ind_area_color,
                                                                          color_diff,
                                                                          color_diff_ok,
                                                                          match_val,
                                                                          match_val_ok),
                                                self.full_map[y:y + h, x:x + w]),
                                               axis=1))
            cv2.waitKey(10)

        need_y = M * color_diff + B
        if match_val > need_y and ind_color_ok:
            match_found = MatchResult.SUCCESFUL

        return match_found, coords, ind_color, color_diff, match_val, this_percent

    def video_iterator(self):
        """
        Return every time_step minimaps from the supplied video, skipping the first start_delay frames.
        
        :return: iterator that yields (percent, minimap) tuples 
        """
        frame_count = 0

        if os.path.isfile(self.video_file):
            # noinspection PyArgumentList
            cap = cv2.VideoCapture(self.video_file)
        else:
            raise FileNotFoundError("{} cannot be found".format(self.video_file))

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        start_delay_frames = int(self.start_delay * fps)
        # need to at least increment by 1 each iteration
        time_step_frames = max(int(self.step_time * fps), 1)
        death_frame = int(self.death_time * fps) if self.death_time is not None else total_frames

        frames_to_process = death_frame - start_delay_frames

        finished = False

        # skip the first frames (plane, etc.)
        for i in range(start_delay_frames):
            finished |= cap.grab()

        ret, frame = cap.read()
        finished |= ret

        while not finished and frame_count + start_delay_frames <= death_frame:
            if frame.shape == (1080, 1920, 3):
                minimap_min_y = 798
                minimap_max_y = 1051
                minimap_min_x = 1630
                minimap_max_x = 1882
            else:
                raise ValueError

            minimap = frame[minimap_min_y:minimap_max_y, minimap_min_x:minimap_max_x]

            percent_processed = min(int((frame_count / frames_to_process) * 100), 100)
            yield percent_processed, minimap

            for i in range(time_step_frames):
                finished |= cap.grab()
            frame_count += time_step_frames

            ret, frame = cap.read()
            finished |= ret

    def find_path_bounds(self):
        """
        This function aims to provide bounds for the current path for pleasant viewing.
        
        To achieve this goal, the bounds provided should be:
            - square to prevent distortion, as the preview box will be square
            - not smaller than the provided minimum size to prevent too much zoom
            - equally padded from the boundaries of the path (in the x and y directions)
            
        :return: (x, y, w, h)
        """
        if self.all_coords:
            xs, ys = zip(*self.all_coords)

            min_x = min(xs) - CROP_BORDER
            max_x = max(xs) + CROP_BORDER
            min_y = min(ys) - CROP_BORDER
            max_y = max(ys) + CROP_BORDER

            # To make padding easier, round up the path widths to an even number
            # This mean we won't have to pad 1 side with an extra pixel
            x_path_width = int(ceil((max_x - min_x) / 2) * 2)
            y_path_width = int(ceil((max_y - min_y) / 2) * 2)

            output_size = max(MIN_PROGRESS_MAP_SIZE, x_path_width, y_path_width)

            # Allocation the extra space needed to fill up the required size equally on both sides
            x_pad = (output_size - x_path_width) // 2
            y_pad = (output_size - y_path_width) // 2

            x_corner = max(0, min_x - x_pad)
            y_corner = max(0, min_y - y_pad)

            return x_corner, y_corner, output_size, output_size
        else:
            return 0, 0, self.full_map_w, self.full_map_h

    def process_match(self):
        p = Pool(4)

        for match_found, coords, _, _, _, this_percent in p.imap(self.template_match, self.video_iterator()):
            if match_found == MatchResult.SUCCESFUL:
                try:
                    cv2.line(self.output_map,
                             self.all_coords[-1],
                             coords,
                             color=self.path_color,
                             thickness=PATH_WIDTH,
                             lineType=cv2.LINE_AA)
                except IndexError:
                    pass

                self.all_coords.append(coords)

                min_x, min_y, w, h = self.find_path_bounds()
                yield this_percent, self.output_map[min_y:min_y + h, min_x:min_x + w]

    def create_output(self):
        fig, ax = plt.subplots(figsize=(20, 20))
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        ax.axes.xaxis.set_visible(False)
        ax.axes.yaxis.set_visible(False)
        ax.imshow(cv2.cvtColor(self.full_map, cv2.COLOR_BGR2RGB))
        min_x, min_y, w, h = self.find_path_bounds()
        ax.axes.set_xlim(min_x, min_x + w)
        ax.axes.set_ylim(min_y + h, min_y)
        m_b, m_g, m_r = self.path_color
        mpl_color = [c / 255 for c in (m_r, m_g, m_b)]
        ax.plot(*zip(*self.all_coords), color=mpl_color, linewidth=PATH_WIDTH, alpha=PATH_ALPHA)
        fig.savefig(self.output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('--video_file', required=True)
    parser.add_argument('--death_time', type=int)
    parser.add_argument('--start_delay', type=int)
    parser.add_argument('--step_time', type=int)
    parser.add_argument('--output_file', type=str)
    parser.add_argument('--path_color', type=str)
    parser.add_argument('--debug', action='store_true')
    match = PUBGISMatch(**vars(parser.parse_args()))

    for percent, progress_map in match.process_match():
        cv2.imshow("progress", progress_map)
        cv2.waitKey(10)

    match.create_output()
