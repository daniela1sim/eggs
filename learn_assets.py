# learn_assets.py  (ADD the new constants + hotkeys)
import time
from pathlib import Path
import pyautogui, keyboard
from pywinauto import Desktop

POS_DIR = Path("eggs/game/pos")
POS_DIR.mkdir(parents=True, exist_ok=True)

HOME_BTN      = POS_DIR / "home_btn.png"
GAME_ICON     = POS_DIR / "game_icon.png"
GIFT_ICON     = POS_DIR / "gift_icon.png"
COLLECT_BTN   = POS_DIR / "collect_btn.png"
AD_ICON       = POS_DIR / "ad_icon.png"

# NEW:
NO_THANKS_BTN = POS_DIR / "no_thanks.png"   # red "NO THANKS" on ad popup
TOKEN_OFFER   = POS_DIR / "token_offer.png" # the gold token coin on ad popup

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02

def _bs_rect():
    wins = Desktop(backend="uia").windows(title_re=r".*BlueStacks.*")
    if not wins: raise RuntimeError("Open BlueStacks first.")
    r = wins[0].rectangle()
    return r.left, r.top, r.right, r.bottom

def _snap_under_cursor(path: Path, pad_px: int = 28):
    L, T, R, B = _bs_rect()
    x, y = pyautogui.position()
    x = max(L+pad_px, min(x, R-pad_px))
    y = max(T+pad_px, min(y, B-pad_px))
    shot = pyautogui.screenshot(region=(x-pad_px, y-pad_px, pad_px*2, pad_px*2))
    shot.save(path)
    print(f"Saved → {path.resolve()}")

if __name__ == "__main__":
    print(
        "Learning hotkeys (hover target in BlueStacks, then press):\n"
        "  F5  = HOME button (top bar)\n"
        "  F6  = GAME icon on home\n"
        "  F8  = in-game GIFT icon\n"
        "  F9  = COLLECT button (gift popup)\n"
        "  F10 = AD icon (play triangle circle)\n"
        "  F7  = NO THANKS (ad popup)\n"
        "  F11 = TOKEN OFFER (hover the gold token coin on ad popup)\n"
        "Ctrl+C to quit.\n"
    )
    while True:
        if keyboard.is_pressed("F5"):  _snap_under_cursor(HOME_BTN);      time.sleep(0.5)
        if keyboard.is_pressed("F6"):  _snap_under_cursor(GAME_ICON);     time.sleep(0.5)
        if keyboard.is_pressed("F8"):  _snap_under_cursor(GIFT_ICON);     time.sleep(0.5)
        if keyboard.is_pressed("F9"):  _snap_under_cursor(COLLECT_BTN);   time.sleep(0.5)
        if keyboard.is_pressed("F10"): _snap_under_cursor(AD_ICON);       time.sleep(0.5)
        if keyboard.is_pressed("F7"):  _snap_under_cursor(NO_THANKS_BTN); time.sleep(0.5)   # NEW
        if keyboard.is_pressed("F11"): _snap_under_cursor(TOKEN_OFFER);   time.sleep(0.5)   # NEW
        time.sleep(0.05)
