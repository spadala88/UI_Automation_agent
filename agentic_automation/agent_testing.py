import time
import subprocess
import pyautogui
import easyocr
import ollama
import os
import sys

# ==========================================
# 1. DEFINE AGENT TOOLS
# ==========================================

def install_apk_from_parent() -> str:
    """Finds the first .apk file in the parent directory and installs it via ADB."""
    print(" AGENT ACTION: Locating and installing APK...")
    try:
        # Cross-platform way to find APK in parent dir
        parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
        apks = [f for f in os.listdir(parent_dir) if f.endswith('.apk')]
        
        if not apks:
            return "Error: No APK found in the parent directory."
        
        apk_path = os.path.join(parent_dir, apks[0])
        result = subprocess.run(["adb", "install", "-r", apk_path], capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Successfully installed {apks[0]}."
        return f"Installation failed: {result.stderr}"
    except Exception as e:
        return f"Error during installation: {e}"

def click_ui_text(target_text: str) -> str:
    """Takes a screenshot, uses EasyOCR to find specified text, and clicks it."""
    print(f" AGENT ACTION: Searching for text '{target_text}' to click...")
    # Buffer to ensure UI is ready
    time.sleep(2)
    
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    screenshot_path = "agent_snap.png"
    pyautogui.screenshot(screenshot_path)
    
    results = reader.readtext(screenshot_path)
    for (bbox, text, prob) in results:
        if target_text.lower() in text.lower():
            # Calculate coordinates (Assumes 1:1 scaling for Windows/Linux)
            raw_x = int((bbox[0][0] + bbox[2][0]) / 2)
            raw_y = int((bbox[0][1] + bbox[2][1]) / 2)
            
            pyautogui.moveTo(raw_x, raw_y, duration=0.5)
            pyautogui.click()
            
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            return f"Successfully clicked '{target_text}'."
            
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)
    return f"Failed to find text '{target_text}' on screen."

def wait_for_ui(seconds: int) -> str:
    """Pause execution to allow for app loading or transitions."""
    print(f" AGENT ACTION: Waiting for {seconds}s...")
    time.sleep(seconds)
    return f"Wait complete."

# ==========================================
# 2. AGENT CONFIGURATION & LOOP
# ==========================================

tools = [
    install_apk_from_parent,
    click_ui_text,
    wait_for_ui
]

def run_agentic_flow():
    system_prompt = """
    You are an AI QA Engineer. You must execute these steps in order:
    1. Install the APK from the parent folder.
    2. Wait 5 seconds for the system to settle.
    3. Find and click 'TestApp' on the home screen to launch it.
    4. Once the app is open, click the bottom navigation items in this order: 'Home', then 'Favorites', then 'Profile'.
    
    If you cannot find a text element, wait 3 seconds and try once more.
    """

    messages = [{'role': 'user', 'content': system_prompt}]

    print("🚀 Starting Agentic Flow (Using Llama 3.1 via Ollama)...\n")

    while True:
        response = ollama.chat(
            model='llama3.1', 
            messages=messages,
            tools=tools
        )

        messages.append(response['message'])

        # End loop if agent is done
        if not response['message'].get('tool_calls'):
            print("\n✅ Agent has finished the workflow.")
            print("Summary:", response['message']['content'])
            break

        # Process tool calls
        for tool_call in response['message']['tool_calls']:
            tool_name = tool_call['function']['name']
            arguments = tool_call['function']['arguments']
            
            available_functions = {func.__name__: func for func in tools}
            func_to_call = available_functions.get(tool_name)
            
            if func_to_call:
                result_content = func_to_call(**arguments)
                messages.append({
                    'role': 'tool',
                    'content': str(result_content),
                    'name': tool_name
                })
            else:
                messages.append({
                    'role': 'tool',
                    'content': f"Error: Tool {tool_name} not found.",
                    'name': tool_name
                })

if __name__ == "__main__":
    # Ensure dependencies are installed
    # Run: pip install pyautogui easyocr ollama opencv-python
    run_agentic_flow()