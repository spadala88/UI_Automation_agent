import time
import subprocess
import pyautogui
import easyocr
import os
import sys
import traceback
from PIL import Image
from llm_ollama import call_llm
from langchain_core.messages import HumanMessage, ToolMessage

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
    # 1. Define the objective
    objective = """
    Execute these steps:
    1. Install the APK from the parent folder.
    2. Wait 3 seconds.
    3. Start the activity 'com.example.navuiact/com.example.navuiact.MainActivity' via ADB.
    4. Wait 5 seconds.
    5. Click 'Favorites'.
    """

    print("🚀 Starting Agentic Loop...\n")

    # 2. Maintain message history
    messages = [HumanMessage(content=objective)]

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
    