import cv2
from matplotlib import pyplot as plt
import multiprocessing
import argparse
from tqdm import tqdm


DEFAULT_MAP = "Erangel_Minimap_scaled.jpg"
DEFAULT_INDICATOR_MASK = "circle_mask.jpg"
DEFAULT_OUTPUT_FILE = "game_path.jpg"

DEFAULT_TEMP_MATCH_THRESHOLD = 15000000
DEFAULT_START_DELAY_FRAMES = 2000

# assume 30 fps?
DEFAULT_TIME_STEP_FRAMES = 30

CROP_BORDER = 30

# ??
MAX_DISTANCE_TRAVELED = 1000

PATH_WIDTH = 3
PATH_ALPHA = 0.7

DEFAULT_FONT = cv2.FONT_HERSHEY_SIMPLEX
DEBUG_FONT_SIZE = 0.75

NO_MATCH_COLOR = (0, 0, 255)
MATCH_COLOR = (0, 255, 0)

INDICATOR_COLOR_MIN = [130, 150, 150]
INDICATOR_COLOR_MAX = [225, 225, 225]


class PUBGIS:
    def __init__(self,
                 video_file,
                 full_map_file=DEFAULT_MAP,
                 mask_file=DEFAULT_INDICATOR_MASK,
                 delay_frames=DEFAULT_START_DELAY_FRAMES,
                 step_frames=DEFAULT_TIME_STEP_FRAMES,
                 output_file=DEFAULT_OUTPUT_FILE,
                 crop=False,
                 debug=False):
        self.video_file = video_file
        self.full_map = cv2.imread(full_map_file)
        self.indicator_mask = cv2.imread(mask_file, 0)
        self.gray_full_map = cv2.cvtColor(self.full_map, cv2.COLOR_BGR2GRAY)
        self.start_delay_frames = delay_frames
        self.time_step_frames = step_frames
        self.crop = crop
        self.debug = debug
        self.output_file = output_file
        self.full_map_w, self.full_map_h = self.gray_full_map.shape[::-1]

    @staticmethod
    def markup_image_debug(minimap, max_val, ind_in_range, ind_color):
        text_color = MATCH_COLOR if max_val > DEFAULT_TEMP_MATCH_THRESHOLD else NO_MATCH_COLOR
        rect_color = MATCH_COLOR if ind_in_range else NO_MATCH_COLOR

        b, g, r, _ = tuple(map(int, ind_color))

        cv2.rectangle(minimap, (200, 200), (250, 250), ind_color, thickness=-1)
        cv2.rectangle(minimap, (200, 200), (250, 250), rect_color, thickness=2)
        cv2.putText(minimap, '{:>12}'.format(int(max_val)), (20, 50), DEFAULT_FONT, DEBUG_FONT_SIZE , text_color)
        cv2.putText(minimap, f'{b}', (208, 212), DEFAULT_FONT, 0.3, (0, 0, 0))
        cv2.putText(minimap, f'{g}', (208, 227), DEFAULT_FONT, 0.3, (0, 0, 0))
        cv2.putText(minimap, f'{r}', (208, 242), DEFAULT_FONT, 0.3, (0, 0, 0))

        return minimap

    def template_match_minimap(self, minimap, last_coords):
        match_found = False

        ind_color = cv2.mean(minimap, self.indicator_mask)
        ind_in_range = all(ind_min < color < ind_max for ind_min, color, ind_max in
                           zip(INDICATOR_COLOR_MIN, ind_color, INDICATOR_COLOR_MAX))

        gray_minimap = cv2.cvtColor(minimap, cv2.COLOR_RGB2GRAY)

        w, h = gray_minimap.shape[::-1]

        # apply template matching to find most likely minimap location on the entire map
        # todo: shrink search partition to within range of last position to save time
        res = cv2.matchTemplate(self.gray_full_map, gray_minimap, cv2.TM_CCOEFF)
        _, max_val, _, (max_y, max_x) = cv2.minMaxLoc(res)

        if max_val > DEFAULT_TEMP_MATCH_THRESHOLD and ind_in_range:
            match_found = True

        if self.debug:
            debug_minimap = self.markup_image_debug(minimap, max_val, ind_in_range, ind_color)
        else:
            debug_minimap = None

        return match_found, (max_y + h // 2, max_x + w // 2), debug_minimap

    def video_iterator(self):
        frame_count = 0
        cap = cv2.VideoCapture(self.video_file)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        pbar = tqdm(total=total_frames)

        # skip the first frames (plane, etc.)
        for i in range(self.start_delay_frames):
            cap.grab()
        frame_count += self.start_delay_frames
        pbar.update(self.start_delay_frames)

        while True:
            ret, frame = cap.read()
            if frame is None:
                break
            else:
                if frame.shape == (720, 1280, 3):
                    minimap = frame[532:700, 1087:1255]
                elif frame.shape == (1080, 1920, 3):
                    minimap = frame[798:1051, 1630:1882]
                else:
                    raise ValueError
                yield minimap
                for i in range(self.time_step_frames):
                    cap.grab()
                frame_count += self.time_step_frames
                pbar.update(self.time_step_frames)

        pbar.close()

    def process_match(self):
        p = multiprocessing.Pool(3)
        all_coords = []

        for match_found, coords, debug_minimap in p.imap(self.template_match_minimap, self.video_iterator()):
            if match_found:
                all_coords.append(coords)
                if self.debug:
                    cv2.imshow("debug minimap", debug_minimap)
                    cv2.waitKey(10)

        map_fig, map_ax = plt.subplots()
        map_fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        map_ax.axes.xaxis.set_visible(False)
        map_ax.axes.yaxis.set_visible(False)
        map_ax.imshow(cv2.cvtColor(self.full_map, cv2.COLOR_BGR2RGB))
        map_ax.plot(*zip(*all_coords), color='green', linewidth=PATH_WIDTH, alpha=0.7)

        if self.crop:
            xs, ys = zip(*all_coords)

            min_x = min(xs)
            max_x = max(xs)
            min_y = min(ys)
            max_y = max(ys)

            map_ax.axes.set_xlim(min_x - CROP_BORDER, max_x + CROP_BORDER)
            map_ax.axes.set_ylim(min_y - CROP_BORDER, max_y + CROP_BORDER)

        plt.show()
        map_fig.savefig(f"{self.output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--video_file', required=True)
    parser.add_argument('--full_map_file', default=DEFAULT_MAP)
    parser.add_argument('--mask_file', default=DEFAULT_INDICATOR_MASK)
    parser.add_argument('--delay_frames', type=int, default=DEFAULT_START_DELAY_FRAMES)
    parser.add_argument('--step_frames', type=int, default=DEFAULT_TIME_STEP_FRAMES)
    parser.add_argument('--output_file', default=DEFAULT_OUTPUT_FILE)
    parser.add_argument('--crop', action='store_true')
    parser.add_argument('--debug', action='store_true')
    pubgis = PUBGIS(**vars(parser.parse_args()))

    pubgis.process_match()
