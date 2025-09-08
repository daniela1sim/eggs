# run_watcher.py  (REPLACE your existing with this)
import os, time
from pathlib import Path
from typing import Tuple, Optional, List

import cv2, numpy as np, pyautogui
from pywinauto import Desktop
from mouse import Mouse
from launcher import open_bluestacks_fullscreen, tap_home_button, tap_game_icon

POS_DIR       = Path("eggs/game/pos")
GIFT_ICON     = POS_DIR / "gift_icon.png"
COLLECT_BTN   = POS_DIR / "collect_btn.png"
AD_ICON       = POS_DIR / "ad_icon.png"
GAME_ICON     = POS_DIR / "game_icon.png"   # home detection
NO_THANKS_BTN = POS_DIR / "no_thanks.png"   # NEW
TOKEN_OFFER   = POS_DIR / "token_offer.png" # NEW
RING_FILE     = POS_DIR / "notify.wav"

SCAN_PERIOD       = 60.0
GIFT_THRESHOLD    = 0.84
COLLECT_THRESHOLD = 0.86
AD_THRESHOLD      = 0.86
HOME_THRESHOLD    = 0.86
NO_THANKS_THR     = 0.86
TOKEN_THR         = 0.88

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02
M = Mouse()

# ---------- BlueStacks & regions ----------
def _bs_win():
    wins = Desktop(backend="uia").windows(title_re=r".*BlueStacks.*")
    if not wins: raise RuntimeError("Open BlueStacks first.")
    return wins[0]

def _bs_rect() -> Tuple[int,int,int,int]:
    r = _bs_win().rectangle()
    return r.left, r.top, r.right, r.bottom

def _region_top_right():
    L,T,R,B = _bs_rect(); W,H = (R-L),(B-T)
    return (int(L+0.60*W), int(T+0.00*H), int(0.40*W), int(0.50*H))

def _region_center_modal():
    # where ad/gift popups live
    L,T,R,B = _bs_rect(); W,H = (R-L),(B-T)
    return (int(L+0.20*W), int(T+0.22*H), int(0.60*W), int(0.56*H))

def _region_home_grid():
    L,T,R,B = _bs_rect(); W,H = (R-L),(B-T)
    return (int(L+0.10*W), int(T+0.15*H), int(0.65*W), int(0.60*H))

# ---------- vision ----------
def _grab(region):
    L,T,W,H = region
    img = pyautogui.screenshot(region=(L,T,W,H))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def _best_match(scene, templ, scales):
    best = (None, -1.0, 1.0)
    th, tw = templ.shape[:2]
    for s in [0.85,0.90,0.95,1.00,1.05,1.10]:
        h, w = max(8,int(th*s)), max(8,int(tw*s))
        if h>=scene.shape[0] or w>=scene.shape[1]: continue
        t = cv2.resize(templ, (w,h), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(scene, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if mx>best[1]: best = (loc, mx, s)
    return best

def _center_of(template_path: Path, region, threshold: float):
    if not template_path.exists(): return None
    templ = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if templ is None: return None
    scene = _grab(region)
    loc, score, s = _best_match(scene, templ, [0.85,0.90,0.95,1.00,1.05,1.10])
    if loc is None or score < threshold: return None
    th, tw = templ.shape[:2]
    cx = region[0] + int(loc[0] + (tw*s)/2)
    cy = region[1] + int(loc[1] + (th*s)/2)
    return (cx, cy, score)

def _find_gift():      return _center_of(GIFT_ICON,     _region_top_right(),  GIFT_THRESHOLD)
def _find_collect():   return _center_of(COLLECT_BTN,   _region_center_modal(), COLLECT_THRESHOLD)
def _find_ad():        return _center_of(AD_ICON,       _region_top_right(),  AD_THRESHOLD)
def _find_home_game(): return _center_of(GAME_ICON,     _region_home_grid(),  HOME_THRESHOLD)
def _find_no_thanks(): return _center_of(NO_THANKS_BTN, _region_center_modal(), NO_THANKS_THR)
def _find_token():     return _center_of(TOKEN_OFFER,   _region_center_modal(), TOKEN_THR)

# ---------- ringtone ----------
def _ring_and_exit():
    try:
        if RING_FILE.exists():
            import winsound
            winsound.PlaySound(str(RING_FILE), winsound.SND_FILENAME | winsound.SND_ASYNC)
            time.sleep(2.0)
        else:
            import winsound
            winsound.Beep(880, 220); winsound.Beep(660, 220); winsound.Beep(1046, 260)
    except Exception:
        print("\a\a\a", end="", flush=True); time.sleep(1.0)
    print("Token ad detected → clicked. Exiting.")
    os._exit(0)

# ---------- recovery ----------
def ensure_game_open():
    # If the home grid is visible (game icon present), reopen the game.
    pos = _find_home_game()
    if pos:
        try:
            tap_home_button()
        except Exception:
            pass
        x,y,_ = pos
        M.click_pos((x,y), sleep_time=0.25, once=True)
        time.sleep(2.5)
        return True
    return False

# ---------- actions ----------
def click_gift_then_collect() -> bool:
    pos = _find_gift()
    if not pos: return False
    x,y,_ = pos
    M.click_pos((x,y), sleep_time=0.15, once=True)
    time.sleep(2.0)
    c = _find_collect()
    if c:
        cx,cy,_ = c
        M.click_pos((cx,cy), sleep_time=0.2, once=True)
        print("Gift collected.")
    else:
        print("COLLECT not found.")
    return True

def handle_ad_flow() -> bool:
    """
    If ad icon is present:
      - tap ad icon
      - wait 1s for the popup
      - if TOKEN offer is detected: ringtone + exit
      - else: tap NO THANKS if present (and continue running)
    Returns True if an ad was handled (token or not), False if no ad.
    """
    pos = _find_ad()
    if not pos:
        return False

    # tap the ad circle
    x,y,_ = pos
    M.click_pos((x,y), sleep_time=0.15, once=True)
    time.sleep(1.0)  # let the popup appear

    # Check for token offer
    tok = _find_token()
    if tok:
        _ring_and_exit()

    # Not a token: tap NO THANKS if we can find it
    nt = _find_no_thanks()
    if nt:
        nx,ny,_ = nt
        M.click_pos((nx,ny), sleep_time=0.2, once=True)
        print("Non-token ad → NO THANKS tapped.")
    else:
        print("Non-token ad, but NO THANKS not found.")

    return True

# ---------- main loop ----------
def run():
    open_bluestacks_fullscreen()
    try:
        tap_home_button()
    except Exception:
        pass
    ensure_game_open()

    print("Watcher started (every 60s). Ctrl+C to stop.")
    while True:
        try:
            if ensure_game_open():
                time.sleep(3.0)

            # PRIORITY: ads
            if handle_ad_flow():
                # if token → function has already exited; otherwise keep running
                time.sleep(2.0)

            # gifts
            clicked = click_gift_then_collect()
            time.sleep(SCAN_PERIOD if not clicked else 5.0)

        except KeyboardInterrupt:
            print("Stopped by user."); return
        except Exception as e:
            print(f"[warn] {e}")
            time.sleep(SCAN_PERIOD)

if __name__ == "__main__":
    run()