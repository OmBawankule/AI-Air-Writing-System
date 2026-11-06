import cv2
import mediapipe as mp
import numpy as np
import pytesseract
import time

# ---------------- CONFIGURATION ----------------
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
CAMERA_INDEX = 0
BRUSH_THICKNESS = 12
SMOOTHING = 0.28
# ------------------------------------------------

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.70,
    min_tracking_confidence=0.70
)

cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam. Close other camera apps or change CAMERA_INDEX.")

canvas = None
previous_point = None
smooth_point = None
recognized_text = "Write with index finger, make a fist to recognize"
last_gesture = "READY"
last_ocr_time = 0
fist_frames = 0
palm_frames = 0
clear_cooldown_until = 0
ocr_cooldown_until = 0

def finger_is_up(landmarks, tip_id, pip_id):
    # For index/middle/ring/pinky, compare fingertip with middle joint.
    return landmarks[tip_id].y < landmarks[pip_id].y

def classify_gesture(landmarks):
    index_up = finger_is_up(landmarks, 8, 6)
    middle_up = finger_is_up(landmarks, 12, 10)
    ring_up = finger_is_up(landmarks, 16, 14)
    pinky_up = finger_is_up(landmarks, 20, 18)

    # Palm: four fingers extended. Thumb is intentionally ignored because
    # thumb orientation varies with hand rotation and camera mirroring.
    if index_up and middle_up and ring_up and pinky_up:
        return "PALM"

    # Index-only writing pose
    if index_up and not middle_up and not ring_up and not pinky_up:
        return "WRITE"

    # Closed fist
    if not index_up and not middle_up and not ring_up and not pinky_up:
        return "FIST"

    return "MOVE"

def recognize_canvas(drawing):
    gray = cv2.cvtColor(drawing, cv2.COLOR_BGR2GRAY)
    # Crop to the written area, add margin, and invert to black text on white.
    coords = cv2.findNonZero(gray)
    if coords is None:
        return "No writing detected"

    x, y, w, h = cv2.boundingRect(coords)
    crop = gray[y:y+h, x:x+w]
    crop = cv2.copyMakeBorder(crop, 40, 40, 40, 40,
                              cv2.BORDER_CONSTANT, value=0)
    crop = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, binary = cv2.threshold(crop, 30, 255, cv2.THRESH_BINARY)
    # Tesseract expects dark text on a light background.
    binary = cv2.bitwise_not(binary)
    config = "--oem 3 --psm 6"
    result = pytesseract.image_to_string(binary, config=config).strip()
    return " ".join(result.split()) if result else "Text not recognized - write larger and clearer"

window_name = "AI Air Writing - Camera"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Could not read webcam frame.")
            break

        frame = cv2.flip(frame, 1)
        height, width = frame.shape[:2]

        if canvas is None:
            canvas = np.zeros((height, width, 3), dtype=np.uint8)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)
        now = time.time()
        gesture = "NO HAND"

        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            lm = hand.landmark
            gesture = classify_gesture(lm)

            # Draw landmarks on camera image for visual feedback.
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            if gesture == "WRITE":
                x = int(np.clip(lm[8].x * width, 0, width - 1))
                y = int(np.clip(lm[8].y * height, 0, height - 1))

                if smooth_point is None:
                    smooth_point = (x, y)
                else:
                    sx = int(SMOOTHING * x + (1 - SMOOTHING) * smooth_point[0])
                    sy = int(SMOOTHING * y + (1 - SMOOTHING) * smooth_point[1])
                    smooth_point = (sx, sy)

                if previous_point is not None:
                    cv2.line(canvas, previous_point, smooth_point,
                             (255, 255, 255), BRUSH_THICKNESS, cv2.LINE_AA)
                cv2.circle(canvas, smooth_point, BRUSH_THICKNESS // 2,
                           (255, 255, 255), -1, cv2.LINE_AA)
                previous_point = smooth_point
                last_gesture = "WRITING"
                palm_frames = 0
                fist_frames = 0

            elif gesture == "PALM":
                previous_point = None
                smooth_point = None
                palm_frames += 1
                fist_frames = 0
                last_gesture = "OPEN PALM - CLEAR"
                if palm_frames >= 5 and now >= clear_cooldown_until:
                    canvas[:] = 0
                    recognized_text = ""
                    clear_cooldown_until = now + 1.0
                    palm_frames = 0

            elif gesture == "FIST":
                previous_point = None
                smooth_point = None
                fist_frames += 1
                palm_frames = 0
                last_gesture = "FIST - RECOGNIZING"
                if fist_frames >= 8 and now >= ocr_cooldown_until:
                    try:
                        recognized_text = recognize_canvas(canvas)
                    except pytesseract.TesseractNotFoundError:
                        recognized_text = "Tesseract not found: check TESSERACT_PATH"
                    except Exception as exc:
                        recognized_text = f"OCR error: {exc}"
                    ocr_cooldown_until = now + 2.0
                    fist_frames = 0

            else:
                previous_point = None
                smooth_point = None
                palm_frames = 0
                fist_frames = 0
                last_gesture = "MOVE / PAUSE"
        else:
            previous_point = None
            smooth_point = None
            palm_frames = 0
            fist_frames = 0

        # Camera + white strokes
        display = cv2.add(frame, canvas)

        # Top status panel
        cv2.rectangle(display, (0, 0), (width, 125), (20, 20, 20), -1)
        cv2.putText(display, "INDEX: WRITE   |   OPEN PALM: CLEAR   |   FIST: CONVERT TO TEXT",
                    (25, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(display, f"GESTURE: {last_gesture}",
                    (25, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

        # Text output panel
        panel_y = height - 105
        cv2.rectangle(display, (0, panel_y), (width, height), (15, 15, 15), -1)
        cv2.putText(display, "RECOGNIZED TEXT:",
                    (25, panel_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 255), 2, cv2.LINE_AA)

        # Keep output readable; wrap long text over two lines.
        text = recognized_text if recognized_text else "(Your recognized text will appear here)"
        max_chars = max(20, int(width / 18))
        lines = [text[i:i + max_chars] for i in range(0, len(text), max_chars)][:2]
        for i, line in enumerate(lines):
            cv2.putText(display, line, (25, panel_y + 72 + i * 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (80, 255, 80), 2, cv2.LINE_AA)

        cv2.imshow(window_name, display)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key in (ord('c'), ord('C')):
            canvas[:] = 0
            recognized_text = ""
            previous_point = None
            smooth_point = None
        elif key in (ord('r'), ord('R')):
            try:
                recognized_text = recognize_canvas(canvas)
            except Exception as exc:
                recognized_text = f"OCR error: {exc}"

finally:
    cap.release()
    hands.close()
    cv2.destroyAllWindows()
