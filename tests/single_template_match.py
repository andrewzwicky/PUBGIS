from pubgis import PUBGIS
import cv2

if __name__ == "__main__":
    match = PUBGIS(full_map_file=r"../full_map_scaled.jpg",
                   mask_file=r"../player_indicator_mask.jpg",
                   debug=True)
    test_image = r"good\shroud_2_33300_2400_2636.jpg"
    match.template_match(cv2.imread(test_image))
    cv2.waitKey(-1)