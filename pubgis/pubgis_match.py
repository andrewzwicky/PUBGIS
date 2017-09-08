import argparse
import os
from math import sqrt, ceil
from multiprocessing import Pool

import cv2
import matplotlib.colors as mpl_colors
import numpy as np
from matplotlib import pyplot as plt

from pubgis.template_match_result import MatchResult
from pubgis.pubgis_color import Color, ColorSpace, ColorScaling

MAP_FILE = os.path.join(os.path.dirname(__file__), "images", "full_map_scaled.jpg")
INDICATOR_MASK_FILE = os.path.join(os.path.dirname(__file__), "images", "player_indicator_mask.jpg")
INDICATOR_AREA_MASK_FILE = os.path.join(os.path.dirname(__file__), "images", "player_indicator_area_mask.jpg")
DEFAULT_OUTPUT_FILE = "{}_path.jpg"

DEFAULT_START_DELAY = 10  # seconds
DEFAULT_TIME_INTERVAL = 1  # seconds

CROP_BORDER = 30

MAX_SPEED = 130  # km/h, motorcycle
PIXELS_PER_100M = 64
PIXELS_PER_KM = PIXELS_PER_100M * 10
MAX_PIXELS_PER_H = MAX_SPEED * PIXELS_PER_KM
MAX_PIXELS_PER_SEC = MAX_PIXELS_PER_H / 3600

# calibrated based on test cases
COLOR_DIFF_THRESHOLD_1 = 70
TEMPLATE_MATCH_THRESHOLD_1 = .40
COLOR_DIFF_THRESHOLD_2 = 30
TEMPLATE_MATCH_THRESHOLD_2 = .75

PATH_WIDTH = 4

MIN_PROGRESS_MAP_SIZE = 600

DEFAULT_FONT = cv2.FONT_HERSHEY_SIMPLEX
DEBUG_FONT_SIZE_BIG = 0.6
DEBUG_FONT_SIZE_SMALL = 0.3

NO_MATCH_COLOR = Color(*mpl_colors.to_rgb("Red"))
MATCH_COLOR = Color(*mpl_colors.to_rgb("Lime"))

DEFAULT_PATH_COLOR = Color(*mpl_colors.to_rgb("Lime"), alpha=0.7)

MINIMAP_WIDTH = 252
MINIMAP_HEIGHT = 253


# when indexing an image the format is image[y,x]
# but coords are passed as (x,y)


