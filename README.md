# Egg Inc Automations (BlueStacks + Python)

Small utilities to automate a few repetitive actions in **Egg, Inc.** running inside **BlueStacks** on Windows:
- Launch BlueStacks, toggle fullscreen, go **Home**, and open the game
- Watch for **gift** icon → open → **COLLECT**
- Watch for **ad** icon → if the popup is a **Boost Token** offer → play a ringtone & exit, otherwise press **NO THANKS**
- Tap **drones** that pass through a learned circular zone
- Auto-reopen the game if it crashes back to the BlueStacks **home screen**

---

## Folder layout

```
project/
├─ mouse.py                  # your click helper (used everywhere)
├─ mouse_coordinate.py       # optional: prints live mouse coords
├─ launcher.py               # open BlueStacks → fullscreen → tap Home → (function) tap game icon
├─ learn_assets.py           # learn/save templates (icons/buttons)
├─ run_watcher.py            # gifts + ad token logic (+ auto-reopen on crash)
├─ learn_drone_zone.py       # learn center+radius of drone tap zone
├─ run_drone_tapper.py       # motion-detect drones in the zone and click
├─ requirements.txt
└─ eggs/
   └─ game/
      └─ pos/
         ├─ home_btn.png
         ├─ game_icon.png
         ├─ gift_icon.png
         ├─ collect_btn.png
         ├─ ad_icon.png
         ├─ no_thanks.png
         ├─ token_offer.png
         ├─ drone_zone.json
         └─ notify.wav          # (optional ringtone)
```

All learned assets + ringtone live in `eggs/game/pos/`. The scripts create the folder automatically if it doesn’t exist.

---

## Prerequisites

- Windows 10/11
- Python 3.9+ (64-bit recommended)
- BlueStacks installed (NXT/5)  
- BlueStacks window must be **visible** (not minimized)

Install Python deps:

```bash
pip install -r requirements.txt
```

---

## 1) Learn templates (one-time)

Open BlueStacks and the game. Then run:

```bash
python learn_assets.py
```

While hovering the target in BlueStacks, press the hotkeys:

- **F5** → save **Home** button (top bar, BlueStacks UI)  
- **F6** → save **Game icon** on the BlueStacks **home screen** (Egg, Inc.)  
- **F8** → save in-game **Gift** circle (box in a circle, top-right)  
- **F9** → save **COLLECT** button (open a gift first)  
- **F10** → save **Ad** circle (play triangle, top-right)  
- **F7** → save **NO THANKS** (red button on ad popup)  
- **F11** → save **Token** coin on the ad popup (hover the golden coin)

> Tip: Each save grabs a small 56×56 crop under the cursor, anchored to the BlueStacks window.

Optional ringtone: add a short WAV at `eggs/game/pos/notify.wav`.

---

## 2) Open BlueStacks + Home + Game

To simply open and land in game:

```bash
python launcher.py
```

From code, you can reuse:

```python
from launcher import open_bluestacks_fullscreen, tap_home_button, tap_game_icon
open_bluestacks_fullscreen()
tap_home_button()
tap_game_icon()
```

---

## 3) Gifts & Ads watcher (with auto-reopen)

Runs every 60 seconds:
- If **ad** icon is present → tap → wait 1s → inspect the popup:
  - **Token detected** → play ringtone and **exit** (so you can watch the ad)
  - **Not token** → tap **NO THANKS** and continue
- Else, if **gift** icon is present → tap → wait 2s → tap **COLLECT**
- If the game crashes back to **home**, it reopens it by recognizing your **game icon**

```bash
python run_watcher.py
```

### Tuning (edit constants at top of `run_watcher.py`)
- `SCAN_PERIOD` (default **60.0** seconds)
- Template thresholds: `GIFT_THRESHOLD`, `COLLECT_THRESHOLD`, `AD_THRESHOLD`, `TOKEN_THR`, `NO_THANKS_THR`
- Ringtone path: `eggs/game/pos/notify.wav`

---

## 4) Drone tapper

### Learn the zone (one-time)
Pick the circle on screen where you want to catch drones.

```bash
python learn_drone_zone.py
```

- Hover **center** of the circle → press **F11**
- Hover **edge** of the circle → press **F12**

This saves `drone_zone.json` with **relative** center+radius (resolution-independent).

### Run the tapper
```bash
python run_drone_tapper.py
```

It samples ~14 FPS in that circle and clicks when a moving blob (drone) passes through.

Tuning (top of `run_drone_tapper.py`):
- `FPS`, `THRESH_DELTA`, `MIN_MOTION_FRACTION`, `CLICK_COOLDOWN_S`, `BLUR_KSIZE`

---

## Troubleshooting

- **Template not found / misses clicks**
  - Re-learn that template (`learn_assets.py`) with a tighter crop (hover dead center).
  - Raise/lower the corresponding threshold in `run_watcher.py`.
- **Different UI scale**
  - Templates are matched multi-scale; if you resized BlueStacks or changed DPI, re-learn quickly.
- **Failsafe triggers instantly**
  - `pyautogui.FAILSAFE = True` aborts if the mouse hits a screen corner; avoid corners while running.
- **BlueStacks not detected**
  - Ensure the BlueStacks window is **open and visible** (not minimized).
- **Sound doesn’t play**
  - Provide a `.wav` at `eggs/game/pos/notify.wav`. `winsound` plays WAV only.

---

## Notes

- All clicks go through `mouse.py` (`Mouse.click_pos(..., once=True)`), so taps are single-clicks by default.
- No ADB required for this flow (pure UI automation).  
- If the game UI changes, simply re-run `learn_assets.py`.

---

## Safety & ToS

Automation may violate some games’ or platforms’ terms. Use at your own risk and only for personal/testing purposes.
