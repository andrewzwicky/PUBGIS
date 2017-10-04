from os.path import join, dirname

import cv2
import matplotlib.colors as mpl_colors
import numpy as np
from matplotlib import pyplot as plt

from pubgis.color import Color, Space, Scaling
from pubgis.match_result import MatchResult
from pubgis.support import find_path_bounds, unscale_coords, coordinate_sum, coordinate_offset, \
    create_slice

plt.switch_backend('Agg')

IMAGES = join(dirname(__file__), "images")

MAX_SPEED = 130  # km/h, motorcycle
PIXELS_PER_100M = 64
PIXELS_PER_KM = PIXELS_PER_100M * 10
MAX_PIXELS_PER_H = MAX_SPEED * PIXELS_PER_KM
MAX_PIXELS_PER_SEC = MAX_PIXELS_PER_H / 3600

# calibrated based on test cases
COLOR_DIFF_THRESHS = [30, 70, 150]
TEMPLATE_MATCH_THRESHS = [.75, .40, .30]

PATH_WIDTH = 4

FONT = cv2.FONT_HERSHEY_SIMPLEX
BIG_FONT = 0.6
SMALL_FONT = 0.3

NO_MATCH_COLOR = Color(mpl_colors.to_rgb("Red"))
MATCH_COLOR = Color(mpl_colors.to_rgb("Lime"))
WHITE = Color(mpl_colors.to_rgb("White"))

DEFAULT_PATH_COLOR = Color(mpl_colors.to_rgb("Red"), alpha=0.7)
DEFAULT_PATH_THICKNESS = 2

FULL_SCALE_MINIMAP = 407


class PUBGISMatch:
    # full map will be the same for everything, and return coordinates will be relative to this map
    full_map = cv2.imread(join(IMAGES, "full_map.jpg"))

    def __init__(self,
                 minimap_iterator=None,
                 debug=False):
        self.minimap_iter = minimap_iterator
        self.debug = debug

        self.all_coords = []

        self.scale = self.minimap_iter.size / FULL_SCALE_MINIMAP
        self.gray_map = cv2.cvtColor(cv2.resize(PUBGISMatch.full_map,
                                                (0, 0),
                                                fx=self.scale,
                                                fy=self.scale),
                                     cv2.COLOR_BGR2GRAY)

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

    def debug_context(self, match_found, match_coords, context_slice):
        """
        Display a map showing the context where the matching happened.  It will also display where
        minimap was matched.

        If the supplied minimap was matched, it will be surrounded by a MATCH_COLOR rectangle,
        otherwise the surrounding rectangle will be NO_MATCH_COLOR
        """
        context_thickness = 6

        debug_zoomed = np.copy(self.gray_map[context_slice])

        cv2.rectangle(debug_zoomed,
                      coordinate_offset(match_coords, context_thickness // 2),
                      coordinate_offset(match_coords, self.minimap_iter.size - context_thickness),
                      MATCH_COLOR() if match_found == MatchResult.SUCCESSFUL else NO_MATCH_COLOR(),
                      thickness=context_thickness)

        cv2.imshow("context", debug_zoomed)
        cv2.waitKey(10)

    def annotate_minimap(self, minimap, match_found, color_diff, match_val):
        match_ind_thickness = 4

        cv2.putText(minimap, f"{int(color_diff)}", (25, 25), FONT, BIG_FONT, WHITE())
        cv2.putText(minimap, f"{match_val:.2f}", (25, 60), FONT, BIG_FONT, WHITE())

        cv2.rectangle(minimap,
                      (match_ind_thickness // 2, match_ind_thickness // 2),
                      (self.minimap_iter.size - match_ind_thickness,
                       self.minimap_iter.size - match_ind_thickness),
                      MATCH_COLOR() if match_found == MatchResult.SUCCESSFUL else NO_MATCH_COLOR(),
                      thickness=match_ind_thickness)

        return minimap

    def debug_minimap(self,
                      annotated_minimap,
                      world_coords):
        """
        Create a modified minimap with match information for display during debugging.

        The map displays the result of the template match, and the color difference between
        the player indicator and the area around it.

        If the supplied minimap was matched, it will be surrounded by a MATCH_COLOR rectangle,
        otherwise the surrounding rectangle will be NO_MATCH_COLOR
        """
        matched_minimap = self.gray_map[create_slice(world_coords, self.minimap_iter.size)]

        cv2.imshow("debug", np.concatenate((annotated_minimap, matched_minimap), axis=1))
        cv2.waitKey(10)

    def get_context(self):
        if self.all_coords:
            context_coords, context_size = find_path_bounds(
                self.gray_map.shape[0],
                [self.all_coords[-1]],
                crop_border=0,
                min_output_size=self.minimap_iter.size * 3)
            # TODO: better method for determining minimap sizing (i.e. consecutive missed frames)
            context_slice = create_slice(context_coords, context_size)
        else:
            context_coords = (0, 0)
            context_slice = slice(None)

        return context_coords, context_slice

    def find_map_section(self, minimap):
        """
        Attempt to match the supplied minimap to a section of the larger full map.

        The actual template matching is done by opencv, but there is additional checking that is
        done to ensure that the supplied minimap is actually
        """
        context_coords, context_slice = self.get_context()
        match = cv2.matchTemplate(self.gray_map[context_slice],
                                  cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY),
                                  cv2.TM_CCOEFF_NORMED)

        # When using TM_CCOEFF_NORMED, the minimum of the output is the best match
        _, result, _, match_coords = cv2.minMaxLoc(match)
        world_coords = coordinate_sum(match_coords, context_coords)

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

        if any(within_bounds):
            match_found = MatchResult.SUCCESSFUL
            scaled_coords = coordinate_offset(world_coords, self.minimap_iter.size // 2)
            full_coords = unscale_coords(scaled_coords, self.scale)

        else:
            match_found = MatchResult.OUT_OF_RANGE
            full_coords = None

        if self.debug:
            self.debug_context(match_found, match_coords, context_slice)
            annotated_minimap = self.annotate_minimap(minimap, match_found, color_diff, result)
            self.debug_minimap(annotated_minimap, world_coords)

        return match_found, full_coords, color_diff, result

    def process_match(self):
        for percent, minimap in self.minimap_iter:
            _, full_coords, _, _ = self.find_map_section(minimap)
            if full_coords:
                self.all_coords.append(full_coords)
            yield percent, full_coords

    def create_output(self,
                      output_file,
                      path_color=DEFAULT_PATH_COLOR,
                      path_thickness=DEFAULT_PATH_THICKNESS):
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

            mpl_color = path_color(space=Space.RGB,
                                   scaling=Scaling.PERC,
                                   alpha=True)
            output_axis.plot(*zip(*self.all_coords), color=mpl_color, linewidth=path_thickness)
            fig.savefig(output_file)
