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
COLOR_DIFF_THRESHS = [30, 70, 150]
TEMPLATE_MATCH_THRESHS = [.75, .40, .30]

PATH_WIDTH = 4

MIN_PROGRESS_MAP_SIZE = 600

FONT = cv2.FONT_HERSHEY_SIMPLEX
BIG_FONT = 0.6
SMALL_FONT = 0.3

NO_MATCH_COLOR = Color(mpl_colors.to_rgb("Red"))
MATCH_COLOR = Color(mpl_colors.to_rgb("Lime"))
WHITE = Color(mpl_colors.to_rgb("White"))

DEFAULT_PATH_COLOR = Color(mpl_colors.to_rgb("Red"), alpha=0.7)

# when indexing an image the format is image[y,x]
# but coords are passed as (x,y)


class PUBGISMatch:
    map = cv2.imread(join(IMAGES, "full_map_scaled.jpg"))
    gray_map = cv2.cvtColor(map, cv2.COLOR_BGR2GRAY)
    assert gray_map.shape[0] == gray_map.shape[1]
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
    def debug_minimap(minimap, match_found, color_diff, match_val, all_coords):
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
        :param match_coords:
        :param overall_coords:
        :param zoomed_coords:
        :return:
        """
        (match_x, match_y), (over_x, over_y), (z_x, z_y, size) = all_coords

        cv2.putText(minimap, f"{int(color_diff)}", (25, 25), FONT, BIG_FONT, WHITE())
        cv2.putText(minimap, f"{match_val:.2f}", (25, 60), FONT, BIG_FONT, WHITE())

        cv2.rectangle(minimap,
                      (0, 0),
                      (MMAP_HEIGHT, MMAP_WIDTH),
                      MATCH_COLOR() if match_found == MatchResult.SUCCESSFUL else NO_MATCH_COLOR(),
                      thickness=4)
        # TODO: cropped map is in wrong place, need to scale back by MMAP_WIDTH/HEIGHT // 2
        cropped_map = PUBGISMatch.map[over_y:over_y + MMAP_HEIGHT, over_x:over_x + MMAP_WIDTH]
        cv2.imshow("debug", np.concatenate((minimap, cropped_map), axis=1))

        debug_zoomed = np.copy(PUBGISMatch.map[z_y:z_y + size, z_x:z_x + size])

        cv2.rectangle(debug_zoomed,
                      (match_x, match_y),
                      (match_x + MMAP_WIDTH, match_y + MMAP_HEIGHT),
                      MATCH_COLOR() if match_found == MatchResult.SUCCESSFUL else NO_MATCH_COLOR(),
                      thickness=4)

        cv2.imshow("context", cv2.resize(debug_zoomed,
                                         (0, 0),
                                         fx=600 / size,
                                         fy=600 / size))
        cv2.waitKey(10)

    def find_map_section(self, minimap, debug=False):  # pylint: disable=too-many-locals
        """
        Attempt to match the supplied minimap to a section of the larger full map.

        The actual template matching is done by opencv, but there is additional checking that is
        done to ensure that the supplied minimap is actually

        :param minimap:
        :param debug:
        :return:
        """
        last_coord = self.all_coords[-1] if self.all_coords else None

        if last_coord:
            z_x, z_y, size = PUBGISMatch.find_path_bounds([last_coord],
                                                          crop_border=0,
                                                          min_output_size=minimap.shape[0] * 3)
            zoomed_gray_map = np.copy(PUBGISMatch.gray_map[z_y:z_y + size, z_x:z_x + size])
        else:
            z_x = z_y = 0
            size = PUBGISMatch.gray_map.shape[0]
            zoomed_gray_map = np.copy(PUBGISMatch.gray_map)

        match = cv2.matchTemplate(zoomed_gray_map,
                                  cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY),
                                  cv2.TM_CCOEFF_NORMED)

        # When using TM_CCOEFF_NORMED, the minimum of the output is the best match
        _, result, _, (match_x, match_y) = cv2.minMaxLoc(match)
        best_x = match_x + z_x
        best_y = match_y + z_y
        coords = (best_x + minimap.shape[1] // 2, best_y + minimap.shape[0] // 2)

        color_diff = Color.calculate_color_diff(minimap,
                                                PUBGISMatch.indicator_mask,
                                                minimap,
                                                PUBGISMatch.indicator_area_mask)

        # Determining whether a particular minimap should actually be reported as a match
        # is determined by the following:
        # 1. How closely correlated was the match?
        #     Because we are using normalized matching, this will report a 0-1 value, with 1
        #     being a perfect match.  The higher the better.
        # 2. The difference in color between the the player indicator and the area around it.
        #     When the player indicator is on the screen, we expect to see a large difference in
        #     the colors.  When the inventory is open for example, there should be very little
        #     difference in the colors.
        #
        # There are two different regions used that correspond to experimentally determined
        # regions, found during testing to effectively differentiate the areas.

        within_bounds = [color_diff > c_thresh and result > temp_thresh for c_thresh, temp_thresh in
                         zip(COLOR_DIFF_THRESHS, TEMPLATE_MATCH_THRESHS)]

        if any(within_bounds):
            match_found = MatchResult.SUCCESSFUL
        else:
            match_found = MatchResult.OUT_OF_RANGE

        if debug:
            PUBGISMatch.debug_minimap(minimap, match_found, color_diff, result,
                                      ((match_x, match_y), coords, (z_x, z_y, size)))

        return match_found, coords, color_diff, result

    @staticmethod
    def find_path_bounds(coords,  # pylint: disable=too-many-locals
                         crop_border=CROP_BORDER,
                         min_output_size=MIN_PROGRESS_MAP_SIZE):
        """
        This function should provide a bounding box that contains the current coordinates of the
        path for display, and does not exceed the bounds of the map.

        To be aesthetically pleasing , the bounds provided shall be:
            - square to prevent distortion, as the preview box will be square
            - not smaller than the provided minimum size to prevent too much zoom
            - equally padded from the boundaries of the path (in the x and y directions)

        :return: (x, y, height, width)
        """
        map_size, _ = PUBGISMatch.gray_map.shape

        if coords:
            x_list, y_list = zip(*coords)

            # First, the area of interest should be defined.  This is the area that absolutely
            # needs to be displayed because it has all the coordinates in it.  It's OK for out of
            # bounds here, this will be resolved later.
            min_x = min(x_list) - crop_border
            max_x = max(x_list) + crop_border
            min_y = min(y_list) - crop_border
            max_y = max(y_list) + crop_border

            # Determine the width that the coordinates occupy in the x and y directions.  These
            # are used to determine the final size of the bounds.
            x_path_width = max_x - min_x
            y_path_width = max_y - min_y

            # The size of the final output will be a square, so we need to find out the largest
            # of the possible sizes for the final output.  MIN_PROGRESS_MAP_SIZE is the lower bound
            # for how small the output map can be.  The final output bounds also can't be larger
            # than the entire map.
            output_size = min(max(min_output_size, x_path_width, y_path_width), map_size)

            # Each side is now padded to take up additional room in the smaller direction.
            # If a particular direction was chosen to the be the output size, the padding in that
            # direction will be 0.
            x_corner = min_x - (output_size - x_path_width) // 2
            y_corner = min_y - (output_size - y_path_width) // 2

            # Bounds checks for the corners to make sure all of the bounds is within the map limits.
            x_corner = 0 if x_corner < 0 else x_corner
            y_corner = 0 if y_corner < 0 else y_corner
            x_corner = map_size - output_size if x_corner + output_size > map_size else x_corner
            y_corner = map_size - output_size if y_corner + output_size > map_size else y_corner

            return int(x_corner), int(y_corner), int(output_size)

        # If no frames have been processed yet, the full map should be displayed to show that
        # processing has begun.
        return 0, 0, map_size

    def process_match(self):
        """

        :return:
        """
        for percent, minimap in self.minimap_iterator:
            match, coords, _, _ = self.find_map_section(minimap)
            if match == MatchResult.SUCCESSFUL:
                if self.all_coords:
                    cv2.line(self.preview_map,
                             self.all_coords[-1],
                             coords,
                             color=self.path_color(),
                             thickness=PATH_WIDTH,
                             lineType=cv2.LINE_AA)

                self.all_coords.append(coords)

            min_x, min_y, size = PUBGISMatch.find_path_bounds(self.all_coords)
            yield percent, self.preview_map[min_y:min_y + size, min_x:min_x + size]

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
            min_x, min_y, size = self.find_path_bounds(self.all_coords)
            output_axis.axes.set_xlim(min_x, min_x + size)
            output_axis.axes.set_ylim(min_y + size, min_y)

            mpl_color = self.path_color(space=Space.RGB,
                                        scaling=Scaling.PERC,
                                        alpha=True)
            output_axis.plot(*zip(*self.all_coords), color=mpl_color, linewidth=PATH_WIDTH)
            fig.savefig(self.output_file)
