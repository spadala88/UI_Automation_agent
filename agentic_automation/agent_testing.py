import time
import subprocess
import pyautogui
import easyocr
import os
import sys
import traceback
from PIL import Image
from llm_ollama import call_llm

# ==========================================
# 1. DEFINE AGENT TOOLS
# ==========================================

def install_apk_from_parent() -> str:
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
    print(f" AGENT ACTION: Searching for text '{target_text}'...")
    time.sleep(2) 
    
    screenshot_path = "agent_debug_snap.png"
    pyautogui.screenshot(screenshot_path)
    
    with Image.open(screenshot_path) as img:
        if img.convert("L").getextrema() == (0, 0):
            return "Error: Black screen detected. Disable hardware acceleration in your emulator."

    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = reader.readtext(screenshot_path)
    
    for (bbox, text, prob) in results:
        if target_text.lower() in text.lower():
            center_x = int((bbox[0][0] + bbox[2][0]) / 2)
            center_y = int((bbox[0][1] + bbox[2][1]) / 2)
            pyautogui.moveTo(center_x, center_y, duration=0.5)
            pyautogui.click()
            return f"Successfully clicked '{target_text}'."
            
    return f"Failed to find text '{target_text}' on screen."

def wait_for_ui(seconds: int) -> str:
    """Pause execution to allow for app loading."""
    print(f" AGENT ACTION: Waiting for {seconds}s...")
    time.sleep(seconds)
    return "Wait complete."

# ==========================================
# 2. AGENT CONFIGURATION & LOOP
# ==========================================

# Map functions to a format LangChain understands
available_tools = [install_apk_from_parent, start_test_activity, click_ui_text, wait_for_ui]

def run_agentic_flow():
    # Note: For LangChain ChatOllama, the input usually needs to be a string 
    # or a list of BaseMessages. We will use a string for the initial call.
    prompt = """
    Execute these steps:
    1. Install the APK from the parent folder.
    2. Wait 3 seconds.
    3. Start the activity 'com.example.navuiact/com.example.navuiact.MainActivity' via ADB.
    4. Wait 5 seconds.
    5. Click 'Home', then 'Favorites', then 'Profile'.
    """

    print("🚀 Starting Agentic Flow (LangChain/Ollama Mode)...\n")

    try:
        # LangChain's invoke returns an AIMessage object
        response = call_llm(prompt, tools=available_tools)
        
        # In LangChain, tool calls are stored in .tool_calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                func_name = tool_call['name']
                args = tool_call['args']
                
                print(f"🔧 Agent calling tool: {func_name}")
                
                func_map = {f.__name__: f for f in available_tools}
                if func_name in func_map:
                    result = func_map[func_name](**args)
                    print(f"📊 Result: {result}")
                
            # After tool execution, the agent usually needs to be called again 
            # with the tool output to finalize. For this simple flow, 
            # we execute the sequence provided by the model.
        else:
            print("🤖 Agent Response:", response.content)

    except Exception as e:
        print(f"❌ Critical Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_agentic_flow()
    input("\nExecution finished. Press Enter to close...")