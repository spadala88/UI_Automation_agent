#!/bin/bash

# Define the codes using ANSI-C quoting
BOLD_GREEN=$'\033[1;32m'
BOLD_BLUE=$'\033[1;34m'
BOLD_RED=$'\033[1;31m'
RESET=$'\033[0m'

# --- FUNCTION 1: Install APK from Project Parent Folder ---
install_apk() {
    local APK_PATH=$(find .. -maxdepth 1 -name "*.apk" | head -n 1)

    if [ -z "$APK_PATH" ]; then
        echo -e "${BOLD_RED}❌ Error: No APK found in the project parent folder.${RESET}"
        return 1
    fi

    echo -e "${BOLD_BLUE}Installing APK: $APK_PATH...${RESET}"
    adb install -r "$APK_PATH"
    
    if [ $? -eq 0 ]; then
        echo -e "${BOLD_GREEN}✅ Installation successful.${RESET}"
    else
        echo -e "${BOLD_RED}❌ Installation failed.${RESET}"
        return 1
    fi
}

# --- FUNCTION 2: Launch "NavUiActNavUiAct" using EasyOCR ---
launch_test_app() {
    local TARGET_APP="NavUiAct"
    echo -e "${BOLD_BLUE}Searching for '$TARGET_APP' on home screen...${RESET}"

    python3 - "$TARGET_APP" <<'EOF'
import sys
import time
import os
import tempfile
import platform
import pyautogui
import easyocr

target_text = sys.argv[1]
time.sleep(2) 

try:
    temp_dir = tempfile.gettempdir()
    screenshot_path = os.path.join(temp_dir, "launcher_ocr.png")
    
    if platform.system() == 'Darwin':
        os.system(f"screencapture -x {screenshot_path}")
    else:
        pyautogui.screenshot(screenshot_path)

    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = reader.readtext(screenshot_path)

    found_bbox = None
    for (bbox, text, prob) in results:
        if target_text.lower() in text.lower():
            found_bbox = bbox
            break

    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)

    if found_bbox is None:
        print(f"❌ FAILURE: Could not find '{target_text}' icon.")
        sys.exit(1)

    raw_x = int((found_bbox[0][0] + found_bbox[2][0]) / 2)
    raw_y = int((found_bbox[0][1] + found_bbox[2][1]) / 2)
    divisor = 2 if platform.system() == 'Darwin' else 1

    pyautogui.moveTo(raw_x / divisor, raw_y / divisor, duration=0.5)
    pyautogui.click()
    print(f"✅ Launched {target_text}")

except Exception as e:
    print(f"❌ OCR Error: {e}")
    sys.exit(1)
EOF
}

# --- FUNCTION 3: Click Bottom Navigation Items (Updated for Screenshot) ---
click_bottom_navigation() {
    # Specifically targeting the items from your screenshot
    local NAV_ITEMS=("Home" "Favorites" "Profile")
    
    for item in "${NAV_ITEMS[@]}"; do
        echo -e "${BOLD_BLUE}Navigating to Bottom Tab: $item...${RESET}"
        
        python3 - "$item" <<'EOF'
import sys
import time
import os
import tempfile
import platform
import pyautogui
import easyocr

target_text = sys.argv[1]
try:
    temp_dir = tempfile.gettempdir()
    screenshot_path = os.path.join(temp_dir, "nav_items_ocr.png")
    
    if platform.system() == 'Darwin':
        os.system(f"screencapture -x {screenshot_path}")
    else:
        pyautogui.screenshot(screenshot_path)

    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = reader.readtext(screenshot_path)

    found_bbox = None
    for (bbox, text, prob) in results:
        # Exact match or inclusion check for the tab labels
        if target_text.lower() in text.lower():
            found_bbox = bbox
            break

    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)

    if found_bbox:
        raw_x = int((found_bbox[0][0] + found_bbox[2][0]) / 2)
        raw_y = int((found_bbox[0][1] + found_bbox[2][1]) / 2)
        divisor = 2 if platform.system() == 'Darwin' else 1
        
        # Move and click the specific tab label
        pyautogui.moveTo(raw_x / divisor, raw_y / divisor, duration=0.4)
        pyautogui.click()
        print(f"✅ Clicked {target_text}")
        time.sleep(1.5) # Wait for UI to update
    else:
        print(f"⚠️ Could not find tab: {target_text}")

except Exception as e:
    print(f"❌ Error during Nav: {e}")
EOF
    done
}

# --- EXECUTION ---
install_apk
sleep 2
launch_test_app
sleep 4 # Give the app extra time to load the theme
click_bottom_navigation

echo -e "${BOLD_GREEN}Automation Sequence Complete.${RESET}"