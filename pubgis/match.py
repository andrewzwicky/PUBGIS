from os.path import join, dirname

import cv2
import numpy as np

from pubgis.color import Color
from pubgis.support import find_path_bounds, unscale_coords, coordinate_sum, coordinate_offset, \
    create_slice

IMAGES = join(dirname(__file__), "images")

# These lists of thresholds are the criteria used to determine if a template match output has
# actually matched a minimap, or if the supplied minimap was invalid (inventory, alt-tab, etc.)
#
# These were discovered experimentally by running many sets of images through the algorithm and
# examining the output.
COLOR_DIFF_THRESHS = [30, 70, 150]
TEMPLATE_MATCH_THRESHS = [.75, .40, .30]

MAX_PIXELS_PER_SEC = 160  # plane

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SIZE = 0.6

NO_MATCH_COLOR = Color((1, 0, 0))  # RED
MATCH_COLOR = Color((0, 1, 0))  # LIME
WHITE = Color((1, 1, 1))  # WHITE

# If the minimap were scaled up to be the same resolution as the full map,
# it would take up FULL_SCALE_MINIMAP pixels.
FULL_SCALE_MINIMAP = 407

# Experimentally determined as well
IND_OUTER_CIRCLE_RATIO = 0.05555
IND_INNER_CIRCLE_RATIO = 0.01587
AREA_MASK_AREA_RATIO = 0.145


