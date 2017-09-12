from enum import IntFlag


class Space(IntFlag):
    RGB = 0
    BGR = 1


class Scaling(IntFlag):
    PERC = 0
    UINT8 = 1


class Color:
    def __init__(self, colors, alpha=1, scaling=Scaling.PERC, space=Space.RGB):
        # colors stored internally as 0-1
        if space == Space.RGB:
            input_colors = colors + (alpha,)
        elif space == Space.BGR:
            input_colors = colors[::-1] + (alpha,)
        else:
            raise ValueError

        if scaling == Scaling.UINT8:
            input_colors = tuple(c / 255 for c in input_colors)
        elif scaling == Scaling.PERC:
            pass
        else:
            raise ValueError

        self.red, self.green, self.blue, self.alpha = input_colors

    def __call__(self, scaling=Scaling.UINT8, space=Space.BGR, alpha=False):
        colors = (self.red, self.green, self.blue)

        if space == Space.RGB:
            output = colors
        elif space == Space.BGR:
            output = colors[::-1]
        else:
            raise ValueError

        if alpha:
            output += (self.alpha,)

        if scaling == Scaling.UINT8:
            output = tuple(c*255 for c in output)
        elif scaling == Scaling.PERC:
            pass
        else:
            raise ValueError

        return output
