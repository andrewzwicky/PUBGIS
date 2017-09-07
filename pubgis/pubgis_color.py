from enum import IntFlag


class ColorSpace(IntFlag):
    RGB = 0
    BGR = 1


class ColorScaling(IntFlag):
    PERC = 0
    UINT8 = 1


class Color:
    def __init__(self, c1, c2, c3, in_scaling=ColorScaling.PERC, in_space=ColorSpace.RGB):
        # colors stored internally as 0-1
        if in_scaling == ColorScaling.UINT8:
            if in_space == ColorSpace.RGB:
                self.red = c1 / 255
                self.green = c2 / 255
                self.blue = c3 / 255
            elif in_space == ColorSpace.BGR:
                self.red = c3 / 255
                self.green = c2 / 255
                self.blue = c1 / 255
            else:
                raise ValueError
        elif in_scaling == ColorScaling.PERC:
            if in_space == ColorSpace.RGB:
                self.red = c1
                self.green = c2
                self.blue = c3
            elif in_space == ColorSpace.BGR:
                self.red = c3
                self.green = c2
                self.blue = c1
            else:
                raise ValueError
        else:
            raise ValueError

    def get(self, out_scaling=ColorScaling.UINT8, out_space=ColorSpace.BGR):
        if out_scaling == ColorScaling.UINT8:
            if out_space == ColorSpace.RGB:
                return tuple(int(c * 255) for c in (self.red, self.green, self.blue))
            elif out_space == ColorSpace.BGR:
                return tuple(int(c * 255) for c in (self.blue, self.green, self.red))
            else:
                raise ValueError
        elif out_scaling == ColorScaling.PERC:
            if out_space == ColorSpace.RGB:
                return self.red, self.green, self.blue
            elif out_space == ColorSpace.BGR:
                return self.blue, self.green, self.red
            else:
                raise ValueError
        else:
            raise ValueError
