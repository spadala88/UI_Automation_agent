import time
import subprocess
import easyocr
import os
import sys
import traceback
import inspect
import base64
from PIL import Image
from llm_ollama import call_llm
from langchain_core.messages import HumanMessage, ToolMessage

# Add Android SDK platform-tools to PATH
sdk_platform_tools = "/home/carlos/Android/Sdk/platform-tools"
if sdk_platform_tools not in os.environ["PATH"]:
    os.environ["PATH"] = os.environ["PATH"] + os.pathsep + sdk_platform_tools

try:
    import pyautogui
    pyautogui_import_error = None
except Exception as e:
    pyautogui = None
    pyautogui_import_error = e



# ==========================================
# 1. DEFINE AGENT TOOLS
# ==========================================

# The title of the window to constrain automation to. Set to None for full screen.
TARGET_WINDOW_TITLE = "Android Emulator - Medium_phone:5554"

# The resolution the agent inherently uses for coordinates. Set to None if no scaling is needed.
AGENT_BASE_RESOLUTION = (1000, 1000)

def get_target_window_region():
    if not TARGET_WINDOW_TITLE:
        return None
    try:
        if pyautogui is None:
            return None
        windows = pyautogui.getWindowsWithTitle(TARGET_WINDOW_TITLE)
        if windows:
            win = windows[0]
            return win.left, win.top, win.width, win.height
    except Exception:
        pass
    return None

def host_size():
    """Returns the screen resolution (width, height) of the host machine."""
    try:
        if pyautogui is None:
            raise RuntimeError("PyAutoGUI is not initialized")
        return pyautogui.size()
    except Exception:
        try:
            import pyscreenshot
        # Use ADB to get screen dimensions
        result = subprocess.run(["adb", "shell", "wm", "size"], capture_output=True, text=True)
        if result.returncode == 0:
            res_str = result.stdout.strip().split()[-1]
            w, h = map(int, res_str.split('x'))
            return (w, h)
    except Exception:
        pass
    return (1000, 1000)


def host_screenshot(screenshot_path: str, region=None, ignore_left_edge: bool = False) -> int:
    """Captures a screenshot of the host screen using pyscreenshot.
    Returns the X offset cropped from the left edge (if any).
    """
    crop_x = 0
    try:
        import pyscreenshot
        print(f" -> Using pyscreenshot for capture.")
        if region:
            x, y, w, h = region
            bbox = (x, y, x + w, y + h)
            img = pyscreenshot.grab(bbox=bbox)
        else:
            img = pyscreenshot.grab()
            if ignore_left_edge:
                w, h = img.size
                crop_x = int(w * 0.10)
                img = img.crop((crop_x, 0, w, h))
        img.save(screenshot_path)
    except Exception as e:
        print(f" -> pyscreenshot failed: {e}")
    return crop_x

def host_click(x: int, y: int):
    """Simulates a mouse click on the host machine."""
    import sys
    if sys.platform.startswith("linux"):
        ydotool_x = int(x * 0.75)
        ydotool_y = int(y * 0.75)
        print(f" -> Using ydotool for Linux click mapped to ydotoold ({ydotool_x}, {ydotool_y})")
        
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

def host_swipe(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5):
    """Simulates a drag/swipe gesture on the host machine."""
    import sys
    if sys.platform.startswith("linux"):
        ydotool_start_x = int(start_x * 0.75)
        ydotool_start_y = int(start_y * 0.75)
        ydotool_end_x = int(end_x * 0.75)
        ydotool_end_y = int(end_y * 0.75)
        
        print(f" -> Using ydotool for Linux swipe from ({ydotool_start_x}, {ydotool_start_y}) to ({ydotool_end_x}, {ydotool_end_y}) over {duration}s")
        
        subprocess.run(["ydotool", "mousemove", "-a", "-x", str(ydotool_start_x), "-y", str(ydotool_start_y)], check=False)
        time.sleep(0.1)
        subprocess.run(["ydotool", "key", "272:1"], check=False)
        time.sleep(0.1)
        
        steps = 20
        sleep_time = duration / steps
        for i in range(1, steps + 1):
            cur_x = ydotool_start_x + (ydotool_end_x - ydotool_start_x) * (i / steps)
            cur_y = ydotool_start_y + (ydotool_end_y - ydotool_start_y) * (i / steps)
            subprocess.run(["ydotool", "mousemove", "-a", "-x", str(int(cur_x)), "-y", str(int(cur_y))], check=False)
            time.sleep(sleep_time)
            
        time.sleep(0.1)
        subprocess.run(["ydotool", "key", "272:0"], check=False)
    else:
        import pyautogui
        print(f" -> Using PyAutoGUI for {sys.platform} swipe from ({start_x}, {start_y}) to ({end_x}, {end_y}) over {duration}s")
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=duration, button='left')

