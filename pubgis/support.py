from itertools import repeat

import cv2
import numpy as np

CROP_BORDER = 30
MIN_BOUNDS_SIZE = 600


def find_path_bounds(map_size, coords, crop_border=CROP_BORDER, min_output_size=MIN_BOUNDS_SIZE):
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

        return (int(x_corner), int(y_corner)), int(output_size)

    # If no frames have been processed yet, the full map should be displayed to show that
    # processing has begun.
    return (0, 0), map_size


def unscale_coords(scaled_coords, scale):
    return tuple(int(coord / scale) for coord in scaled_coords)


def coordinate_sum(coords_a, coords_b):
    return tuple(a + b for a, b in zip(coords_a, coords_b))


def coordinate_offset(coords, offset):
    return tuple(a + b for a, b in zip(coords, repeat(offset)))


def create_slice(coords, size):
    x_coord, y_coord = coords
    return slice(y_coord, y_coord + size), slice(x_coord, x_coord + size)


def blend_transparent(base_map, path_overlay):
    # Split out the transparency mask from the colour info
    overlay_img = path_overlay[:, :, :3]  # Grab the BRG planes
    overlay_mask = path_overlay[:, :, 3:]  # And the alpha plane

    # Again calculate the inverse mask
    background_mask = 255 - overlay_mask

    # Turn the masks into three channel, so we can use them as weights
    overlay_mask = cv2.cvtColor(overlay_mask, cv2.COLOR_GRAY2BGR)
    background_mask = cv2.cvtColor(background_mask, cv2.COLOR_GRAY2BGR)

    # Create a masked out face image, and masked out overlay
    # We convert the images to floating point in range 0.0 - 1.0
    face_part = (base_map * (1 / 255.0)) * (background_mask * (1 / 255.0))
    overlay_part = (overlay_img * (1 / 255.0)) * (overlay_mask * (1 / 255.0))

    # And finally just add them together, and rescale it back to an 8bit integer image
    return np.uint8(cv2.addWeighted(face_part, 255.0, overlay_part, 255.0, 0.0))
