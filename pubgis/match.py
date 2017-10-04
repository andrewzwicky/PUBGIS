from os.path import join, dirname

import cv2
import matplotlib.colors as mpl_colors
import numpy as np
from matplotlib import pyplot as plt

from pubgis.color import Color, Space, Scaling
from pubgis.support import find_path_bounds, unscale_coords, coordinate_sum, coordinate_offset, \
    create_slice

plt.switch_backend('Agg')

IMAGES = join(dirname(__file__), "images")

# TODO: outdated numbers, (pixels), based on 1920x1080 resolution.  Should be res-independent
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

IND_OUTER_CIRCLE_RATIO = 0.05555
IND_INNER_CIRCLE_RATIO = 0.01587
AREA_MASK_AREA_RATIO = 0.29


class PUBGISMatch:
    # The full map is the same for all matches processed, regardless of resolution.
    full_map = cv2.imread(join(IMAGES, "full_map.jpg"))

    def __init__(self, minimap_iterator=None, debug=False):
        self.minimap_iter = minimap_iterator
        self.debug = debug

        self.scaled_positions = []

        # For processing purposes, a scaled grayscale map will be stored.  This map is scaled so
        # features on the minimap and this map are the same resolution.  This is important for
        # the template matching, and is done on an instance basis because it may change for
        # each match.
        self.scale = self.minimap_iter.size / FULL_SCALE_MINIMAP
        scaled_map = cv2.resize(PUBGISMatch.full_map, (0, 0), fx=self.scale, fy=self.scale)
        self.gray_map = cv2.cvtColor(scaled_map, cv2.COLOR_BGR2GRAY)

        self.masks = self.create_masks(self.minimap_iter.size)

    @staticmethod
    def create_masks(size):
        center = size // 2

        mask_base = np.zeros((size, size, 1), np.uint8)

        ind_base = np.copy(mask_base)
        cv2.circle(ind_base, (center, center), int(size * IND_OUTER_CIRCLE_RATIO), 255, thickness=2)
        cv2.circle(ind_base, (center, center), int(size * IND_INNER_CIRCLE_RATIO), 255, thickness=1)
        _, indicator_mask = cv2.threshold(ind_base, 10, 255, cv2.THRESH_BINARY)

        area_base = np.copy(mask_base)
        area_size = int(size * AREA_MASK_AREA_RATIO) // 2
        cv2.rectangle(area_base,
                      (center - area_size, center - area_size),
                      (center + area_size, center + area_size),
                      255,
                      thickness=cv2.FILLED)
        cv2.circle(area_base, (center, center), int(size * IND_OUTER_CIRCLE_RATIO), 0, thickness=2)
        cv2.circle(area_base, (center, center), int(size * IND_INNER_CIRCLE_RATIO), 0, thickness=1)
        _, area_mask = cv2.threshold(area_base, 10, 255, cv2.THRESH_BINARY)

        return indicator_mask, area_mask

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
                      MATCH_COLOR() if match_found else NO_MATCH_COLOR(),
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
                      MATCH_COLOR() if match_found else NO_MATCH_COLOR(),
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

    def get_scaled_match_context(self):
        if self.scaled_positions:
            context_coords, context_size = find_path_bounds(
                self.gray_map.shape[0],
                [self.scaled_positions[-1]],
                crop_border=0,
                min_output_size=self.minimap_iter.size * 3)
            # TODO: better method for determining minimap sizing (i.e. consecutive missed frames)
            context_slice = create_slice(context_coords, context_size)
        else:
            context_coords = (0, 0)
            context_slice = slice(None)

        return context_coords, context_slice

    def find_scaled_player_position(self, minimap):
        """
        Attempt to match the supplied minimap to a section of the larger full map.

        The actual template matching is done by opencv, but there is additional checking that is
        done to ensure that the supplied minimap is actually.

        This method contains several sets of coordinates.  Everything done inside this method is
        done on the scaled coordinate system, which uses the scaled map, based on the input
        resolution.

        The context refers to the reduced area that matching will take place in.  Reducing the
        search area significantly reduces the amount of time that matching takes.

        context_coords are the coordinates of the top-left corner of the context area.
        match_coords are the coordinates of the matched minimap within the context.
        scaled_coords are the coordinates of the matched minimap within the scaled map.
        scaled_map_pos is just the coordinates for the center of the matched minimap, relative to
            the scaled map.

        To obtain the coordinates relative to the full map, the coordinates are unscaled later.
        """
        context_coords, context_slice = self.get_scaled_match_context()
        match = cv2.matchTemplate(self.gray_map[context_slice],
                                  cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY),
                                  cv2.TM_CCOEFF_NORMED)

        # When using TM_CCOEFF_NORMED, the minimum of the output is the best match
        _, result, _, match_coords = cv2.minMaxLoc(match)
        scaled_coords = coordinate_sum(match_coords, context_coords)

        color_diff = Color.calculate_color_diff(minimap, *self.masks)

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
        # There are three different regions used that correspond to experimentally determined
        # regions, found during testing to effectively differentiate the areas.

        within_bounds = [color_diff > c_thresh and result > temp_thresh for c_thresh, temp_thresh in
                         zip(COLOR_DIFF_THRESHS, TEMPLATE_MATCH_THRESHS)]

        if any(within_bounds):
            match_found = True
            scaled_map_pos = coordinate_offset(scaled_coords, self.minimap_iter.size // 2)

        else:
            match_found = False
            scaled_map_pos = None

        if self.debug:
            self.debug_context(match_found, match_coords, context_slice)
            annotated_minimap = self.annotate_minimap(minimap, match_found, color_diff, result)
            self.debug_minimap(annotated_minimap, scaled_coords)

        return scaled_map_pos, color_diff, result

    def process_match(self):
        for percent, minimap in self.minimap_iter:
            scaled_position, _, _ = self.find_scaled_player_position(minimap)
            self.scaled_positions.append(scaled_position)
            full_position = unscale_coords(scaled_position, self.scale)
            yield percent, full_position

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
