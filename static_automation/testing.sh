#!/bin/bash

BOLD_GREEN=$'\033[1;32m'
BOLD_BLUE=$'\033[1;34m'
BOLD_RED=$'\033[1;31m'
RESET=$'\033[0m'

export PATH="$PATH:/home/carlos/Android/Sdk/platform-tools"

install_apk() {
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local APK_PATH=$(find "$SCRIPT_DIR/.." -maxdepth 1 -name "*.apk" | head -n 1)

    if [ -z "$APK_PATH" ]; then
        echo -e "${BOLD_RED}❌ Error: No APK found.${RESET}"
        return 1
    fi

    echo -e "${BOLD_BLUE}Installing APK: $APK_PATH...${RESET}"
    adb install -r "$APK_PATH"
}

# --- FUNCTION 2: Launch App using EasyOCR on Host Screenshot ---
launch_test_app() {
    local TARGET_APP="NavUiAct"
    echo -e "${BOLD_BLUE}Searching for app icon on home screen...${RESET}"

    python3 - "$TARGET_APP" <<'EOF'
import sys
import os
import tempfile
import time
import subprocess
import easyocr

def host_screenshot(screenshot_path: str):
    import pyscreenshot
    img = pyscreenshot.grab()
    img.save(screenshot_path)

def host_click(x: int, y: int):
    if sys.platform.startswith("linux"):
        # ydotoold's absolute coordinate space defaults to 1920x1080.
        # GNOME Wayland maps this tablet preserving aspect ratio. 
        # Since 3840/1920 = 2.0, both X and Y are scaled physically by 2.0.
        # To map from 2560x1600 logical space, the multiplier is exactly 0.75 for both axes!
        ydotool_x = int(x * 0.75)
        ydotool_y = int(y * 0.75)
        print(f" -> Using ydotool for Linux Wayland click mapped to ydotoold ({ydotool_x}, {ydotool_y})")
        
        subprocess.run(["ydotool", "mousemove", "-a", "-x", str(ydotool_x), "-y", str(ydotool_y)], check=False)
        time.sleep(0.2)
        subprocess.run(["ydotool", "key", "272:1"], check=False)
        time.sleep(0.1)
        subprocess.run(["ydotool", "key", "272:0"], check=False)
    else:
        import pyautogui
        print(f" -> Using PyAutoGUI for {sys.platform} click at ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.2)
        pyautogui.click()

target_text = sys.argv[1]
try:
    temp_dir = tempfile.gettempdir()
    screenshot_path = os.path.join(temp_dir, "launcher_ocr.png")
    
    host_screenshot(screenshot_path)
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = reader.readtext(screenshot_path)

    matches = []
    for (bbox, text, prob) in results:
        # Strict exact match to avoid clicking the terminal window's output!
        if target_text.lower() == text.strip().lower():
            matches.append(bbox)

    found_bbox = None
    if matches:
        # Sort by Y descending to prefer the actual emulator icon over terminal output which is usually higher up
        matches.sort(key=lambda b: (b[0][1], b[0][0]), reverse=True)
        found_bbox = matches[0]

    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)

    if found_bbox is None:
        print(f"❌ FAILURE: Could not find '{target_text}'.")
        sys.exit(1)

    raw_x = int((found_bbox[0][0] + found_bbox[2][0]) / 2)
    raw_y = int((found_bbox[0][1] + found_bbox[2][1]) / 2)

    host_click(raw_x, raw_y)
    print(f"✅ Launched {target_text}")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF
}

# --- FUNCTION 3: Click Bottom Navigation Items ---
click_bottom_navigation() {
    local NAV_ITEMS=("Home" "Favorites" "Profile")
    
    for item in "${NAV_ITEMS[@]}"; do
        echo -e "${BOLD_BLUE}Navigating to Bottom Tab...${RESET}"
        
        python3 - "$item" <<'EOF'
import sys
import os
import tempfile
import time
import subprocess
import easyocr

def host_screenshot(screenshot_path: str):
    import pyscreenshot
    img = pyscreenshot.grab()
    w, h = img.size
    crop_x = int(w * 0.10)
    cropped_img = img.crop((crop_x, 0, w, h))
    cropped_img.save(screenshot_path)
    return crop_x

def host_click(x: int, y: int):
    if sys.platform.startswith("linux"):
        # GNOME Wayland preserves aspect ratio, scale is 0.75 for both axes.
        ydotool_x = int(x * 0.75)
        ydotool_y = int(y * 0.75)
        print(f" -> Using ydotool for Linux Wayland click mapped to ydotoold ({ydotool_x}, {ydotool_y})")
        
        subprocess.run(["ydotool", "mousemove", "-a", "-x", str(ydotool_x), "-y", str(ydotool_y)], check=False)
        time.sleep(0.2)
        subprocess.run(["ydotool", "key", "272:1"], check=False)
        time.sleep(0.1)
        subprocess.run(["ydotool", "key", "272:0"], check=False)
    else:
        import pyautogui
        print(f" -> Using PyAutoGUI for {sys.platform} click at ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.2)
        pyautogui.click()

target_text = sys.argv[1]
try:
    temp_dir = tempfile.gettempdir()
    screenshot_path = os.path.join(temp_dir, "nav_items_ocr.png")
    
    crop_offset_x = host_screenshot(screenshot_path)
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = reader.readtext(screenshot_path)

    matches = []
    for (bbox, text, prob) in results:
        # Strict exact match to avoid clicking the terminal window's output!
        if target_text.lower() == text.strip().lower():
            matches.append(bbox)

    found_bbox = None
    if matches:
        matches.sort(key=lambda b: (b[0][1], b[0][0]), reverse=True)
        found_bbox = matches[0]

    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)

    if found_bbox is None:
        print(f"⚠️ Could not find tab: {target_text}")
        sys.exit(0)

    raw_x = int((found_bbox[0][0] + found_bbox[2][0]) / 2) + crop_offset_x
    raw_y = int((found_bbox[0][1] + found_bbox[2][1]) / 2)
    
    host_click(raw_x, raw_y)
    print(f"✅ Clicked {target_text}")
    time.sleep(1.5)

except Exception as e:
    print(f"❌ Error during Nav: {e}")
EOF
    done
}

install_apk
sleep 2
launch_test_app
sleep 8
click_bottom_navigation
echo -e "${BOLD_GREEN}Automation Sequence Complete.${RESET}"