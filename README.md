# UI Automation Agent

This project provides tools for automated UI testing of Android applications using computer vision (OCR) and AI agents. It includes both a static script-based approach and an agentic approach using Large Language Models.

## Project Structure

- `requirements.txt`: List of Python dependencies.
- `static_automation/testing.sh`: A Bash script that automates the installation, launching, and navigation of an Android app using ADB and EasyOCR.
- `agentic_automation/agent_testing.py`: An AI-powered QA engineer script that uses Ollama (Llama 3.1) to intelligently interact with the UI based on text recognition.

## Prerequisites

1.  **ADB (Android Debug Bridge)**: Must be installed and available in your PATH.
2.  **Python 3.x**: Required for OCR and agent logic.
3.  **Ollama**: Required for the agentic flow (specifically `llama3.1` model).
4.  **Tesseract/EasyOCR Dependencies**: Ensure your system supports the required libraries for image processing.

## Installation

Install the required Python packages:

```bash
pip install -r requirements.txt
pip install ollama
```

*Note: `ollama` is used in the agentic automation.*

## Usage

### 1. Static Automation

The `testing.sh` script provides a fixed sequence of actions:
- Installs the first APK found in the parent directory.
- Launches the "NavUiAct" application.
- Navigates through "Home", "Favorites", and "Profile" tabs.

Run it using:
```bash
./static_automation/testing.sh
```

### 2. Agentic Automation

The `agent_testing.py` script uses an AI agent to perform tasks:
- Dynamically decides which tools to call (install, click, wait).
- Uses OCR to find text elements on the screen.
- Driven by a system prompt defining the QA workflow.

Ensure Ollama is running and the model is pulled:
```bash
ollama pull llama3.1
```

Run the agent:
```bash
python agentic_automation/agent_testing.py
```

## How it Works

- **OCR**: Uses `easyocr` to identify text locations on the screen from screenshots.
- **UI Interaction**: Uses `pyautogui` to simulate mouse movements and clicks on the identified coordinates.
- **Agent Logic**: Uses `ollama` with tool-calling capabilities to allow the LLM to execute Python functions based on the current state of the UI.
