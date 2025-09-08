# run_drone_tapper.py
import json, time, math
from pathlib import Path
from typing import Tuple, Optional

import cv2
import numpy as np
import pyautogui
from pywinauto import Desktop
from mouse import Mouse
from launcher import open_bluestacks_fullscreen  # optional, to ensure window exists

POS_DIR   = Path("eggs/game/pos")
ZONE_FILE = POS_DIR / "drone_zone.json"

# ---- tuning ----
FPS                 = 14             # how often we check (frames per second)
MIN_MOTION_FRACTION = 0.0010         # min moving area (fraction of ROI area) to register as a drone
CLICK_COOLDOWN_S    = 0.60           # don’t click more often than this
BLUR_KSIZE          = 5              # gaussian blur kernel (odd)
THRESH_DELTA        = 22             # threshold for frame diff (0-255)
MORPH_KERNEL        = 3              # morphology kernel size (pixels)
# -----------------

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01
M = Mouse()

def _bs_win():
    wins = Desktop(backend="uia").windows(title_re=r".*BlueStacks.*")
    if not wins:
        raise RuntimeError("Open BlueStacks first.")
    return wins[0]

def _bs_rect():
    r = _bs_win().rectangle()
    return r.left, r.top, r.right, r.bottom  # L,T,R,B

def _rel_to_abs(center_rel: Tuple[float,float], radius_rel: float) -> Tuple[int,int,int]:
    """Return (cx, cy, r) in absolute screen pixels, clamped to BlueStacks."""
    L,T,R,B = _bs_rect()
    W, H = R-L, B-T
    cx = int(L + center_rel[0]*W)
    cy = int(T + center_rel[1]*H)
    r  = int(radius_rel * min(W, H))
    # clamp radius to fit inside window
    r = max(8, min(r, min(cx-L, cy-T, R-cx, B-cy)))
    return cx, cy, r

def _roi_bounds(cx:int, cy:int, r:int) -> Tuple[int,int,int,int]:
    """Return ROI rectangle (L,T,W,H) covering the circle."""
    L = cx - r; T = cy - r; W = r*2; H = r*2
    return L, T, W, H

def _grab(L:int, T:int, W:int, H:int) -> np.ndarray:
    img = pyautogui.screenshot(region=(L,T,W,H))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def _prep_gray(frame_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    if BLUR_KSIZE >= 3:
        gray = cv2.GaussianBlur(gray, (BLUR_KSIZE, BLUR_KSIZE), 0)
    return gray

def _circular_mask(h:int, w:int) -> np.ndarray:
    mask = np.zeros((h,w), dtype=np.uint8)
    cv2.circle(mask, (w//2, h//2), min(h,w)//2, 255, -1)
    return mask

def run():
    if not ZONE_FILE.exists():
        raise FileNotFoundError(f"Drone zone not learned. Run learn_drone_zone.py first (missing {ZONE_FILE}).")
    zone = json.loads(ZONE_FILE.read_text())
    center_rel = (zone["center"]["x"], zone["center"]["y"])
    radius_rel = float(zone["radius_rel"])

    # Make sure BlueStacks is in focus / measured correctly (optional but handy)
    try:
        open_bluestacks_fullscreen()
    except Exception:
        pass

    cx, cy, r = _rel_to_abs(center_rel, radius_rel)
    L, T, W, H = _roi_bounds(cx, cy, r)
    mask = _circular_mask(H, W)
    roi_area = math.pi * (min(W,H)/2)**2

    print(f"Watching circle at center=({cx},{cy}) r={r}px  (Ctrl+C to stop)")
    prev_gray = None
    last_click_t = 0.0
    period = 1.0 / max(6, FPS)

    while True:
        try:
            frame = _grab(L,T,W,H)
            gray  = _prep_gray(frame)

            if prev_gray is None:
                prev_gray = gray
                time.sleep(period)
                continue

            diff = cv2.absdiff(gray, prev_gray)
            prev_gray = gray

            # apply circular mask to focus inside the zone only
            diff = cv2.bitwise_and(diff, diff, mask=mask)

            _, th = cv2.threshold(diff, THRESH_DELTA, 255, cv2.THRESH_BINARY)
            if MORPH_KERNEL >= 3:
                k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (MORPH_KERNEL, MORPH_KERNEL))
                th = cv2.morphologyEx(th, cv2.MORPH_OPEN, k, iterations=1)
                th = cv2.morphologyEx(th, cv2.MORPH_DILATE, k, iterations=1)

            cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not cnts:
                time.sleep(period)
                continue

            # biggest moving blob
            cnt = max(cnts, key=cv2.contourArea)
            area = cv2.contourArea(cnt)
            if area < (MIN_MOTION_FRACTION * roi_area):
                time.sleep(period); continue

            # centroid of motion
            Mmom = cv2.moments(cnt)
            if Mmom["m00"] == 0:
                time.sleep(period); continue
            ux = int(Mmom["m10"]/Mmom["m00"])
            uy = int(Mmom["m01"]/Mmom["m00"])

            now = time.time()
            if (now - last_click_t) >= CLICK_COOLDOWN_S:
                # translate back to absolute screen coords
                click_x = L + ux
                click_y = T + uy
                from_center = math.hypot(ux - W/2, uy - H/2)
                if from_center <= (min(W,H)/2):  # inside circle guard
                    M.click_pos((click_x, click_y), sleep_time=0.05, once=True)
                    last_click_t = now
                    # small settle to avoid immediate double clicks
                    time.sleep(max(0.02, period))

            time.sleep(period)

        except KeyboardInterrupt:
            print("Stopped.")
            return
        except Exception as e:
            print(f"[warn] {e}")
            time.sleep(period)

if __name__ == "__main__":
    run()
