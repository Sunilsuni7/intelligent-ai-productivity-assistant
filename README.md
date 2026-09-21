# Intelligent AI Personal Computer Assistant

## Project Overview
The Intelligent AI Personal Computer Assistant is a locally hosted, voice-and-text-activated productivity agent that securely orchestrates PC commands, system operations, and daily workflows. Powered by Google's Gemini API, the assistant translates natural language into structured execution plans to securely manage tasks, navigate the file system, retrieve system information, and control applications without requiring unrestricted shell execution.

## Problem Statement
Modern users struggle with context-switching across disjointed operating system tools, web browsers, and productivity apps. Traditional desktop assistants lack the reasoning depth to process complex workflows, while fully autonomous AI agents present severe security risks by demanding unrestricted shell or PowerShell execution capabilities. 

## Objectives
- Build a reasoning AI assistant capable of multi-step task execution.
- Maintain a strict zero-trust security perimeter around computer control.
- Ensure natural, latency-optimized interaction via voice and text.
- Provide a unified interface for scheduling, web browsing, system monitoring, and personal management.

## Key Features
- **Conversational AI**: Context-aware natural language processing with persistent memory.
- **Voice & Text Interface**: Integrated Speech-to-Text and Text-to-Speech interaction loop.
- **Controlled Windows Automation**: Safe, targeted opening of applications (e.g., VS Code, Chrome).
- **Web Browsing**: Controlled Google searches, YouTube lookups, and GitHub navigation.
- **Secure File Management**: Safe creation, opening, and searching of files/folders in approved user directories.
- **System Diagnostics**: Read-only monitoring of CPU, RAM, and disk utilization.
- **Multi-Step Execution**: Orchestration of sequential tasks (e.g., "Create a Projects folder and open Downloads") with intelligent failure-halting.
- **Task & Reminder Management**: SQLite-backed personal scheduling and memory persistence.
- **Session Isolation**: Independent conversation threads preventing context bleed.

## System Architecture
The application splits into a high-performance backend and an accessible frontend:
- **Frontend**: Streamlit-based UI for seamless chat and voice interaction.
- **Backend**: FastAPI providing robust endpoints for message processing.
- **Data Layer**: SQLite database managing chat history, tasks, reminders, and persistent memory.

## Agent Architecture
```
User Input (Voice/Text)
       ↓
Speech-to-Text Processing
       ↓
AI Assistant (Gemini)
       ↓
Structured Execution Plan (JSON)
       ↓
Tool Registry Validation
       ↓
Sequential Execution Engine (Halts on failure)
       ↓
Registered Tools (Filesystem, Browser, System Info)
       ↓
Deterministic Execution Result
       ↓
Assistant Response (Text / TTS)
```

## Tool Registry Architecture
To execute operations safely, the assistant does NOT generate arbitrary code. Instead, it selects from pre-registered, strongly-typed Python functions in the `ToolRegistry`. Each tool specifies its required `input_schema` and `RiskLevel`.

## Security Model
The system operates on a principle of least privilege.
- **No Arbitrary Shell**: The AI cannot generate or execute raw cmd.exe, PowerShell, or bash scripts.
- **Strict Validation**: All JSON arguments requested by the AI are validated against JSONSchema before execution.
- **Path Traversal Prevention**: File operations dynamically resolve absolute paths and explicitly verify they fall within approved base directories (e.g., `Desktop`, `Downloads`).
- **Confirmation Gates**: DESTRUCTIVE or EXTERNAL risk-level tools automatically halt execution to explicitly request user confirmation.

## Technology Stack
- **Language**: Python 3.13
- **AI/LLM**: Google Gemini API (`google-genai`)
- **Backend**: FastAPI, Uvicorn
- **Frontend**: Streamlit
- **Database**: SQLite, SQLAlchemy
- **Voice**: SpeechRecognition, PyAudio, pyttsx3
- **System**: psutil, platform
- **Testing**: pytest

## Project Structure
- `app/api/`: FastAPI routes and endpoints.
- `app/ai/`: Core Gemini integration and fallback logic.
- `app/agent/`: Agent loops, models, execution engine, and tool registry.
- `app/database/`: SQLite connections and SQLAlchemy models.
- `app/memory/`, `app/tasks/`, `app/reminders/`: Core productivity modules.
- `app/web_tools/`: Registered browser and application tools.
- `tests/`: Comprehensive unit and integration test suite.
- `streamlit_app.py`: Frontend entrypoint.
- `requirements.txt`: Project dependencies.

## Installation / Setup
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Configure `.env` file.

## Environment Variables
Create a `.env` file in the root directory:
```
GEMINI_API_KEY=your_secure_api_key_here
```
*(Never commit this file to version control)*

## Run Instructions
**Start the Backend:**
```bash
python -m uvicorn app.api.routes:app --port 8000
```
**Start the Frontend:**
```bash
streamlit run streamlit_app.py
```

## Example Commands
- **"What is Python?"** - *Conversational bypass; returns standard AI explanation.*
- **"Open Calculator."** - *Triggers registered application tool.*
- **"Open YouTube."** - *Triggers registered browser tool.*
- **"Search YouTube for Python DSA."** - *Executes direct targeted search query.*
- **"Create a folder called Projects."** - *Safely provisions a directory in an approved location.*
- **"Find resume.pdf."** - *Executes a controlled filesystem search.*
- **"What is my CPU usage?"** - *Reads native system diagnostics safely.*
- **"Create a Projects folder and open Downloads."** - *Executes sequentially; stops if step 1 fails.*

## Testing
Run the full regression suite:
```bash
python -m pytest tests/
```

## Known Limitations
- Dependent on Gemini API quota limits; free-tier users may experience `429 RESOURCE_EXHAUSTED` errors during high-frequency requests.
- Multi-step execution is strictly linear. If step 1 fails, the agent does not currently attempt dynamic alternate-tool branching.
- Supported filesystem operations are restricted to approved user directories only.
- System diagnostics are strictly read-only.

## Future Scope
*FUTURE ONLY:*
- Integration of a local/self-hosted LLM fallback.
- Advanced Model-provider abstraction layer.
- Dynamic multi-step branching logic.
- Multilingual voice support and wake-word activation.
- Mobile companion application integration.
