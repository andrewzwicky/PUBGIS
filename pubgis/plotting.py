import cv2
import matplotlib.colors as mpl_colors
from matplotlib import pyplot as plt

from pubgis.color import Color, Scaling, Space
from pubgis.support import find_path_bounds

PATH_COLOR = Color(mpl_colors.to_rgb("Red"), alpha=0.7)
PATH_THICKNESS = 2


def create_output(input_map, input_coords, output_file, color=PATH_COLOR, thickness=PATH_THICKNESS):
    fig, output_axis = plt.subplots(figsize=(20, 20))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    output_axis.axes.xaxis.set_visible(False)
    output_axis.axes.yaxis.set_visible(False)

    output_axis.imshow(input_map)

    (min_x, min_y), size = find_path_bounds(input_map.shape[0], input_coords)
    output_axis.axes.set_xlim(min_x, min_x + size)
    output_axis.axes.set_ylim(min_y + size, min_y)

    mpl_color = color(space=Space.RGB, scaling=Scaling.PERC, alpha=True)
    output_axis.plot(*zip(*input_coords), color=mpl_color, linewidth=thickness)
    fig.savefig(output_file)


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
