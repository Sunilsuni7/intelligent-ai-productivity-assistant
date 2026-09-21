import os
from pathlib import Path
from app.agent.tool_registry import register_tool
from app.agent.safety import RiskLevel

def get_safe_base_dirs():
    user_home = Path(os.path.expanduser("~")).resolve()
    return {
        "desktop": user_home / "Desktop",
        "documents": user_home / "Documents",
        "downloads": user_home / "Downloads"
    }

def resolve_safe_path(base_name: str, sub_path: str) -> Path:
    safe_dirs = get_safe_base_dirs()
    base_name = base_name.lower()
    if base_name not in safe_dirs:
        raise ValueError(f"Base directory '{base_name}' is not an approved safe directory.")
    
    base_path = safe_dirs[base_name]
    
    # Check if sub_path is absolute or contains path traversal
    if os.path.isabs(sub_path) or ":" in sub_path:
        raise ValueError("Absolute paths are not allowed.")
    
    if ".." in sub_path or sub_path.startswith("/") or sub_path.startswith("\\"):
        raise ValueError("Path traversal is not allowed.")
        
    resolved_path = (base_path / sub_path).resolve()
    
    # Final safety check: resolved path must be under the base path
    if not str(resolved_path).startswith(str(base_path)):
        raise ValueError("Path traversal is not allowed.")
        
    return resolved_path

@register_tool(
    name="create_folder",
    description="Creates a new folder in a safe user directory (desktop, documents, downloads).",
    input_schema={
        "type": "object",
        "properties": {
            "folder_name": {"type": "string", "description": "The name of the folder or relative path"},
            "base_dir": {"type": "string", "enum": ["desktop", "documents", "downloads"], "description": "The approved base directory"}
        },
        "required": ["folder_name", "base_dir"]
    },
    risk_level=RiskLevel.WRITE,
    requires_confirmation=False
)
def handle_create_folder(folder_name: str, base_dir: str):
    try:
        target_path = resolve_safe_path(base_dir, folder_name)
        if target_path.exists():
            return f"I couldn't create the folder. A folder or file named {folder_name} already exists."
        target_path.mkdir(parents=True, exist_ok=False)
        return f"✓ Created the {folder_name} folder."
    except Exception as e:
        return "I couldn't create the folder."

@register_tool(
    name="create_text_file",
    description="Creates a new text file in a safe user directory.",
    input_schema={
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "description": "The name of the text file, e.g., notes.txt"},
            "content": {"type": "string", "description": "The content to write to the file"},
            "base_dir": {"type": "string", "enum": ["desktop", "documents", "downloads"], "description": "The approved base directory"}
        },
        "required": ["file_name", "base_dir"]
    },
    risk_level=RiskLevel.WRITE,
    requires_confirmation=False
)
def handle_create_text_file(file_name: str, base_dir: str, content: str = ""):
    try:
        target_path = resolve_safe_path(base_dir, file_name)
        
        if not target_path.suffix.lower() in [".txt", ".md", ".csv", ".json", ".log"]:
            target_path = target_path.with_suffix(".txt")
            file_name = target_path.name
            
        if target_path.exists():
            return f"A file named {file_name} already exists."
            
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✓ Created the {file_name} file."
    except Exception as e:
        return "I couldn't create the file."

@register_tool(
    name="open_downloads",
    description="Opens the user's Downloads folder.",
    input_schema={
        "type": "object",
        "properties": {}
    },
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_open_downloads():
    try:
        downloads_path = get_safe_base_dirs()["downloads"]
        if not downloads_path.exists():
            return "I couldn't open the folder. Downloads directory does not exist."
            
        if os.name == 'nt':
            os.startfile(str(downloads_path))
        else:
            import subprocess
            subprocess.run(["xdg-open", str(downloads_path)], check=True)
        return "✓ Opened your Downloads folder."
    except Exception as e:
        return "I couldn't open the Downloads folder."

@register_tool(
    name="find_file",
    description="Searches for a file by name in approved safe directories (desktop, documents, downloads).",
    input_schema={
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "description": "The exact name of the file to search for, e.g. resume.pdf"}
        },
        "required": ["file_name"]
    },
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_find_file(file_name: str):
    try:
        if ".." in file_name or "/" in file_name or "\\" in file_name:
            return "I couldn't find the file. Invalid file name format."
            
        safe_dirs = get_safe_base_dirs()
        matches = []
        target_lower = file_name.lower()
        
        for base_name, base_path in safe_dirs.items():
            if base_path.exists():
                for root, dirs, files in os.walk(str(base_path), followlinks=False):
                    for f in files:
                        if f.lower() == target_lower:
                            matches.append(os.path.join(root, f))
                            
        if not matches:
            return f"I couldn't find {file_name} in your approved folders."
            
        if len(matches) == 1:
            return f"Found 1 matching file:\n{matches[0]}"
        else:
            return f"Found {len(matches)} matching files:\n" + "\n".join(matches)
    except Exception:
        return f"I couldn't find {file_name} in the approved folders."
