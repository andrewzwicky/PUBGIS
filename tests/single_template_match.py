from pubgis import PUBGISMatch
import cv2

if __name__ == "__main__":
    match = PUBGISMatch(debug=True)
    for test_image in [r"bad\squads_dinner_mike_pat_11885.jpg"]:
        img = cv2.imread(test_image)
        match_found, coords, ind_color, color_diff, match_val, percent = match.template_match(img)
        print(coords)
        cv2.waitKey(-1)
