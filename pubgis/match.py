from os.path import join, dirname

import cv2
import numpy as np

from pubgis.color import Color, Scaling
from pubgis.support import find_path_bounds, unscale_coords, scale_coords, coordinate_sum, \
    coordinate_offset, create_slice, get_coords_from_slices

IMAGES = join(dirname(__file__), "images")

# These lists of thresholds are the criteria used to determine if a template match output has
# actually matched a minimap, or if the supplied minimap was invalid (inventory, alt-tab, etc.)
#
# These were discovered experimentally by running many sets of images through the algorithm and
# examining the output.
COLOR_DIFF_THRESHS = [30, 70, 150]
TEMPLATE_MATCH_THRESHS = [.75, .40, .30]

MAX_PLANE_PIX_PER_SEC = 160  # plane
MAX_WATER_PIX_PER_SEC = 120  # boat

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SIZE = 0.6

NO_MATCH_COLOR = Color((1, 0, 0))  # RED
MATCH_COLOR = Color((0, 1, 0))  # LIME
LAND = Color((0, 255, 0), scaling=Scaling.UINT8)  # HUNTER GREEN
WATER = Color((0, 0, 255), scaling=Scaling.UINT8)  # BLUE
WHITE = Color((1, 1, 1))  # WHITE

# If the minimap were scaled up to be the same resolution as the full map,
# it would take up FULL_SCALE_MINIMAP pixels.
FULL_SCALE_MINIMAP = 407

# Experimentally determined as well
IND_OUTER_CIRCLE_RATIO = 0.05555
IND_INNER_CIRCLE_RATIO = 0.01587
AREA_MASK_AREA_RATIO = 0.145
AREA_OUTER_CIRCLE_RATIO = IND_OUTER_CIRCLE_RATIO * 1.1


