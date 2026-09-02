import cv2
from cameras import cameras


def run_opencv(display=False):

    caps = {}

    for name, url in cameras.items():

        print(f"Starting: {name}")

        cap = cv2.VideoCapture(url)

        if not cap.isOpened():
            print(f"FAILED: {name}")
            continue

        caps[name] = cap
        print(f"Started: {name}")

    try:
        while True:

            for name, cap in caps.items():

                ret, frame = cap.read()

                if not ret:
                    print(f"Frame failed: {name}")
                    continue

                if display:
                    cv2.imshow(name, frame)

            if display and cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:

        for cap in caps.values():
            cap.release()

        if display:
            cv2.destroyAllWindows()


run_opencv(display=False)