def get_target_window_region() -> Optional[Tuple[int, int, int, int]]:
    """Returns None as we don't have a reliable way to get the window rect on Wayland."""
    return None
    """Finds the first .apk file in the parent directory and installs it via ADB."""
    print(" AGENT ACTION: Locating and installing APK...")
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
        apks = [f for f in os.listdir(parent_dir) if f.endswith('.apk')]
        
        if not apks:
            return "Error: No APK found in the parent directory."
        
        apk_path = os.path.join(parent_dir, apks[0])
        result = subprocess.run(f'adb install -r "{apk_path}"', capture_output=True, text=True, shell=True)
        return f"Successfully installed {apks[0]}." if result.returncode == 0 else f"Failed: {result.stderr}"
    except Exception as e:
        return f"Error during installation: {e}"

def start_test_activity() -> str:
    """Starts the application directly using an ADB shell command."""
    print(" AGENT ACTION: Starting activity via ADB...")
    cmd = "adb shell am start -n com.example.navuiact/com.example.navuiact.MainActivity"
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return "Activity started successfully." if result.returncode == 0 else f"Failed: {result.stderr}"

def click_ui_text(target_text: str) -> str:
    """Takes a screenshot, uses EasyOCR to find specified text, and clicks it."""
    print(f" AGENT ACTION: Searching for text...")
    time.sleep(2) 
    
    screenshot_path = "agent_debug_snap.png"
    region = get_target_window_region()
    # If no specific region, ignore the left edge to avoid finding Ubuntu desktop icons
    crop_offset_x = host_screenshot(screenshot_path, region=region, ignore_left_edge=(region is None))

    with Image.open(screenshot_path) as img:
        if img.convert("L").getextrema() == (0, 0):
            return "Error: Black screen detected. Disable hardware acceleration in your emulator."

    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = reader.readtext(screenshot_path)
    
    matches = []
    for (bbox, text, prob) in results:
        # Exact match or inclusion check for the tab labels
        if target_text.lower() in text.lower():
            matches.append(bbox)
            
    if not matches:
        return f"Failed to find text '{target_text}' on screen."
        
    # The Android bottom navigation tabs will be at the bottom of the screen.
    # Sort matches by Y descending, then X descending to break ties in favor of the emulator
    matches.sort(key=lambda b: (b[0][1], b[0][0]), reverse=True)
    found_bbox = matches[0]
    
    center_x = int((found_bbox[0][0] + found_bbox[2][0]) / 2) + crop_offset_x
    center_y = int((found_bbox[0][1] + found_bbox[2][1]) / 2)
    
    if region:
        center_x += region[0]
        center_y += region[1]
        
    host_click(center_x, center_y)
    return f"Successfully clicked '{target_text}'."

def wait_for_ui(seconds: int) -> str:
    """Pause execution to allow for app loading."""
    print(f" AGENT ACTION: Waiting for {seconds}s...")
    time.sleep(seconds)
    return "Wait complete."

