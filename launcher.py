# launcher.py
import time, subprocess
from pathlib import Path
from typing import Tuple, Optional, List

import cv2, numpy as np, pyautogui
from pywinauto import Desktop
from pywinauto.keyboard import send_keys
from mouse import Mouse  # your util

POS_DIR   = Path("eggs/game/pos")
HOME_BTN  = POS_DIR / "home_btn.png"
GAME_ICON = POS_DIR / "game_icon.png"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02
M = Mouse()

# ---------- BlueStacks window ----------
def _find_bs():
    wins = Desktop(backend="uia").windows(title_re=r".*BlueStacks.*")
    return wins[0] if wins else None

def _bs_rect() -> Tuple[int,int,int,int]:
    r = _find_bs().rectangle()
    return r.left, r.top, r.right, r.bottom

def _is_fullscreen(win) -> bool:
    import ctypes
    rect = win.rectangle()
    u = ctypes.windll.user32
    return rect.left == 0 and rect.top == 0 and rect.width() == u.GetSystemMetrics(0) and rect.height() == u.GetSystemMetrics(1)

def open_bluestacks_fullscreen(timeout_sec: int = 60, instance: Optional[str] = None):
    win = _find_bs()
    if not win:
        for p in [
            r"C:\Program Files\BlueStacks_nxt\HD-Player.exe",
            r"C:\Program Files\BlueStacks5\HD-Player.exe",
            r"C:\Program Files\BlueStacks\HD-Player.exe",
            r"C:\Program Files (x86)\BlueStacks_nxt\HD-Player.exe",
            r"C:\Program Files (x86)\BlueStacks\HD-Player.exe",
        ]:
            if Path(p).exists():
                subprocess.Popen([p] + (["--instance", instance] if instance else []),
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                break
        deadline = time.time() + timeout_sec
        while time.time() < deadline and not win:
            win = _find_bs(); time.sleep(1)
        if not win: raise RuntimeError("BlueStacks window not found.")
    win.set_focus(); time.sleep(0.3)
    if not _is_fullscreen(win):
        send_keys("{F11}"); time.sleep(0.5)
    win.set_focus()

# ---------- image search ----------
def _grab(region):  # region=(L,T,W,H)
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

def _center_of_match(template_path: Path, region, threshold: float) -> Optional[Tuple[int,int,float]]:
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

def _region_top_bar():
    L,T,R,B = _bs_rect(); W,H = (R-L),(B-T)
    return (L, T, W, int(0.10*H))  # top ~10%

def _region_home_grid():
    L,T,R,B = _bs_rect(); W,H = (R-L),(B-T)
    # central grid area (avoid the ad rail on the right)
    return (int(L+0.10*W), int(T+0.15*H), int(0.65*W), int(0.60*H))

# ---------- exported actions ----------
def tap_home_button(threshold: float = 0.86):
    pos = _center_of_match(HOME_BTN, _region_top_bar(), threshold)
    if not pos: raise RuntimeError("HOME button template not found on screen. Re-learn it.")
    x,y,_ = pos
    M.click_pos((x,y), sleep_time=0.15, once=True)

def tap_game_icon(threshold: float = 0.86):
    pos = _center_of_match(GAME_ICON, _region_home_grid(), threshold)
    if not pos: raise RuntimeError("GAME icon template not found on home grid. Re-learn it.")
    x,y,_ = pos
    M.click_pos((x,y), sleep_time=0.2, once=True)

# ---------- simple script behavior ----------
if __name__ == "__main__":
    open_bluestacks_fullscreen()
    tap_home_button()
    tap_game_icon()