class PUBGISMatch:
    """
    PUBGISMatch is responsible for processing a series of minimap images and outputting the
    position of the player at each of the minimaps (if possible).

    The output positions are based on the full_map which is the highest resolution map.  This
    same map is used as the reference for output positions, regardless of input resolution.
    """
    full_map = cv2.imread(join(IMAGES, "full_map.jpg"))
    land_mask_image = cv2.imread(join(IMAGES, "land_mask.jpg"), cv2.IMREAD_GRAYSCALE)
    _, land_mask = cv2.threshold(land_mask_image, 10, 255, cv2.THRESH_BINARY)
    land_mask_scale = len(land_mask) / len(full_map)

    def __init__(self, minimap_iterator, debug=False):
        self.minimap_iter = minimap_iterator
        self.debug = debug

        # last_known_position is stored to narrow the search space for template matching.
        # last_known_position is unscaled, thus corresponds to coordinates on the full map.
        self.last_known_position = None
        self.missed_frames = 0

        # For processing purposes, a scaled grayscale map will be stored.  This map is scaled so
        # features on the minimap and this map are the same resolution.  This is important for
        # the template matching, and is done on an instance basis because the input resolution may
        # change for each instance of PUBGISMatch.
        self.scale = self.minimap_iter.size / FULL_SCALE_MINIMAP
        scaled_map = cv2.resize(PUBGISMatch.full_map, (0, 0), fx=self.scale, fy=self.scale)
        self.gray_map = cv2.cvtColor(scaled_map, cv2.COLOR_BGR2GRAY)

        self.masks = self._create_masks(self.minimap_iter.size)

    def process_match(self):
        for percent, timestamp, minimap in self.minimap_iter:
            unscaled_position = self._find_unscaled_player_position(minimap)

            self._update_missed_frames(unscaled_position)
            self._update_last_unscaled_position(unscaled_position)

            yield percent, timestamp, unscaled_position

    def _find_unscaled_player_position(self, minimap):
        scaled_position = self._find_scaled_player_position(minimap)
        unscaled_position = self._unscale_coords(scaled_position)
        unscaled_position_valid = self._is_unscaled_position_valid(unscaled_position)

        if not unscaled_position_valid:
            unscaled_position = None

        return unscaled_position

    def _find_scaled_player_position(self, minimap):
        color_diff = Color.calculate_color_diff(minimap, *self.masks)
        if color_diff < min(COLOR_DIFF_THRESHS):
            scaled_position = None
            template_match_result = 0
            scaled_position_valid = False
        else:
            scaled_position, template_match_result = self._perform_template_matching(minimap)
            scaled_position_valid = self._is_scaled_position_valid(color_diff,
                                                                   template_match_result)

        if self.debug:
            ann_map = self.__annotate_minimap(minimap, color_diff, template_match_result)
            self.__debug_minimap(ann_map, scaled_position)

        if not scaled_position_valid:
            scaled_position = None

        return scaled_position

    def _perform_template_matching(self, minimap):
        context_slice = self._get_scaled_context()
        context_coords = get_coords_from_slices(context_slice)
        template_match = cv2.matchTemplate(self.gray_map[context_slice],
                                           cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY),
                                           cv2.TM_CCOEFF_NORMED)
        # match is an array, the same shape as the context.  Next, we must find the minimum value
        # in the array because we're using the TM_CCOEFF_NORMED matching method.

        if context_slice != slice(None, None, None):
            scaled_last_known = scale_coords(self.last_known_position, self.scale)
            context_last_known = coordinate_sum(scaled_last_known, [-x for x in context_coords])
            xax = np.arange(template_match.shape[0]) - context_last_known[0]
            yax = np.arange(template_match.shape[0]) - context_last_known[1]
            xx, yy = np.meshgrid(xax, yax)
            z = np.sqrt(np.sqrt(xx ** 2 + yy ** 2)) / 1000
            template_match -= z

        _, template_match_value, _, match_position = cv2.minMaxLoc(template_match)
        scaled_position = coordinate_sum(match_position, context_coords)
        scaled_position = coordinate_offset(scaled_position, self.minimap_iter.size // 2)

        if self.debug:
            self.__debug_context(match_position, context_slice)
            # self.__debug_land(scaled_position)

        return scaled_position, template_match_value

    def _get_scaled_context(self):
        # Context defines the area that the template matching will be limited to.
        # This area gets larger each time a match is missed to account for movement processing.
        context_slice = slice(None)

        if self.last_known_position:
            max_reachable_dist = self._calculate_max_travel_distance()

            context_coords, context_size = find_path_bounds(
                self.gray_map.shape[0],
                [scale_coords(self.last_known_position, self.scale)],
                crop_border=0,
                min_size=max_reachable_dist)
            context_slice = create_slice(context_coords, context_size)

        return context_slice

    def _calculate_max_travel_distance(self):
        # First, we get the maximum number of unscaled pixels that is expected we could travel
        # This doesn't cover weird edge cases like being flung across the map or something like
        # that.  Sorry. This must also be per time_step as well so that we don't scale the map
        # too quickly.
        if self._is_position_on_land(self.last_known_position):
            max_pixels_per_sec = MAX_PLANE_PIX_PER_SEC
        else:
            max_pixels_per_sec = MAX_WATER_PIX_PER_SEC

        max_scaled_pixels_per_step = self.minimap_iter.time_step * max_pixels_per_sec * self.scale
        # Then the maximum distance able to be traveled in any 1 direction is
        # the number of frames multiplied by the max travel distance.
        # The reason that 1 is added to missed_frames, is that if we haven't missed the
        # last frame, we still need to account for one frame of travel.
        max_reachable_dist = (self.missed_frames + 1) * int(max_scaled_pixels_per_step)
        # multiply by 2 to get the width of the search space
        max_reachable_dist *= 2
        # Add a buffer around the edge so that there is at least 1/2 the minimap around the edge
        max_reachable_dist += self.minimap_iter.size

        return max_reachable_dist

    @staticmethod
    def _is_scaled_position_valid(color_diff, template_match_result):
        # Determining whether a particular minimap should actually be reported as a match
        # is determined by the following:
        # 1. How closely correlated was the match? [template_match_result]
        #     Because we are using normalized matching, this will report a 0-1 value, with 1
        #     being a perfect match.  The higher the better.
        # 2. The difference in color between the player indicator and the surroundings. [color_diff]
        #     When the player indicator is on the screen, we expect to see a large difference in
        #     the colors.  When the inventory is open for example, there should be very little
        #     difference in the colors.
        #
        # There are three different regions used that correspond to experimentally determined
        # regions, found during testing to effectively differentiate the areas.
        # As long as this iteration's combination of color_diff and template_match_result fall above
        # both thresholds for each pair of thresholds, we consider that a match.
        match_found = False
        for color_diff_thresh, template_match_thresh in zip(COLOR_DIFF_THRESHS,
                                                            TEMPLATE_MATCH_THRESHS):
            if color_diff > color_diff_thresh and template_match_result > template_match_thresh:
                match_found = True
                break

        return match_found

    def _is_unscaled_position_valid(self, unscaled_position):
        if unscaled_position is None:
            return False

        return self.last_known_position is not None or self._is_position_on_land(unscaled_position)

    def _is_position_on_land(self, unscaled_position):
        on_land = False

        if unscaled_position:
            land_mask_coords = scale_coords(unscaled_position, self.land_mask_scale)
            on_land = bool(self.land_mask[land_mask_coords[1], land_mask_coords[0]])

        return on_land

    def _update_missed_frames(self, unscaled_position):
        if unscaled_position:
            self.missed_frames = 0
        else:
            self.missed_frames += 1

    def _update_last_unscaled_position(self, unscaled_position):
        if unscaled_position:
            if self.last_known_position is not None or self._is_position_on_land(unscaled_position):
                self.last_known_position = unscaled_position

    @staticmethod
    def _create_masks(size):
        # These masks are used to calculate the color difference between where the player indicator
        # should be and the area around it.  The masks are based on ratios, so they scale
        # to different input resolutions.
        #
        # The indicator_mask is 2 concentric circles that mask everything except the outer and
        # inner rings of the player indicator.
        #
        # The area_mask is the inverse of the indicator mask, limited to a small area right
        # around the indicator, this is used to get the mean color in the surrounding area.
        center = (size // 2, size // 2)

        mask_base = np.zeros((size, size, 1), np.uint8)

        ind_base = np.copy(mask_base)
        cv2.circle(ind_base, center, int(size * IND_OUTER_CIRCLE_RATIO), 255, thickness=2)
        cv2.circle(ind_base, center, int(size * IND_INNER_CIRCLE_RATIO), 255, thickness=1)
        _, indicator_mask = cv2.threshold(ind_base, 10, 255, cv2.THRESH_BINARY)

        area_base = np.copy(mask_base)
        cv2.circle(area_base, center, int(size * AREA_MASK_AREA_RATIO), 255, thickness=cv2.FILLED)
        cv2.circle(area_base, center, int(size * AREA_OUTER_CIRCLE_RATIO), 0, thickness=cv2.FILLED)
        _, area_mask = cv2.threshold(area_base, 10, 255, cv2.THRESH_BINARY)

        return indicator_mask, area_mask

    def _unscale_coords(self, scaled_position):
        return unscale_coords(scaled_position, self.scale)

    def __debug_context(self, match_position, context_slice):
        context_thickness = 6
        context_display_size = 800

        debug_zoomed = np.copy(self.gray_map[context_slice])
        debug_zoomed = cv2.cvtColor(debug_zoomed, cv2.COLOR_GRAY2BGR)

        cv2.rectangle(debug_zoomed,
                      coordinate_offset(match_position, context_thickness // 2),
                      coordinate_offset(match_position, self.minimap_iter.size - context_thickness),
                      WHITE(),
                      thickness=context_thickness)

        debug_zoomed = cv2.resize(debug_zoomed,
                                  (0, 0),
                                  fx=context_display_size / debug_zoomed.shape[0],
                                  fy=context_display_size / debug_zoomed.shape[0])

        cv2.imshow("context", debug_zoomed)
        cv2.waitKey(10)

    def __debug_land(self, scaled_position):

        land_debug = np.copy(self.land_mask)

        if scaled_position:
            unscaled_position = self._unscale_coords(scaled_position)
            on_land = self._is_position_on_land(unscaled_position)
            land_debug = cv2.cvtColor(land_debug, cv2.COLOR_GRAY2BGR)
            land_mask_coords = scale_coords(unscaled_position, self.land_mask_scale)
            cv2.circle(land_debug, land_mask_coords, 10, LAND() if on_land else WATER(), cv2.FILLED)

        cv2.imshow("land", land_debug)
        cv2.waitKey(10)

    def __annotate_minimap(self, minimap, color_diff, match_val):
        ind_mask_minimap = np.copy(minimap)
        res1 = cv2.bitwise_and(ind_mask_minimap, ind_mask_minimap, mask=self.masks[0])
        ind_area_mask_minimap = np.copy(minimap)
        res2 = cv2.bitwise_and(ind_area_mask_minimap, ind_area_mask_minimap, mask=self.masks[1])

        cv2.putText(minimap, f"{int(color_diff)}", (25, 25), FONT, FONT_SIZE, WHITE())
        cv2.putText(minimap, f"{match_val:.2f}", (25, 60), FONT, FONT_SIZE, WHITE())
        cv2.putText(minimap, f"{self.missed_frames:.2f}", (25, 95), FONT, FONT_SIZE, WHITE())

        minimap = cv2.cvtColor(minimap, cv2.COLOR_BGRA2BGR)
        res1 = cv2.cvtColor(res1, cv2.COLOR_BGRA2BGR)
        res2 = cv2.cvtColor(res2, cv2.COLOR_BGRA2BGR)

        return np.concatenate((res1, res2, minimap), axis=1)

    def __debug_minimap(self, annotated_minimap, scaled_position):
        if scaled_position is None:
            offset_coords = (0, 0)
        else:
            offset_coords = coordinate_offset(scaled_position, -self.minimap_iter.size // 2)
        matched_minimap = self.gray_map[create_slice(offset_coords, self.minimap_iter.size)]
        matched_minimap = cv2.cvtColor(matched_minimap, cv2.COLOR_GRAY2BGR)

        cv2.imshow("debug", np.concatenate((annotated_minimap, matched_minimap), axis=1))
        cv2.waitKey(10)
