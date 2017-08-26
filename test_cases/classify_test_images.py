import cv2
import os
import shutil

GOOD = 103
BAD = 98

for image in os.listdir("unknown"):
    unknown_path = os.path.join("unknown", image)
    cv2.imshow("test", cv2.imread(unknown_path))
    key = cv2.waitKey(-1)
    if key == GOOD:
        shutil.move(unknown_path, os.path.join("good", image))
    elif key == BAD:
        shutil.move(unknown_path, os.path.join("bad", image))
    else:
        pass
