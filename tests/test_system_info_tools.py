import pytest
from unittest.mock import patch, MagicMock
from app.agent.system_info_tools import (
    handle_get_cpu_usage,
    handle_get_memory_usage,
    handle_get_disk_usage,
    handle_get_os_information,
    handle_get_system_information
)

@patch('psutil.cpu_percent')
def test_get_cpu_usage(mock_cpu_percent):
    mock_cpu_percent.return_value = 25.5
    result = handle_get_cpu_usage()
    assert "25.5%" in result
    mock_cpu_percent.assert_called_with(interval=0.5)

@patch('psutil.virtual_memory')
def test_get_memory_usage(mock_virtual_memory):
    mock_mem = MagicMock()
    mock_mem.total = 16 * (1024 ** 3)
    mock_mem.available = 4 * (1024 ** 3)
    mock_mem.percent = 75.0
    mock_virtual_memory.return_value = mock_mem
    
    result = handle_get_memory_usage()
    assert "12.0 GB" in result
    assert "16.0 GB" in result
    assert "75.0%" in result

@patch('psutil.disk_usage')
def test_get_disk_usage(mock_disk_usage):
    mock_disk = MagicMock()
    mock_disk.total = 500 * (1024 ** 3)
    mock_disk.used = 100 * (1024 ** 3)
    mock_disk.free = 400 * (1024 ** 3)
    mock_disk.percent = 20.0
    mock_disk_usage.return_value = mock_disk
    
    result = handle_get_disk_usage()
    assert "100.0 GB used" in result
    assert "400.0 GB free" in result
    assert "500.0 GB total" in result
    assert "20.0%" in result

@patch('platform.system')
@patch('platform.release')
@patch('platform.machine')
def test_get_os_information(mock_machine, mock_release, mock_system):
    mock_system.return_value = "Windows"
    mock_release.return_value = "11"
    mock_machine.return_value = "AMD64"
    
    result = handle_get_os_information()
    assert "Windows 11" in result
    assert "AMD64" in result

@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
@patch('psutil.disk_usage')
@patch('platform.system')
@patch('platform.release')
@patch('platform.machine')
def test_get_system_information(mock_machine, mock_release, mock_system, mock_disk, mock_mem, mock_cpu):
    mock_cpu.return_value = 15.0
    
    mem = MagicMock()
    mem.total = 8 * (1024 ** 3)
    mem.available = 2 * (1024 ** 3)
    mock_mem.return_value = mem
    
    disk = MagicMock()
    disk.total = 256 * (1024 ** 3)
    disk.used = 128 * (1024 ** 3)
    disk.free = 128 * (1024 ** 3)
    mock_disk.return_value = disk
    
    mock_system.return_value = "Linux"
    mock_release.return_value = "Ubuntu"
    mock_machine.return_value = "x86_64"
    
    result = handle_get_system_information()
    assert "Linux Ubuntu (x86_64)" in result
    assert "15.0%" in result
    assert "6.0 GB used out of 8.0 GB" in result
    assert "128.0 GB" in result

@patch('psutil.cpu_percent')
def test_safe_error_handling(mock_cpu_percent):
    mock_cpu_percent.side_effect = Exception("System error")
    result = handle_get_cpu_usage()
    assert result == "I couldn't retrieve the CPU usage right now."
