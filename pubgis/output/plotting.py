import cv2

from pubgis.color import Color
from pubgis.support import find_path_bounds, create_slice

PATH_COLOR = Color((1, 0, 0), alpha=0.9) # RED
PATH_THICKNESS = 5


def create_output_opencv(input_map, coords, output_file, full_map=False):
    if full_map:
        output_slice = slice(None)
    else:
        output_slice = create_slice(*find_path_bounds(input_map.shape[0], coords))
    cv2.imwrite(output_file, input_map[output_slice])


def plot_coordinate_line(input_map, prev_positions, position, color, thickness):
    if position is not None:
        last_valid_pos = next((pos for pos in prev_positions[::-1] if pos is not None), None)
        if last_valid_pos is not None:
            cv2.line(input_map,
                     last_valid_pos,
                     position,
                     color=color,
                     thickness=thickness,
                     lineType=cv2.LINE_AA)
