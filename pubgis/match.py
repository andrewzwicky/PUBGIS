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
DEFAULT_PATH_THICKNESS = 2


# when indexing an image the format is image[y,x]
# but coords are passed as (x,y)


class PUBGISMatch:  # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 minimap_iterator=None,
                 path_color=DEFAULT_PATH_COLOR,
                 path_thickness=DEFAULT_PATH_THICKNESS,
                 debug=False):
        self.minimap_iter = minimap_iterator
        self.debug = debug

        self.path_color = path_color
        self.path_thickness = path_thickness
        self.all_coords = []

        full_map = cv2.imread(join(IMAGES, "full_map.jpg"))
        self.map = cv2.resize(full_map,
                              (0, 0),
                              fx=self.minimap_iter.size / 407,
                              fy=self.minimap_iter.size / 407)
        self.gray_map = cv2.cvtColor(self.map, cv2.COLOR_BGR2GRAY)
        self.preview_map = np.copy(self.map)

        _, self.indicator_mask = cv2.threshold(self.create_mask(self.minimap_iter.size),
                                               10,
                                               255,
                                               cv2.THRESH_BINARY)
        _, self.indicator_area_mask = cv2.threshold(
            self.create_area_mask(self.minimap_iter.size),
            10,
            255,
            cv2.THRESH_BINARY)

    @staticmethod
    def create_mask(size):
        mask = np.zeros((size, size, 1), np.uint8)
        cv2.circle(mask, (size // 2, size // 2), int(size * 0.05555), 255, thickness=2)
        cv2.circle(mask, (size // 2, size // 2), int(size * 0.01587), 255, thickness=1)
        return mask

    @staticmethod
    def create_area_mask(size):
        mask = np.zeros((size, size, 1), np.uint8)
        width = int(size * .29)
        cv2.rectangle(mask,
                      (size // 2 - width // 2, size // 2 - width // 2),
                      (size // 2 + width // 2, size // 2 + width // 2),
                      255,
                      thickness=-1)
        cv2.circle(mask, (size // 2, size // 2), int(size * 0.05555), 0, thickness=2)
        cv2.circle(mask, (size // 2, size // 2), int(size * 0.01587), 0, thickness=1)
        return mask

    def debug_context(self, match_found, match_x, match_y, context_slice):
        """
        Display a map showing the context where the matching happened.  It will also display where
        minimap was matched.

        If the supplied minimap was matched, it will be surrounded by a MATCH_COLOR rectangle,
        otherwise the surrounding rectangle will be NO_MATCH_COLOR
        """
        context_thickness = 6

        debug_zoomed = np.copy(self.map[context_slice])

        cv2.rectangle(debug_zoomed,
                      (match_x + context_thickness // 2, match_y + context_thickness // 2),
                      (match_x + self.minimap_iter.size - context_thickness,
                       match_y + self.minimap_iter.size - context_thickness),
                      MATCH_COLOR() if match_found == MatchResult.SUCCESSFUL else NO_MATCH_COLOR(),
                      thickness=context_thickness)

        cv2.imshow("context", debug_zoomed)
        cv2.waitKey(10)

    def debug_minimap(self,  # pylint: disable=too-many-arguments
                      minimap,
                      match_found,
                      color_diff,
                      match_val,
                      world_coords):
        """
        Create a modified minimap with match information for display during debugging.

        The map displays the result of the template match, and the color difference between
        the player indicator and the area around it.

        If the supplied minimap was matched, it will be surrounded by a MATCH_COLOR rectangle,
        otherwise the surrounding rectangle will be NO_MATCH_COLOR
        """
        world_x, world_y = world_coords

        match_ind_thickness = 4

        cv2.putText(minimap, f"{int(color_diff)}", (25, 25), FONT, BIG_FONT, WHITE())
        cv2.putText(minimap, f"{match_val:.2f}", (25, 60), FONT, BIG_FONT, WHITE())

        cv2.rectangle(minimap,
                      (match_ind_thickness // 2, match_ind_thickness // 2),
                      (self.minimap_iter.size - match_ind_thickness,
                       self.minimap_iter.size - match_ind_thickness),
                      MATCH_COLOR() if match_found == MatchResult.SUCCESSFUL else NO_MATCH_COLOR(),
                      thickness=match_ind_thickness)

        matched_minimap = self.map[world_y:world_y + self.minimap_iter.size,
                                   world_x:world_x + self.minimap_iter.size]

        cv2.imshow("debug", np.concatenate((minimap, matched_minimap), axis=1))
        cv2.waitKey(10)

    def find_map_section(self, minimap):  # pylint: disable=too-many-locals
        """
        Attempt to match the supplied minimap to a section of the larger full map.

        The actual template matching is done by opencv, but there is additional checking that is
        done to ensure that the supplied minimap is actually
        """
        if self.all_coords:
            context_x, context_y, context_size = PUBGISMatch.find_path_bounds(
                self.gray_map.shape[0],
                [self.all_coords[-1]],
                crop_border=0,
                min_output_size=minimap.shape[0] * 3)
            # TODO: better method for determining minimap sizing (i.e. consecutive missed frames)
            context_slice = (slice(context_y, context_y + context_size),
                             slice(context_x, context_x + context_size))
        else:
            context_x = context_y = 0
            context_slice = slice(None)

        match = cv2.matchTemplate(self.gray_map[context_slice],
                                  cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY),
                                  cv2.TM_CCOEFF_NORMED)

        # When using TM_CCOEFF_NORMED, the minimum of the output is the best match
        _, result, _, (match_x, match_y) = cv2.minMaxLoc(match)
        world_x = match_x + context_x
        world_y = match_y + context_y
        coords = (world_x + (self.minimap_iter.size // 2),
                  world_y + (self.minimap_iter.size // 2))

        color_diff = Color.calculate_color_diff(minimap,
                                                self.indicator_mask,
                                                self.indicator_area_mask)

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

        match_found = MatchResult.SUCCESSFUL if any(within_bounds) else MatchResult.OUT_OF_RANGE

        if self.debug:
            self.debug_context(match_found, match_x, match_y, context_slice)
            self.debug_minimap(minimap, match_found, color_diff, result, (world_x, world_y))

        return match_found, coords, color_diff, result

    @staticmethod
    def find_path_bounds(map_size,  # pylint: disable=too-many-locals
                         coords,
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
        for percent, minimap in self.minimap_iter:
            match, coords, _, _ = self.find_map_section(minimap)
            if match == MatchResult.SUCCESSFUL:
                if self.all_coords:
                    cv2.line(self.preview_map,
                             self.all_coords[-1],
                             coords,
                             color=self.path_color(),
                             thickness=self.path_thickness,
                             lineType=cv2.LINE_AA)

                self.all_coords.append(coords)

            min_x, min_y, size = PUBGISMatch.find_path_bounds(self.gray_map.shape[0],
                                                              self.all_coords)
            yield percent, self.preview_map[min_y:min_y + size, min_x:min_x + size]

    def create_output(self, output_file):
        if output_file:
            fig, output_axis = plt.subplots(figsize=(20, 20))
            fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
            output_axis.axes.xaxis.set_visible(False)
            output_axis.axes.yaxis.set_visible(False)
            output_axis.imshow(cv2.cvtColor(self.map, cv2.COLOR_BGR2RGB))
            min_x, min_y, size = PUBGISMatch.find_path_bounds(self.gray_map.shape[0],
                                                              self.all_coords)
            output_axis.axes.set_xlim(min_x, min_x + size)
            output_axis.axes.set_ylim(min_y + size, min_y)

            mpl_color = self.path_color(space=Space.RGB,
                                        scaling=Scaling.PERC,
                                        alpha=True)
            output_axis.plot(*zip(*self.all_coords), color=mpl_color, linewidth=self.path_thickness)
            fig.savefig(output_file)
