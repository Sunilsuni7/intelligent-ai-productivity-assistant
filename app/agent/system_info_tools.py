import os
import platform
import psutil
from app.agent.tool_registry import register_tool
from app.agent.safety import RiskLevel

@register_tool(
    name="get_cpu_usage",
    description="Returns the current CPU utilization percentage.",
    input_schema={
        "type": "object",
        "properties": {}
    },
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_get_cpu_usage():
    try:
        # Taking a brief interval to get a somewhat accurate reading
        usage = psutil.cpu_percent(interval=0.5)
        return f"CPU usage is {usage}%."
    except Exception as e:
        return "I couldn't retrieve the CPU usage right now."

@register_tool(
    name="get_memory_usage",
    description="Returns information about the system's RAM usage.",
    input_schema={
        "type": "object",
        "properties": {}
    },
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_get_memory_usage():
    try:
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        used_gb = (mem.total - mem.available) / (1024 ** 3)
        return f"RAM usage: {used_gb:.1f} GB / {total_gb:.1f} GB ({mem.percent}%)."
    except Exception as e:
        return "I couldn't retrieve the memory usage right now."

@register_tool(
    name="get_disk_usage",
    description="Returns information about the available disk space on the main system drive.",
    input_schema={
        "type": "object",
        "properties": {}
    },
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_get_disk_usage():
    try:
        # Determine the main drive, default to C:\ on Windows or / on Linux
        path = "C:\\" if os.name == 'nt' else "/"
        disk = psutil.disk_usage(path)
        total_gb = disk.total / (1024 ** 3)
        used_gb = disk.used / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        return f"Disk usage: {used_gb:.1f} GB used, {free_gb:.1f} GB free of {total_gb:.1f} GB total ({disk.percent}%)."
    except Exception as e:
        return "I couldn't retrieve the disk usage right now."

@register_tool(
    name="get_os_information",
    description="Returns information about the operating system.",
    input_schema={
        "type": "object",
        "properties": {}
    },
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_get_os_information():
    try:
        sys_os = platform.system()
        release = platform.release()
        arch = platform.machine()
        return f"You are running {sys_os} {release} on a {arch} system."
    except Exception as e:
        return "I couldn't retrieve the operating system information right now."

@register_tool(
    name="get_system_information",
    description="Returns a concise summary of the system (OS, CPU, RAM, Disk).",
    input_schema={
        "type": "object",
        "properties": {}
    },
    risk_level=RiskLevel.READ,
    requires_confirmation=False
)
def handle_get_system_information():
    try:
        cpu_usage = psutil.cpu_percent(interval=0.5)
        
        mem = psutil.virtual_memory()
        total_ram = mem.total / (1024 ** 3)
        used_ram = (mem.total - mem.available) / (1024 ** 3)
        
        path = "C:\\" if os.name == 'nt' else "/"
        disk = psutil.disk_usage(path)
        free_disk = disk.free / (1024 ** 3)
        
        sys_os = platform.system()
        release = platform.release()
        arch = platform.machine()
        
        return (f"System Information:\n"
                f"- OS: {sys_os} {release} ({arch})\n"
                f"- CPU Usage: {cpu_usage}%\n"
                f"- RAM: {used_ram:.1f} GB used out of {total_ram:.1f} GB\n"
                f"- Free Disk Space: {free_disk:.1f} GB on {path}")
    except Exception as e:
        return "I couldn't retrieve the system information right now."
