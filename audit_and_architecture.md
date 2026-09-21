# Intelligent AI Personal Computer Assistant - Audit and Architecture Design

## Phase 1: Existing Project Audit

### 1. Current Architecture
- **Frontend**: Streamlit application running on port 8501 (`streamlit_app.py`).
- **Backend**: FastAPI server running on port 8000 (`app/api/routes.py`, `app/main.py`).
- **Communication**: The frontend communicates with the backend via HTTP REST calls (`POST /chat`).
- **Execution Model**: The backend uses an autonomous Agent that parses natural language into JSON plans and executes registered tools sequentially.

### 2. Current UI
- A multi-page Streamlit application with a sidebar navigation system.
- Separated tabs for "AI Assistant" (Text chat), "Voice Assistant", "My Tasks", "Reminders", "Documents", "Planning", and "Analytics".
- The UI treats voice and text as separate workflows instead of a unified assistant experience.

### 3. Current Gemini Integration
- Handled in `app/ai/assistant.py` and `app/agent/agent.py`.
- The Agent passes a system prompt containing memory context and a JSON schema of registered tools to the Gemini API.
- Gemini returns a list of "plans" (tool intents and arguments) and a natural language response.
- Includes a fallback mechanism if the Gemini API is rate-limited or fails.

### 4. Current Voice System
- Located in `app/voice/speech_to_text.py` and `app/voice/text_to_speech.py`.
- Uses `SpeechRecognition` for listening and `pyttsx3` for TTS playback.
- Currently siloed in the "Voice Assistant" Streamlit page. The user must manually click "Start Listening". The voice pipeline sends transcripts to the same `/chat` endpoint but is not integrated with the main text-based chat history.

### 5. Current Agent System
- Located in `app/agent/agent.py`.
- Sequential planner: parses Gemini's JSON output, loops through up to 5 tool plans, executes them, and aggregates the results.
- Incorporates a confirmation loop for sensitive actions ("PENDING_CONFIRMATION").

### 6. Current Tool Registry
- Located in `app/agent/tool_registry.py` and `app/agent/tools.py`.
- Uses a decorator `@register_tool` to define tools, their JSON schema for the LLM, and their `RiskLevel`.

### 7. Current Computer/Web Tools
- Extremely limited. Located in `app/web_tools/`.
- Contains `validate_url`, `search_web`, `open_website`, and `search_media`.
- Relies solely on Python's built-in `webbrowser` to open URLs.
- **Missing**: No real computer control. Cannot close apps, open local apps, control volume, or play/pause media.

### 8. Current Memory
- Persistent string-based memory stored in SQLite (`memories` table) via `app/memory/memory_manager.py`.
- Injected into the Gemini system prompt during every chat request.

### 9. Current Tasks/Reminders
- Fully functional SQLite-backed task and reminder tracking (`app/tasks/`, `app/reminders/`).
- Includes an `APScheduler` background job that tracks the `Asia/Kolkata` timezone to trigger reminders.

### 10. Current Planning
- Advanced proactive planning system (`app/planning/`).
- Supports mapping Goals to Project Plans, Milestones, and Tasks with dependency tracking and progress calculation.

### 11. Current Analytics
- Analyzes SQLite data to generate productivity metrics, trends, and weekly reports (`app/analytics/`).

### 12. Current Security
- Implemented in `app/agent/safety.py`.
- Groups tools into `RiskLevel` (READ, WRITE, EXTERNAL, DESTRUCTIVE).
- Enforces an intercept layer requiring manual chat confirmation ("yes"/"no") before executing DESTRUCTIVE or EXTERNAL tools.

### 13. Current Database
- SQLite database (`productivity.db`) configured in `app/database/database.py`.
- Stores tasks, reminders, memories, tool activity, goals, and project plans.
- Currently single-tenant; does not natively distinguish between multiple users' data.

### 14. Current Tests
- Pytest suite located in `tests/` covering agent, analytics, api, managers, memory, planning, rag, security, voice, and web_tools.

### 15. Company-Specific Code
- None strictly identified. The application is a generic personal productivity assistant.

### 16. Document/RAG Code
- Located in `app/documents/`.
- Ingests PDFs and DOCX files into a local vector space.
- Supports hybrid semantic search, accessible to the user via the "Documents" UI tab and to the Agent via the `search_documents` tool.

### 17. Broken Code
- No hard crashes, but architectural disconnects: The Streamlit text chat and voice chat have separate state management, violating the unified intelligence requirement.

### 18. Duplicate Code
- Minimal duplication. Some UI rendering logic in Streamlit could be abstracted, but backend code is highly modularized.

---

## Phase 2: Proposed Architecture Design

To transform this into the **INTELLIGENT AI PERSONAL COMPUTER ASSISTANT**, the following architectural changes are proposed.

### 1. Unified Interface (One Unique Website / Workspace)
- **Consolidation**: Merge the "AI Assistant" and "Voice Assistant" pages into a single, central Chat Workspace.
- **Omnichannel Intelligence**: The interface will feature a text input box and a persistent microphone button. Both inputs will route through the exact same state, history, and API pipeline. 
- **Voice Pipeline**: 
  - Microphone -> `speech_to_text.py` -> Streamlit Chat State -> `POST /chat` -> Gemini Agent -> Safe Tool Execution -> Response -> Streamlit Chat State -> `text_to_speech.py` -> Speaker.

### 2. Multi-Person Session Architecture
- **Session Context**: Redesign the backend state to be heavily dependent on `session_id`.
- **Database Schema Updates**: 
  - Update all critical SQLite tables (`memories`, `tasks`, `reminders`, `goals`, `tool_activity`) to include a `session_id` or `user_id` column.
- **Frontend Implementation**: 
  - Implement a simple login/session-selection overlay in Streamlit, or auto-generate distinct UUIDs per browser tab/user, ensuring one person's conversation and tool history does not bleed into another's.

### 3. Safe PC Computer Control (Python Tooling)
- We will expand the Tool Registry with new controlled modules (e.g., `app/computer_tools/`) using safe Python libraries instead of arbitrary shell execution (`subprocess` with shell=True is forbidden).
- **Application Control**:
  - `open_application(app_name)`: Use a predefined safe registry of executable paths or use `os.startfile()` / `subprocess.Popen` without shell execution.
  - `close_application(app_name)`: Use `psutil` to iterate processes and safely call `.terminate()` on verified application names.
- **Web Browser Control**:
  - `open_website(url)`: Continue using `webbrowser` or integrate `pygetwindow`/`pyautogui` for more advanced control.
  - `close_browser()`: Use `psutil` to close Chrome/Edge processes safely.
- **Media & Volume Control**:
  - `control_media(action)`: Use `pyautogui` or `pynput` to simulate hardware media keys (Play/Pause, Next Track).
  - `control_volume(level)`: Use the `pycaw` library (Python Core Audio Windows) to programmatically adjust the system master volume.
- **File System Control**:
  - `open_file(path)`: Use `os.startfile()` to safely open files.
  - `search_local_files(query)`: Use Python's `os.walk` or `glob` restricted strictly to user-safe directories (e.g., Documents, Downloads) to prevent system directory traversal.

### 4. Agent & Security Pipeline Updates
- **Tool Mapping**: The Gemini agent will be updated with the expanded computer tool schemas.
- **Security Policy**: Update `app/agent/safety.py` to classify app termination and file opening. For example, closing an application should perhaps require confirmation (`RiskLevel.DESTRUCTIVE`), or we can allow it to be seamless (`RiskLevel.WRITE`) based on user preference, ensuring the assistant actually acts rather than just conversing.

**Awaiting your approval to proceed to the implementation phase.**
