# UI Automation Agent

An intelligent Android UI automation framework that combines computer vision (OCR) with AI-powered agents. This project provides both a traditional scripted approach and an advanced LLM-based agent approach for automating Android app testing and interaction.

**Key Features:**
- 🤖 AI-powered agent using Ollama with tool-calling capabilities
- 🔍 Text-based UI element detection using EasyOCR
- ⚙️ ADB integration for Android device interaction
- 🖱️ Automated UI element clicking and navigation
- 📸 Real-time screenshot analysis and OCR
- 🔄 Flexible scripted and agentic automation approaches

## Project Structure

```
UI_Automation_agent/
├── agentic_automation/          # LLM-based intelligent automation
│   ├── agent_testing.py         # Main agent with tool-calling loop
│   └── llm_ollama.py            # LLM configuration and utilities
├── static_automation/           # Traditional scripted automation
│   └── testing.sh              # Bash script for static workflows
├── app-debug.apk               # Test APK file
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Core Components

- **`agentic_automation/agent_testing.py`**: AI-powered QA agent that uses LangChain and Ollama to intelligently decide which actions to take, with tools for APK installation, activity launching, UI text clicking, and wait operations.

- **`agentic_automation/llm_ollama.py`**: LLM interface module for initializing and configuring the ChatOllama instance, binding tools, and managing connections to the Ollama server.

- **`static_automation/testing.sh`**: Bash script providing a fixed automation workflow that finds and installs APK files, launches the NavUiAct app, and navigates through Home, Favorites, and Profile tabs using EasyOCR for text detection.

## Prerequisites

1. **ADB (Android Debug Bridge)**: Must be installed and available in your system PATH
   - Required for communicating with Android devices/emulators
   
2. **Python 3.8+**: Core language for the automation scripts
   
3. **Ollama**: Required for the agentic approach
   - Download from [ollama.ai](https://ollama.ai)
   - Must be running as a background service on localhost:11434
   - Default model: `gpt-oss:120b-cloud` (configure in `llm_ollama.py`)
   
4. **Android Emulator or Device**: Connected via ADB
   - For emulator: Ensure it's running before executing automation scripts

## Installation

### 1. Clone and Set Up Virtual Environment

```bash
# Navigate to project directory
cd UI_Automation_agent

# Create virtual environment
python -m venv env

# Activate (Windows)
env\Scripts\activate

# Activate (macOS/Linux)
source env/bin/activate
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `pyautogui`: GUI automation and mouse/keyboard control
- `easyocr`: Optical character recognition for text detection
- `opencv-python`: Computer vision processing
- `Pillow`: Image processing
- `langchain`: LLM orchestration framework
- `langchain-ollama`: Ollama integration for LangChain
- `ollama`: Ollama client library

### 3. Set Up Ollama

```bash
# Download and install Ollama from ollama.ai
# Then pull the required model
ollama pull gpt-oss:120b-cloud

# Start Ollama service (runs on http://localhost:11434)
ollama serve
```

## Usage

### Approach 1: Agentic Automation (LLM-Powered)

The agentic approach uses an LLM to intelligently decide which actions to take based on the current objective.

**How it works:**
1. The agent receives an objective (e.g., "Install APK and click Favorites")
2. It uses EasyOCR to analyze the current screen state
3. It decides which tool to call next (install, click, wait, etc.)
4. It receives feedback about the action and continues until objectives are met

**Run the agent:**

```bash
# Ensure Ollama is running in another terminal
python agentic_automation/agent_testing.py
```

**Available Agent Tools:**
- `install_apk_from_parent()`: Finds and installs the first APK in the parent directory
- `start_test_activity()`: Launches the NavUiAct application via ADB
- `click_ui_text(target_text)`: Finds text on screen using OCR and clicks it
- `wait_for_ui(seconds)`: Pauses execution for app loading

**Customization:**
- Edit the `objective` variable in `run_agentic_flow()` to change the automation workflow
- Modify `DEFAULT_MODEL` in `llm_ollama.py` to use different Ollama models
- Add new tools by creating functions and adding them to `available_tools` list

### Approach 2: Static Scripted Automation

The static approach follows a fixed sequence of predefined actions without AI decision-making.

**Run the script:**

```bash
# On macOS/Linux
chmod +x static_automation/testing.sh
./static_automation/testing.sh

# On Windows (using Git Bash or WSL)
bash static_automation/testing.sh
```

**Workflow:**
1. Locates and installs APK from project parent directory
2. Launches the NavUiAct app
3. Navigates through Home, Favorites, and Profile tabs
4. Uses EasyOCR to find and click navigation items

## How It Works

### OCR-Based Text Detection
- Takes screenshots using `pyautogui` or ADB
- Uses `easyocr` to extract text and bounding boxes
- Identifies target UI elements by text matching

### UI Interaction
- Calculates center coordinates of detected text elements
- Uses `pyautogui` to move mouse and simulate clicks
- Implements natural delays for app responsiveness

### Agent Loop (Agentic Approach)
1. **Initialization**: Create message history with initial objective
2. **LLM Reasoning**: Call Ollama with bound tools to get next action
3. **Tool Execution**: Parse tool calls and execute corresponding Python functions
4. **Feedback Loop**: Return tool results as ToolMessages to LLM
5. **Termination**: Stop when LLM indicates no more tool calls needed

## Troubleshooting

| Issue | Solution |
|-------|----------|
| ADB not found | Ensure Android SDK is installed and ADB is in PATH |
| Black screen error | Disable hardware acceleration in Android emulator settings |
| OCR fails to find text | Check screenshot quality, adjust confidence thresholds in code |
| Ollama connection error | Verify Ollama is running (`ollama serve`), check localhost:11434 is accessible |
| Model not found error | Pull the model: `ollama pull gpt-oss:120b-cloud` |
| Permission denied (testing.sh) | Make file executable: `chmod +x static_automation/testing.sh` |

## Configuration

### LLM Settings (`agentic_automation/llm_ollama.py`)
```python
DEFAULT_MODEL = "gpt-oss:120b-cloud"  # Change to different model
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama server location
temperature = 0  # Set to 0 for deterministic behavior
```

### Agent Objective (`agentic_automation/agent_testing.py`)
Modify the `objective` string in `run_agentic_flow()` to define custom automation workflows.

## Future Enhancements

- [ ] Support for more LLM providers beyond Ollama
- [ ] Mobile element detection using accessibility frameworks
- [ ] Video recording and playback of automation
- [ ] Integration with CI/CD pipelines
- [ ] Web platform support beyond Android
- [ ] Performance metrics and logging
- [ ] Multi-device parallel testing

## Notes

- The project uses a local Ollama instance for agent reasoning. For cloud-based LLMs, modify `llm_ollama.py`
- EasyOCR initialization can be slow on first run; consider pre-loading the model
- For best results with OCR, ensure the Android emulator/device has good display quality
- The agent loop includes safety checks to prevent infinite loops

## License

[Add license information]
