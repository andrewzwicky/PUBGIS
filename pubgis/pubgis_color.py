from enum import IntFlag


class ColorSpace(IntFlag):
    RGB = 0
    BGR = 1


class ColorScaling(IntFlag):
    PERC = 0
    UINT8 = 1


class Color:
    def __init__(self, color_tuple, alpha=1, scaling=ColorScaling.PERC, space=ColorSpace.RGB):
        # colors stored internally as 0-1
        if scaling == ColorScaling.UINT8:
            if space == ColorSpace.RGB:
                self.red, self.green, self.blue = [color / 255 for color in color_tuple]
            elif space == ColorSpace.BGR:
                self.red, self.green, self.blue = [color / 255 for color in color_tuple[::-1]]
            else:
                raise ValueError

            self.alpha = alpha / 255
        elif scaling == ColorScaling.PERC:
            if space == ColorSpace.RGB:
                self.red, self.green, self.blue = color_tuple
            elif space == ColorSpace.BGR:
                self.red, self.green, self.blue = color_tuple[::-1]
            else:
                raise ValueError

            self.alpha = alpha
        else:
            raise ValueError

    def get_with_alpha(self, scaling=ColorScaling.UINT8, space=ColorSpace.BGR):
        if scaling == ColorScaling.UINT8:
            return self.get(scaling=scaling, space=space) + (self.alpha * 255,)
        elif scaling == ColorScaling.PERC:
            return self.get(scaling=scaling, space=space) + (self.alpha,)

    def get(self, scaling=ColorScaling.UINT8, space=ColorSpace.BGR):
        if scaling == ColorScaling.UINT8:
            if space == ColorSpace.RGB:
                return tuple(int(c * 255) for c in (self.red, self.green, self.blue))
            elif space == ColorSpace.BGR:
                return tuple(int(c * 255) for c in (self.blue, self.green, self.red))
            else:
                raise ValueError
        elif scaling == ColorScaling.PERC:
            if space == ColorSpace.RGB:
                return self.red, self.green, self.blue
            elif space == ColorSpace.BGR:
                return self.blue, self.green, self.red
            else:
                raise ValueError
        else:
            raise ValueError
