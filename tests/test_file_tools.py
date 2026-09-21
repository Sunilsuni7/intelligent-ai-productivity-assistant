import os
import pytest
from pathlib import Path
from unittest.mock import patch

from app.agent.file_tools import (
    handle_create_folder,
    handle_create_text_file,
    handle_open_downloads,
    handle_find_file,
    resolve_safe_path
)

@pytest.fixture
def mock_safe_dirs(tmp_path):
    desktop = tmp_path / "Desktop"
    documents = tmp_path / "Documents"
    downloads = tmp_path / "Downloads"
    
    desktop.mkdir()
    documents.mkdir()
    downloads.mkdir()
    
    safe_dirs = {
        "desktop": desktop,
        "documents": documents,
        "downloads": downloads
    }
    
    with patch("app.agent.file_tools.get_safe_base_dirs", return_value=safe_dirs):
        yield safe_dirs

def test_resolve_safe_path_valid(mock_safe_dirs):
    path = resolve_safe_path("desktop", "projects")
    assert str(path) == str(mock_safe_dirs["desktop"] / "projects")

def test_resolve_safe_path_traversal_rejection(mock_safe_dirs):
    with pytest.raises(ValueError, match="Path traversal is not allowed"):
        resolve_safe_path("desktop", "../Windows")
        
    with pytest.raises(ValueError, match="Path traversal is not allowed"):
        resolve_safe_path("desktop", "..\\Windows")

def test_resolve_safe_path_absolute_rejection(mock_safe_dirs):
    with pytest.raises(ValueError, match="Absolute paths are not allowed"):
        resolve_safe_path("desktop", "C:\\Windows")

def test_resolve_safe_path_protected_dir(mock_safe_dirs):
    with pytest.raises(ValueError, match="is not an approved safe directory"):
        resolve_safe_path("system32", "file.txt")

def test_create_folder(mock_safe_dirs):
    res = handle_create_folder("Projects", "desktop")
    assert "✓ Created the Projects folder" in res
    assert (mock_safe_dirs["desktop"] / "Projects").exists()

def test_create_folder_duplicate(mock_safe_dirs):
    (mock_safe_dirs["desktop"] / "Projects").mkdir()
    res = handle_create_folder("Projects", "desktop")
    assert "already exists" in res

def test_create_text_file(mock_safe_dirs):
    res = handle_create_text_file("notes.txt", "documents", "hello world")
    assert "✓ Created the notes.txt file" in res
    assert (mock_safe_dirs["documents"] / "notes.txt").exists()
    assert (mock_safe_dirs["documents"] / "notes.txt").read_text() == "hello world"

def test_create_text_file_duplicate(mock_safe_dirs):
    (mock_safe_dirs["documents"] / "notes.txt").write_text("old")
    res = handle_create_text_file("notes.txt", "documents", "new")
    assert "already exists" in res
    assert (mock_safe_dirs["documents"] / "notes.txt").read_text() == "old"

def test_open_downloads(mock_safe_dirs):
    with patch("os.startfile") as mock_startfile:
        res = handle_open_downloads()
        assert "✓ Opened your Downloads folder" in res
        mock_startfile.assert_called_once_with(str(mock_safe_dirs["downloads"]))

def test_find_file_single(mock_safe_dirs):
    (mock_safe_dirs["documents"] / "resume.pdf").write_text("data")
    res = handle_find_file("resume.pdf")
    assert "Found 1 matching file:" in res
    assert "resume.pdf" in res

def test_find_file_multiple(mock_safe_dirs):
    (mock_safe_dirs["documents"] / "resume.pdf").write_text("data")
    (mock_safe_dirs["desktop"] / "resume.pdf").write_text("data2")
    res = handle_find_file("resume.pdf")
    assert "Found 2 matching files:" in res

def test_find_file_none(mock_safe_dirs):
    res = handle_find_file("missing.txt")
    assert "I couldn't find missing.txt" in res

def test_find_file_invalid_name(mock_safe_dirs):
    res = handle_find_file("../resume.pdf")
    assert "Invalid file name format" in res
