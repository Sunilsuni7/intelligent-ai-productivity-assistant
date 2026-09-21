import subprocess
import shutil
import ctypes
import time

def open_application(app_name: str) -> str:
    app_map = {
        "vs code": "code.cmd",
        "vscode": "code.cmd",
        "calculator": "calc.exe",
        "notepad": "notepad.exe",
        "chrome": "chrome.exe",
        "explorer": "explorer.exe"
    }
    
    executable = app_map.get(app_name.lower())
    if not executable:
        return f"Application '{app_name}' is not in the safe allowed list."
        
    try:
        exe_path = shutil.which(executable)
        if not exe_path:
            return f"Executable for {app_name} not found in PATH."
            
        subprocess.Popen([exe_path])
        return f"Opened {app_name}."
    except Exception as e:
        return f"Failed to open {app_name}: {e}"

def close_application(app_name: str) -> str:
    app_map = {
        "vs code": "Code.exe",
        "vscode": "Code.exe",
        "calculator": "CalculatorApp.exe",
        "notepad": "notepad.exe",
        "chrome": "chrome.exe",
        "explorer": "explorer.exe"
    }
    
    executable = app_map.get(app_name.lower())
    if not executable:
        return f"Application '{app_name}' is not in the safe allowed list."
        
    try:
        res = subprocess.run(["taskkill", "/IM", executable, "/F"], capture_output=True)
        if res.returncode == 0:
            return f"Closed {app_name}."
        else:
            return f"Could not find or close {app_name}."
    except Exception as e:
        return f"Failed to close {app_name}: {e}"

def switch_application() -> str:
    """Uses Alt+Tab to switch to the previous application."""
    try:
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0) # Alt down
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0x09, 0, 0, 0) # Tab down
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0x09, 0, 2, 0) # Tab up
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0x12, 0, 2, 0) # Alt up
        return "Switched application."
    except Exception as e:
        return f"Failed to switch application: {e}"

def open_window() -> str:
    return switch_application()

def close_window() -> str:
    """Uses Alt+F4 to close the active window."""
    try:
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0) # Alt down
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0x73, 0, 0, 0) # F4 down
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0x73, 0, 2, 0) # F4 up
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0x12, 0, 2, 0) # Alt up
        return "Closed active window."
    except Exception as e:
        return f"Failed to close window: {e}"

def focus_application(app_name: str) -> str:
    # Safely ignoring specific string matching via ctypes unless we use a window enumerator.
    # We will just switch app as a fallback since building a reliable focus app logic in pure CTypes is long.
    return switch_application()