class PUBGISMatch:
    def __init__(self,
                 video_file,
                 start_delay=DEFAULT_START_DELAY,
                 step_interval=DEFAULT_TIME_INTERVAL,
                 death_time=None,
                 output_file=None,
                 path_color=DEFAULT_PATH_COLOR,
                 debug=False):
        self.video_file = video_file
        self.full_map = cv2.imread(MAP_FILE)
        self.output_map = np.copy(self.full_map)
        _, self.indicator_mask = cv2.threshold(cv2.imread(INDICATOR_MASK_FILE, 0), 10, 255, cv2.THRESH_BINARY)
        _, self.indicator_area_mask = cv2.threshold(cv2.imread(INDICATOR_AREA_MASK_FILE, 0), 10, 255, cv2.THRESH_BINARY)
        self.gray_full_map = cv2.cvtColor(self.full_map, cv2.COLOR_BGR2GRAY)
        self.start_delay = start_delay
        self.step_interval = step_interval
        self.death_time = death_time
        self.debug = debug

        # TODO: double check output file handling.
        if not output_file:
            video_name = os.path.splitext(video_file)[0]
            self.output_file = DEFAULT_OUTPUT_FILE.format(video_name)
        else:
            self.output_file = output_file

        self.path_color = path_color
        self.full_map_h, self.full_map_w = self.gray_full_map.shape
        self.all_coords = []

    @staticmethod
    def markup_minimap_debug(minimap,
                             ind_color,
                             ind_area_color,
                             color_diff,
                             match_val):
        ind_rect_corner = (200, 200)
        ind_rect_area_corner = (120, 200)
        rect_size = 50
        text_inset = (8, 15)
        test_spacing = 15

        cv2.putText(minimap, f"{int(color_diff)}", (25, 25), DEFAULT_FONT, DEBUG_FONT_SIZE_BIG, MATCH_COLOR.get())
        cv2.putText(minimap, f"{match_val:.2f}", (25, 60), DEFAULT_FONT, DEBUG_FONT_SIZE_BIG, MATCH_COLOR.get())

        cv2.rectangle(minimap,
                      ind_rect_corner,
                      tuple(c + rect_size for c in ind_rect_corner),
                      ind_color.get(),
                      thickness=-1)

        for i, color in enumerate(ind_color.get()):
            x = ind_rect_corner[0] + text_inset[0]
            y = ind_rect_corner[1] + text_inset[1] + i * test_spacing
            cv2.putText(minimap, f'{color}', (x, y), DEFAULT_FONT, DEBUG_FONT_SIZE_SMALL, (0, 0, 0))

        cv2.rectangle(minimap,
                      ind_rect_area_corner,
                      tuple(c + rect_size for c in ind_rect_area_corner),
                      ind_area_color.get(),
                      thickness=-1)
        for i, color in enumerate(ind_area_color.get()):
            x = ind_rect_area_corner[0] + text_inset[0]
            y = ind_rect_area_corner[1] + text_inset[1] + i * test_spacing
            cv2.putText(minimap, f'{color}', (x, y), DEFAULT_FONT, DEBUG_FONT_SIZE_SMALL, (0, 0, 0))

        return minimap

    def template_match(self, percent_minimap):
        this_percent, minimap = percent_minimap
        match_found = MatchResult.SUCCESFUL

        gray_minimap = cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY)
        h, w = gray_minimap.shape

        res = cv2.matchTemplate(self.gray_full_map, gray_minimap, cv2.TM_CCOEFF_NORMED)
        _, match_val, _, (x, y) = cv2.minMaxLoc(res)

        coords = (x + w // 2, y + h // 2)

        ind_color = Color(*cv2.mean(minimap, self.indicator_mask)[:3], scaling=ColorScaling.UINT8,
                          space=ColorSpace.BGR)
        ind_area_color = Color(*cv2.mean(minimap, self.indicator_area_mask)[:3], scaling=ColorScaling.UINT8,
                               space=ColorSpace.BGR)
        color_diff = sqrt(sum([(c1 - c2) ** 2 for c1, c2 in zip(ind_color.get(),
                                                                ind_area_color.get())]))

        in_range = (color_diff > COLOR_DIFF_THRESHOLD_1 and match_val > TEMPLATE_MATCH_THRESHOLD_1) or \
                   (color_diff > COLOR_DIFF_THRESHOLD_2 and match_val > TEMPLATE_MATCH_THRESHOLD_2)

        if not in_range:
            match_found |= MatchResult.OUT_OF_RANGE

        if self.debug:
            cv2.imshow("debug", np.concatenate((self.markup_minimap_debug(minimap,
                                                                          ind_color,
                                                                          ind_area_color,
                                                                          color_diff,
                                                                          match_val),
                                                self.full_map[y:y + h, x:x + w]),
                                               axis=1))
            cv2.waitKey(10)

        return match_found, coords, ind_color, color_diff, match_val, this_percent

    def video_iterator(self):
        """
        Return the minimap every time_interval seconds from the supplied video, skipping the first start_delay frames.
        
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
        num_interval_frames = max(int(self.step_interval * fps), 1)
        death_frame = int(self.death_time * fps) if self.death_time is not None else total_frames

        frames_to_process = death_frame - start_delay_frames

        finished = False

        # skip the first frames (plane, etc.)
        for i in range(start_delay_frames):
            finished |= not cap.grab()

        ret, frame = cap.read()
        finished |= not ret

        while not finished and frame_count + start_delay_frames <= death_frame:
            if frame.shape == (1080, 1920, 3):
                minimap_min_y = 798
                minimap_max_y = minimap_min_y + MINIMAP_HEIGHT
                minimap_min_x = 1630
                minimap_max_x = minimap_min_x + MINIMAP_WIDTH
            else:
                raise ValueError

            minimap = frame[minimap_min_y:minimap_max_y, minimap_min_x:minimap_max_x]

            percent_processed = min(int((frame_count / frames_to_process) * 100), 100)
            yield percent_processed, minimap

            for i in range(num_interval_frames):
                finished |= not cap.grab()
            frame_count += num_interval_frames

            # If no frames has been grabbed the methods return false
            ret, frame = cap.read()
            finished |= not ret

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
                             color=self.path_color.get(),
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

        mpl_color, alpha = self.path_color.get_with_alpha(space=ColorSpace.RGB, scaling=ColorScaling.PERC)
        ax.plot(*zip(*self.all_coords), color=mpl_color, linewidth=PATH_WIDTH, alpha=alpha)
        fig.savefig(self.output_file)


class ColorAction(argparse.Action):
    def __call__(self, parser_arg, namespace, values, option_string=None):
        setattr(namespace, self.dest, Color(*mpl_colors.to_rgb(values)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('--video_file', required=True)
    parser.add_argument('--death_time', type=int)
    parser.add_argument('--start_delay', type=int)
    parser.add_argument('--step_interval', type=int)
    parser.add_argument('--output_file', type=str)
    parser.add_argument('--path_color', type=str, action=ColorAction)
    parser.add_argument('--debug', action='store_true')
    match = PUBGISMatch(**vars(parser.parse_args()))

    for percent, progress_map in match.process_match():
        cv2.imshow("progress", progress_map)
        cv2.waitKey(10)

    match.create_output()
