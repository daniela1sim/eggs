# learn_drone_zone.py
import json, time, math
from pathlib import Path
import pyautogui, keyboard
from pywinauto import Desktop

POS_DIR = Path("eggs/game/pos")
POS_DIR.mkdir(parents=True, exist_ok=True)
ZONE_FILE = POS_DIR / "drone_zone.json"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02

def _bs_win():
    wins = Desktop(backend="uia").windows(title_re=r".*BlueStacks.*")
    if not wins:
        raise RuntimeError("Open BlueStacks first.")
    return wins[0]

def _bs_rect():
    r = _bs_win().rectangle()
    return r.left, r.top, r.right, r.bottom  # L,T,R,B

def _abs_to_rel(x, y):
    L,T,R,B = _bs_rect()
    W, H = R-L, B-T
    return ( (x - L) / W, (y - T) / H )

def main():
    print(
        "Teach the drone circle:\n"
        "  1) Hover the CIRCLE CENTER → press F11.\n"
        "  2) Hover anywhere on the CIRCLE EDGE → press F12.\n"
        "Ctrl+C to cancel.\n"
    )
    center_rel = None
    radius_rel = None

    while True:
        if keyboard.is_pressed("F11"):
            x, y = pyautogui.position()
            cx_rel, cy_rel = _abs_to_rel(x, y)
            center_rel = (cx_rel, cy_rel)
            print(f"Saved center (rel): {center_rel}")
            time.sleep(0.5)

        if keyboard.is_pressed("F12"):
            if not center_rel:
                print("Please set the center first (F11).")
                time.sleep(0.5)
                continue
            x, y = pyautogui.position()
            L,T,R,B = _bs_rect()
            W, H = R-L, B-T
            cx = L + center_rel[0]*W
            cy = T + center_rel[1]*H
            # radius relative to the SHORT side (stable with aspect changes)
            r_px = math.hypot(x - cx, y - cy)
            radius_rel = r_px / min(W, H)
            print(f"Saved radius (rel): {radius_rel:.4f}")
            # commit to file
            ZONE_FILE.write_text(json.dumps(
                {"center": {"x": center_rel[0], "y": center_rel[1]}, "radius_rel": radius_rel},
                indent=2
            ))
            print(f"Saved → {ZONE_FILE.resolve()}")
            time.sleep(0.8)
            break

        time.sleep(0.05)

if __name__ == "__main__":
    main()
