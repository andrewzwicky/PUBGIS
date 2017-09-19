from math import ceil
from multiprocessing import Pool
from os.path import join, dirname

import cv2
import matplotlib.colors as mpl_colors
import numpy as np
from matplotlib import pyplot as plt

from pubgis.color import Color, Space, Scaling
from pubgis.match_result import MatchResult

plt.switch_backend('Agg')

IMAGES = join(dirname(__file__), "images")

CROP_BORDER = 30

MAX_SPEED = 130  # km/h, motorcycle
PIXELS_PER_100M = 64
PIXELS_PER_KM = PIXELS_PER_100M * 10
MAX_PIXELS_PER_H = MAX_SPEED * PIXELS_PER_KM
MAX_PIXELS_PER_SEC = MAX_PIXELS_PER_H / 3600

# calibrated based on test cases
COLOR_DIFF_THRESH_1 = 70
TEMPLATE_MATCH_THRESH_1 = .40
COLOR_DIFF_THRESH_2 = 30
TEMPLATE_MATCH_THRESH_2 = .75

PATH_WIDTH = 4

MIN_PROGRESS_MAP_SIZE = 600

FONT = cv2.FONT_HERSHEY_SIMPLEX
BIG_FONT = 0.6
SMALL_FONT = 0.3

NO_MATCH_COLOR = Color(mpl_colors.to_rgb("Red"))
MATCH_COLOR = Color(mpl_colors.to_rgb("Lime"))
WHITE = Color(mpl_colors.to_rgb("White"))

DEFAULT_PATH_COLOR = Color(mpl_colors.to_rgb("Lime"), alpha=0.7)

MMAP_WIDTH = 252
MMAP_HEIGHT = 253
MMAP_Y = 798
MMAP_X = 1630


# when indexing an image the format is image[y,x]
# but coords are passed as (x,y)


class PUBGISMatch:
    map = cv2.imread(join(IMAGES, "full_map_scaled.jpg"))
    gray_map = cv2.cvtColor(map, cv2.COLOR_BGR2GRAY)
    indicator_file = cv2.imread(join(IMAGES, "indicator_mask.jpg"), cv2.IMREAD_GRAYSCALE)
    indicator_area_file = cv2.imread(join(IMAGES, "indicator_area_mask.jpg"), cv2.IMREAD_GRAYSCALE)
    _, indicator_mask = cv2.threshold(indicator_file, 10, 255, cv2.THRESH_BINARY)
    _, indicator_area_mask = cv2.threshold(indicator_area_file, 10, 255, cv2.THRESH_BINARY)

    def __init__(self,
                 minimap_iterator=None,
                 output_file=None,
                 path_color=DEFAULT_PATH_COLOR,
                 debug=False):
        self.minimap_iterator = minimap_iterator
        self.preview_map = np.copy(PUBGISMatch.map)
        self.debug = debug
        self.output_file = output_file
        self.path_color = path_color
        self.all_coords = []

    @staticmethod
    def debug_minimap(minimap,
                      match_found,
                      color_diff,
                      match_val):
        """
        Create a modified minimap with match information for display during debugging.

        The map displays the result of the template match, and the color difference between
        the player indicator and the area around it.

        If the supplied minimap was matched, it will be surrounded by a MATCH_COLOR rectangle,
        otherwise the surrounding rectangle will be NO_MATCH_COLOR

        :param minimap:
        :param match_found:
        :param color_diff:
        :param match_val:
        :return:
        """

        cv2.putText(minimap, f"{int(color_diff)}", (25, 25), FONT, BIG_FONT, WHITE())
        cv2.putText(minimap, f"{match_val:.2f}", (25, 60), FONT, BIG_FONT, WHITE())

        cv2.rectangle(minimap,
                      (0, 0),
                      (MMAP_HEIGHT, MMAP_WIDTH),
                      MATCH_COLOR() if match_found == MatchResult.SUCCESFUL else NO_MATCH_COLOR(),
                      thickness=4)

        return minimap

    #  This method should be static to make imap work with an external iterator class.
    @staticmethod
    def find_map_section(args):
        """
        Attempt to match the supplied minimap to a section of the larger full map.

        The actual template matching is done by opencv, but there is additional checking that is
        done to ensure that the supplied minimap is actually

        :param args:
        :return:
        """
        this_percent, minimap = args
        debug = False

        match = cv2.matchTemplate(PUBGISMatch.gray_map,
                                  cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY),
                                  cv2.TM_CCOEFF_NORMED)

        _, result, _, (best_x, best_y) = cv2.minMaxLoc(match)
        coords = (best_x + MMAP_WIDTH // 2, best_y + MMAP_HEIGHT // 2)

        color_diff = Color.calculate_color_diff(minimap,
                                                PUBGISMatch.indicator_mask,
                                                minimap,
                                                PUBGISMatch.indicator_area_mask)

        if (color_diff > COLOR_DIFF_THRESH_1 and result > TEMPLATE_MATCH_THRESH_1) or \
                (color_diff > COLOR_DIFF_THRESH_2 and result > TEMPLATE_MATCH_THRESH_2):
            match_found = MatchResult.SUCCESFUL
        else:
            match_found = MatchResult.OUT_OF_RANGE

        if debug:
            debug_minimap = PUBGISMatch.debug_minimap(minimap, match_found, color_diff, result)
            cropped_map = PUBGISMatch.map[best_y:best_y + MMAP_HEIGHT, best_x:best_x + MMAP_WIDTH]
            cv2.imshow("debug", np.concatenate((debug_minimap, cropped_map), axis=1))
            cv2.waitKey(10)

        return match_found, coords, color_diff, result, this_percent

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
            x_list, y_list = zip(*self.all_coords)

            min_x = min(x_list) - CROP_BORDER
            max_x = max(x_list) + CROP_BORDER
            min_y = min(y_list) - CROP_BORDER
            max_y = max(y_list) + CROP_BORDER

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

        return (0, 0) + tuple(PUBGISMatch.gray_map.shape)

    def process_match(self):
        """

        :return:
        """
        pool = Pool(multiprocessing.cpu_count())

        for match_found, coords, _, _, percent in pool.imap(PUBGISMatch.find_map_section,
                                                            self.minimap_iterator):
            if match_found == MatchResult.SUCCESFUL:
                if self.all_coords:
                    cv2.line(self.preview_map,
                             self.all_coords[-1],
                             coords,
                             color=self.path_color(),
                             thickness=PATH_WIDTH,
                             lineType=cv2.LINE_AA)

                self.all_coords.append(coords)

                min_x, min_y, width, height = self.find_path_bounds()
                yield percent, self.preview_map[min_y:min_y + height, min_x:min_x + width]

    def create_output(self):
        """

        :return:
        """
        if self.output_file:
            fig, output_axis = plt.subplots(figsize=(20, 20))
            fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
            output_axis.axes.xaxis.set_visible(False)
            output_axis.axes.yaxis.set_visible(False)
            output_axis.imshow(cv2.cvtColor(PUBGISMatch.map, cv2.COLOR_BGR2RGB))
            min_x, min_y, width, height = self.find_path_bounds()
            output_axis.axes.set_xlim(min_x, min_x + width)
            output_axis.axes.set_ylim(min_y + height, min_y)

            mpl_color = self.path_color(space=Space.RGB,
                                        scaling=Scaling.PERC,
                                        alpha=True)
            output_axis.plot(*zip(*self.all_coords), color=mpl_color, linewidth=PATH_WIDTH)
            fig.savefig(self.output_file)