def swipe_screen(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> str:
    """Clicks and drags from the start coordinates to the end coordinates to simulate a swipe or scroll. Default duration is 0.5s for a moderate scroll. Decrease to 0.1 for a fast flick, or increase to 1.0+ for a slow drag."""
    print(f" AGENT ACTION: Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y})...")
    region = get_target_window_region()
    if region:
        # Dynamically adjust orientation of base resolution to match the window
        if AGENT_BASE_RESOLUTION:
            base_x, base_y = AGENT_BASE_RESOLUTION
            if (region[2] > region[3]) != (base_x > base_y):
                base_x, base_y = base_y, base_x

            # Scale the coordinates based on the agent's base resolution
            start_x = int((start_x / base_x) * region[2])
            start_y = int((start_y / base_y) * region[3])
            end_x = int((end_x / base_x) * region[2])
            end_y = int((end_y / base_y) * region[3])
            
        # Clamp to region bounds, with 15px padding to avoid window resize handles
        start_x = max(15, min(start_x, region[2] - 15))
        start_y = max(15, min(start_y, region[3] - 15))
        end_x = max(15, min(end_x, region[2] - 15))
        end_y = max(15, min(end_y, region[3] - 15))
        
        start_x += region[0]
        start_y += region[1]
        end_x += region[0]
        end_y += region[1]
        
    screen_w, screen_h = host_size()
    start_x = max(10, min(start_x, screen_w - 10))
    start_y = max(10, min(start_y, screen_h - 10))
    end_x = max(10, min(end_x, screen_w - 10))
    end_y = max(10, min(end_y, screen_h - 10))
    
    host_swipe(start_x, start_y, end_x, end_y, duration=duration)
    return f"Successfully swiped from ({start_x}, {start_y}) to ({end_x}, {end_y}) with duration {duration}s."

def click_icon_by_coordinate(x: int, y: int, template_name: str) -> str:
    """Clicks the specified x,y coordinate, and saves a cropped image around it for future OpenCV matching. Use only if click_ui_text (easyocr) cannot find the target."""
    print(f" AGENT ACTION: Clicking coordinate ({x}, {y}) and saving template '{template_name}'...")
    
    # Save crop
    screenshot_path = "agent_debug_snap.png"
    region = get_target_window_region()
    if region:
        host_screenshot(screenshot_path, region=region)
        
        # Dynamically adjust orientation of base resolution to match the window
        if AGENT_BASE_RESOLUTION:
            base_x, base_y = AGENT_BASE_RESOLUTION
            if (region[2] > region[3]) != (base_x > base_y):
                base_x, base_y = base_y, base_x
                
            x = int((x / base_x) * region[2])
            y = int((y / base_y) * region[3])
        x = max(15, min(x, region[2] - 15))
        y = max(15, min(y, region[3] - 15))
    else:
        host_screenshot(screenshot_path)
        screen_w, screen_h = host_size()
        x = max(15, min(x, screen_w - 15))
        y = max(15, min(y, screen_h - 15))
        
    with Image.open(screenshot_path) as img:
        box = (max(0, x-30), max(0, y-30), min(img.width, x+30), min(img.height, y+30))
        crop = img.crop(box)
        crop.save(f"template_{template_name}.png")
    
    # Click
    click_x = x + region[0] if region else x
    click_y = y + region[1] if region else y
    
    screen_w, screen_h = host_size()
    click_x = max(10, min(click_x, screen_w - 10))
    click_y = max(10, min(click_y, screen_h - 10))
    
    host_click(click_x, click_y)
    return f"Successfully clicked ({x}, {y}) and saved template."

def click_by_template(template_path: str) -> str:
    """Uses OpenCV to find and click an image template on the screen. (Used by standalone script)"""
    print(f" AGENT ACTION: Searching for image template '{template_path}'...")
    time.sleep(2)
    import cv2
    import numpy as np
    
    screenshot_path = "agent_debug_snap.png"
    region = get_target_window_region()
    host_screenshot(screenshot_path, region=region)
    
    # Load screenshot and template
    img_rgb = cv2.imread(screenshot_path)
    template = cv2.imread(template_path)
    if img_rgb is None:
        return f"Failed to read screenshot {screenshot_path}"
    if template is None:
        return f"Failed to read template {template_path}"
        
    h, w = template.shape[:2]
    res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    # Set threshold (0.8 confidence equivalent)
    threshold = 0.8
    if max_val >= threshold:
        # Center of matched area
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        
        if region:
            center_x += region[0]
            center_y += region[1]
            
        screen_w, screen_h = host_size()
        click_x = max(10, min(center_x, screen_w - 10))
        click_y = max(10, min(center_y, screen_h - 10))
        
        host_click(click_x, click_y)
        return f"Successfully clicked template '{template_path}'."
    return f"Failed to find template '{template_path}' on screen."

def generate_standalone_script(filename: str = "standalone_automation.py") -> str:
    """Generates a standalone python script that replicates the successful steps taken so far."""
    print(f"\n📝 Generating standalone script: {filename}")
    steps = _executed_steps
    if not steps:
        return "Error: No successful steps to generate a script from."
        
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("import time\nimport subprocess\nimport pyautogui\nimport easyocr\nimport os\nimport shutil\nfrom PIL import Image\n\n")
            f.write(f"TARGET_WINDOW_TITLE = {repr(TARGET_WINDOW_TITLE)}\n")
            f.write(f"AGENT_BASE_RESOLUTION = {repr(AGENT_BASE_RESOLUTION)}\n\n")
            f.write(inspect.getsource(get_target_window_region) + "\n\n")
            
            # Write host helpers so they are available in standalone
            f.write(inspect.getsource(host_size) + "\n\n")
            f.write(inspect.getsource(host_screenshot) + "\n\n")
            f.write(inspect.getsource(host_click) + "\n\n")
            f.write(inspect.getsource(host_swipe) + "\n\n")
            
            # Add the tool definitions (so it is truly standalone)
            used_funcs = []
            for step in steps:
                if step['func_name'] not in used_funcs and step['func_name'] != 'generate_standalone_script':
                    used_funcs.append(step['func_name'])
                    
            standalone_tools = available_tools + [click_by_template]
            func_map = {func.__name__: func for func in standalone_tools}
            
            for func_name in used_funcs:
                if func_name in func_map:
                    source = inspect.getsource(func_map[func_name])
                    f.write(source + "\n\n")
                    
            f.write("if __name__ == '__main__':\n")
            f.write("    print('🚀 Starting standalone automation...')\n")
            for step in steps:
                func_name = step['func_name']
                if func_name == 'generate_standalone_script':
                    continue
                args = step['args']
                args_str = ", ".join([f"{k}={repr(v)}" for k, v in args.items()])
                f.write(f"    print(\"Executing: {func_name}({args_str})\")\n")
                f.write(f"    {func_name}({args_str})\n")
            f.write("    print('✅ Automation finished.')\n")
        return f"Successfully generated standalone script at {filename}"
    except Exception as e:
        return f"Error generating script: {str(e)}"

def validate_screen(query: str) -> str:
    """Takes a screenshot and sends it to the LLM for visual validation based on the query. Use sparingly due to cost."""
    print(" AGENT ACTION: Taking screenshot for visual validation...")
    screenshot_path = "validation_snap.png"
    region = get_target_window_region()
    host_screenshot(screenshot_path, region=region)
    return f"__IMAGE_VALIDATION_REQUESTED__:{query}"

available_tools = [install_apk_from_parent, start_test_activity, click_ui_text, wait_for_ui, generate_standalone_script, validate_screen, click_icon_by_coordinate, swipe_screen]

def run_agentic_flow():
    # 1. Define the objective
    objective = """
    Execute these steps:
    1. Make sure you are in the home screen.
    2. Open the app drawer.
    3. open settings.
    4. Scroll until you find the accessibility settings.
    5. click on "Accessibility".
    """

    print("🚀 Starting Agentic Loop...\n")

    # 2. Maintain message history
    messages = [HumanMessage(content=objective)]
    
    global _executed_steps
    _executed_steps.clear()

    while True:
        try:
            # 3. Call the LLM with current history
            response = call_llm(messages, tools=available_tools)
            
            # Add the AI's reasoning/decision to history
            messages.append(response)

            # 4. Check if the LLM wants to use tools
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    func_name = tool_call['name']
                    args = tool_call['args']
                    
                    print(f"🔧 Agent is invoking: {func_name}")
                    
                    func_map = {f.__name__: f for f in available_tools}
                    if func_name in func_map:
                        # Execute the tool
                        result = func_map[func_name](**args)
                        print(f"📊 Result: {result}")
                        
                        if isinstance(result, str) and result.startswith("__IMAGE_VALIDATION_REQUESTED__"):
                            query = result.split(":", 1)[1] if ":" in result else "Please review the screen."
                            
                            with Image.open("validation_snap.png") as img:
                                img_w, img_h = img.size
                                
                            with open("validation_snap.png", "rb") as img_file:
                                b64_img = base64.b64encode(img_file.read()).decode("utf-8")
                            
                            # 5. FEEDBACK: Tell the LLM what happened
                            messages.append(ToolMessage(
                                tool_call_id=tool_call['id'],
                                content="Screenshot taken successfully. Please see the image in the next human message."
                            ))
                            
                            # Inject image as human message
                            messages.append(HumanMessage(
                                content=[
                                    {"type": "text", "text": f"Here is the requested screenshot for validation. The image size is {img_w}x{img_h} pixels. Provide coordinates relative to this size. Query: {query}"},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                                ]
                            ))
                        else:
                            # Record successful step
                            if "Failed" not in str(result) and "Error" not in str(result):
                                if func_name == "click_icon_by_coordinate":
                                    _executed_steps.append({
                                        "func_name": "click_by_template", 
                                        "args": {"template_path": f"template_{args['template_name']}.png"}
                                    })
                                else:
                                    _executed_steps.append({"func_name": func_name, "args": args})
                            
                            # 5. FEEDBACK: Tell the LLM what happened
                            # This is the "Observation" that triggers the next step
                            messages.append(ToolMessage(
                                tool_call_id=tool_call['id'],
                                content=str(result)
                            ))
                    else:
                        print(f"❌ Tool {func_name} not found.")
                
                # Go back to the top of the loop so the LLM can process the result
                continue 
            
            else:
                # No more tool calls means the agent is finished
                print("\n✅ Final Agent Summary:", response.content)
                break

        except Exception as e:
            print(f"❌ Error in loop: {e}")
            break

if __name__ == "__main__":
    run_agentic_flow()
    input("\nExecution finished. Press Enter to close...")
    