class PUBGISMatch:
    """
    PUBGISMatch is responsible for processing a series of minimap images and outputting the
    position of the player at each of the minimaps (if possible).

    The output positions are based on the full_map which is the highest resolution map.  This
    same map is used as the reference for output positions, regardless of input resolution.

    On a high level, this class first attempts to match given minimaps against the entire map.
    Once a position has successfully been found, subsequent minimaps are only searched for in a
    smaller area, around the last position.  This speeds up searching significantly.
    """
    full_map = cv2.imread(join(IMAGES, "full_map.jpg"))

    def __init__(self, minimap_iterator, debug=False):
        self.minimap_iter = minimap_iterator

        assert self.minimap_iter.size

        self.debug = debug

        # last_scaled_position is stored so later iterations can use this to
        # narrow the search space for template matching.
        self.last_scaled_position = None
        self.missed_frames = 0

        # For processing purposes, a scaled grayscale map will be stored.  This map is scaled so
        # features on the minimap and this map are the same resolution.  This is important for
        # the template matching, and is done on an instance basis because it may change for
        # each instance of PUBGISMatch.
        self.scale = self.minimap_iter.size / FULL_SCALE_MINIMAP
        scaled_map = cv2.resize(PUBGISMatch.full_map, (0, 0), fx=self.scale, fy=self.scale)
        self.gray_map = cv2.cvtColor(scaled_map, cv2.COLOR_BGR2GRAY)

        self.masks = self.create_masks(self.minimap_iter.size)

    @staticmethod
    def create_masks(size):
        """
        These masks are used to calculate the color difference between where the player indicator
        should be and the area around it.  The masks are based on ratios, so should scale
        to different input resolutions.

        The indicator_mask is 2 concentric circles that mask everything except the outer and inner
        rings of the player indicator.

        The area_mask is the inverse of the indicator mask, limited to a small area right around the
        indicator, this is used to get the mean color in the surrounding area.
        """
        center = (size // 2, size // 2)

        mask_base = np.zeros((size, size, 1), np.uint8)

        ind_base = np.copy(mask_base)
        cv2.circle(ind_base, center, int(size * IND_OUTER_CIRCLE_RATIO), 255, thickness=2)
        cv2.circle(ind_base, center, int(size * IND_INNER_CIRCLE_RATIO), 255, thickness=1)
        _, indicator_mask = cv2.threshold(ind_base, 10, 255, cv2.THRESH_BINARY)

        area_base = np.copy(mask_base)
        cv2.circle(area_base, center, int(size * AREA_MASK_AREA_RATIO), 255, thickness=cv2.FILLED)
        cv2.circle(area_base, center, int(size * IND_OUTER_CIRCLE_RATIO), 0, thickness=2)
        cv2.circle(area_base, center, int(size * IND_INNER_CIRCLE_RATIO), 0, thickness=1)
        _, area_mask = cv2.threshold(area_base, 10, 255, cv2.THRESH_BINARY)

        return indicator_mask, area_mask

    def __debug_context(self, match_found, match_coords, context_slice):
        """
        Display the context that was used for this iteration of template matching, as well as
        where the minimap was matched.

        If the supplied minimap was matched, it will be surrounded by a MATCH_COLOR rectangle,
        otherwise the surrounding rectangle will be NO_MATCH_COLOR.
        """
        context_thickness = 6
        context_display_size = 800

        debug_zoomed = np.copy(self.gray_map[context_slice])
        debug_zoomed = cv2.cvtColor(debug_zoomed, cv2.COLOR_GRAY2BGR)

        cv2.rectangle(debug_zoomed,
                      coordinate_offset(match_coords, context_thickness // 2),
                      coordinate_offset(match_coords, self.minimap_iter.size - context_thickness),
                      MATCH_COLOR() if match_found else NO_MATCH_COLOR(),
                      thickness=context_thickness)

        debug_zoomed = cv2.resize(debug_zoomed,
                                  (0, 0),
                                  fx=context_display_size / debug_zoomed.shape[0],
                                  fy=context_display_size / debug_zoomed.shape[0])

        cv2.imshow("context", debug_zoomed)
        cv2.waitKey(10)

    def __annotate_minimap(self, minimap, match_found, color_diff, match_val):
        """
        Produce an annotated minimap that shows the parameters of the match, and whether a match
        was successfully found.  The parameters are drawn directly on the map in-place, which is
        then returned.

        If the supplied minimap was matched, it will be surrounded by a MATCH_COLOR rectangle,
        otherwise the surrounding rectangle will be NO_MATCH_COLOR
        """
        match_ind_thickness = 4

        cv2.putText(minimap, f"{int(color_diff)}", (25, 25), FONT, FONT_SIZE, WHITE())
        cv2.putText(minimap, f"{match_val:.2f}", (25, 60), FONT, FONT_SIZE, WHITE())
        cv2.putText(minimap, f"{self.missed_frames:.2f}", (25, 95), FONT, FONT_SIZE, WHITE())

        cv2.rectangle(minimap,
                      (match_ind_thickness // 2, match_ind_thickness // 2),
                      (self.minimap_iter.size - match_ind_thickness,
                       self.minimap_iter.size - match_ind_thickness),
                      MATCH_COLOR() if match_found else NO_MATCH_COLOR(),
                      thickness=match_ind_thickness)

        return minimap

    def __debug_minimap(self, annotated_minimap, world_coords):
        """
        Concatenate the annotated minimap, with the matched section of the same size from the
        scaled map.  This is useful for debugging potential incorrect matches.
        """
        matched_minimap = self.gray_map[create_slice(world_coords, self.minimap_iter.size)]
        matched_minimap = cv2.cvtColor(matched_minimap, cv2.COLOR_GRAY2BGR)

        cv2.imshow("debug", np.concatenate((annotated_minimap, matched_minimap), axis=1))
        cv2.waitKey(10)

    def get_scaled_context(self):
        context_coords = (0, 0)
        context_slice = slice(None)

        # the context calculation is present to reduce the search space
        # when the last position was known.
        if self.last_scaled_position:
            # First, we get the maximum number of unscaled pixels that is expected we could travel
            # This doesn't cover weird edge cases like being flung across the map or something like
            # that.  Sorry.
            # This must also be per time_step as well so that we don't scale the map too quickly
            max_unscaled_pixels_per_step = self.minimap_iter.time_step * MAX_PIXELS_PER_SEC
            max_scaled_pixels_per_step = max_unscaled_pixels_per_step * self.scale

            # Then the mximum distance able to be traveled in any 1 direction is
            # the number of frames multiplied by the max travel distance.
            # The reason that 1 is added to missed_frames, is that if we haven't missed the
            # last frame, we still need to account for one frame of travel.
            max_reachable_dist = (self.missed_frames + 1) * int(max_scaled_pixels_per_step)

            # multiply by 2 to get the width of the search space
            max_reachable_dist *= 2

            # Add a buffer around the edge so that there is at least 1/2 the minimap around the edge
            max_reachable_dist += self.minimap_iter.size

            context_coords, context_size = find_path_bounds(
                self.gray_map.shape[0],
                [self.last_scaled_position],
                crop_border=0,
                min_size=max_reachable_dist)
            context_slice = create_slice(context_coords, context_size)

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

        # First, get the context and perform the match on that part of the grayscale scaled map.
        context_coords, context_slice = self.get_scaled_context()
        match = cv2.matchTemplate(self.gray_map[context_slice],
                                  cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY),
                                  cv2.TM_CCOEFF_NORMED)

        # match is an array, the same shape as the context.  Next, we must find the minimum value
        # in the array because we're using the TM_CCOEFF_NORMED matching method.
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
        # As long as this iteration's combination of color difference and match_value fall above
        # both thresholds for each pair of thresholds, we consider that a match.

        within_bounds = [color_diff > c_thresh and result > temp_thresh for c_thresh, temp_thresh in
                         zip(COLOR_DIFF_THRESHS, TEMPLATE_MATCH_THRESHS)]

        if any(within_bounds):
            match_found = True
            scaled_map_pos = coordinate_offset(scaled_coords, self.minimap_iter.size // 2)
            self.missed_frames = 0

        else:
            match_found = False
            scaled_map_pos = None
            self.missed_frames += 1

        if self.debug:
            self.__debug_context(match_found, match_coords, context_slice)
            annotated_minimap = self.__annotate_minimap(minimap, match_found, color_diff, result)
            self.__debug_minimap(annotated_minimap, scaled_coords)

        return scaled_map_pos, color_diff, result

    def process_match(self):
        """
        Process the match by calling find_scaled_player_position on each minimap that is generated.

        last_scaled_position is stored, but the unscaled full map coordinates the ones that are
        yielded.  This means that the same game played on different resolutions should provide
        comparable results.
        """
        for percent, minimap in self.minimap_iter:
            scaled_position, _, _ = self.find_scaled_player_position(minimap)
            if scaled_position:
                self.last_scaled_position = scaled_position
            full_position = unscale_coords(scaled_position, self.scale)
            yield percent, full_position
