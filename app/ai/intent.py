import re


# =========================================================
# INTENT DETECTION
# =========================================================

def detect_intent(message):
    text = message.lower().strip()

    # -----------------------------------------------------
    # TASK INTENTS
    # -----------------------------------------------------

    if (
        "add task" in text
        or "add a task" in text
        or "add something to my tasks" in text
        or "create task" in text
        or "create a task" in text
        or "new task" in text
        or "i need to" in text
    ):
        return "create_task"


    if (
        "complete task" in text
        or "finish task" in text
        or "mark task" in text
    ):
        return "complete_task"


    if (
        "delete task" in text
        or "remove task" in text
    ):
        return "delete_task"


    if (
        "show my pending tasks" in text
        or "show pending tasks" in text
        or "show my tasks" in text
        or "show tasks" in text
        or "list tasks" in text
        or "what do i still need to finish" in text
        or "what do i need to finish" in text
    ):
        return "list_tasks"


    # -----------------------------------------------------
    # REMINDER CREATION
    # -----------------------------------------------------

    if (
        "remind me" in text
        or "create reminder" in text
        or "create a reminder" in text
        or "add reminder" in text
        or "add a reminder" in text
        or "set reminder" in text
        or "set a reminder" in text
        or "don't let me forget" in text
        or "do not let me forget" in text
    ):
        return "create_reminder"


    # -----------------------------------------------------
    # REMINDER LIST
    # -----------------------------------------------------

    if (
        "show reminders" in text
        or "list reminders" in text
        or "my reminders" in text
        or "upcoming reminders" in text
        or "what reminders do i have" in text
        or "what reminders" in text
    ):
        return "list_reminders"


    # -----------------------------------------------------
    # COMPLETE REMINDER
    # -----------------------------------------------------

    if (
        "complete reminder" in text
        or "finish reminder" in text
        or "mark reminder" in text
        or "done reminder" in text
    ):
        return "complete_reminder"


    # -----------------------------------------------------
    # DELETE REMINDER
    # -----------------------------------------------------

    if (
        "delete reminder" in text
        or "remove reminder" in text
    ):
        return "delete_reminder"


    # -----------------------------------------------------
    # GENERAL CHAT
    # -----------------------------------------------------

    return "general_chat"


# =========================================================
# COMPUTER COMMAND DETECTION (FALLBACK)
# =========================================================

def detect_computer_command(message):
    text_lower = message.lower().strip()
    
    if re.search(r"^(go to|take me to|open)\s+youtube$", text_lower):
        return {"tool_name": "open_website", "arguments": {"url": "https://youtube.com"}}
    
    m = re.search(r"^search\s+youtube\s+for\s+(.+)$", message.strip(), re.IGNORECASE)
    if m:
        return {"tool_name": "search_youtube", "arguments": {"query": m.group(1).strip()}}
        
    m = re.search(r"^search\s+google\s+for\s+(.+)$", message.strip(), re.IGNORECASE)
    if m:
        return {"tool_name": "search_google", "arguments": {"query": m.group(1).strip()}}
        
    m = re.search(r"^open\s+(vs code|visual studio code)$", text_lower)
    if m:
        return {"tool_name": "open_application", "arguments": {"app_name": "vs code"}}
        
    m = re.search(r"^open\s+(calculator)$", text_lower)
    if m:
        return {"tool_name": "open_application", "arguments": {"app_name": "calculator"}}
        
    m = re.search(r"^open\s+(.+)$", text_lower)
    if m and not m.group(1).startswith("youtube"):
        return {"tool_name": "open_application", "arguments": {"app_name": m.group(1).strip()}}
        
    m = re.search(r"^(close|exit|quit)\s+(vs code|visual studio code)$", text_lower)
    if m:
        return {"tool_name": "close_application", "arguments": {"app_name": "vs code"}}
        
    m = re.search(r"^(close|exit|quit)\s+(chrome)$", text_lower)
    if m:
        return {"tool_name": "close_application", "arguments": {"app_name": "chrome"}}

    if re.search(r"^(close|exit|quit)\s+(the\s+)?browser$", text_lower):
        return {"tool_name": "close_browser", "arguments": {}}

    m = re.search(r"^(close|exit|quit)\s+(.+)$", text_lower)
    if m:
        return {"tool_name": "close_application", "arguments": {"app_name": m.group(2).strip()}}
        
    m = re.search(r"^play\s+(.+)$", message.strip(), re.IGNORECASE)
    if m:
        return {"tool_name": "play_media", "arguments": {"query": m.group(1).strip()}}
    if text_lower == "play music" or text_lower == "play":
        return {"tool_name": "play_media", "arguments": {}}
        
    if text_lower.startswith("pause"):
        return {"tool_name": "pause_media", "arguments": {}}
        
    if text_lower.startswith("resume"):
        return {"tool_name": "resume_media", "arguments": {}}
        
    if text_lower.startswith("stop"):
        return {"tool_name": "stop_media", "arguments": {}}
        
    if "increase volume" in text_lower or "volume up" in text_lower:
        return {"tool_name": "volume_up", "arguments": {}}
    if "decrease volume" in text_lower or "volume down" in text_lower:
        return {"tool_name": "volume_down", "arguments": {}}
    if "mute" in text_lower:
        return {"tool_name": "mute", "arguments": {}}
        
    return None


# =========================================================
# TASK TITLE EXTRACTION
# =========================================================

def extract_task_title(message):

    text = message.strip()

    patterns = [
        r"^add\s+(?:a\s+)?task\s+(?:to\s+)?(.+)$",
        r"^create\s+(?:a\s+)?task\s+(?:to\s+)?(.+)$",
        r"^new\s+task\s+(?:to\s+)?(.+)$",
        r"^i need to\s+(.+)$",
        r"add something to my tasks(?:\s+like|\s+such as|\s+to)?\s*(.*)$"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            title = match.group(1).strip()

            title = re.sub(
                r"\b(?:with\s+)?(?:high|medium|low)\s+priority\b",
                "",
                title,
                flags=re.IGNORECASE
            )

            title = re.sub(
                r"\btoday\b",
                "",
                title,
                flags=re.IGNORECASE
            )

            title = re.sub(
                r"\btomorrow\b",
                "",
                title,
                flags=re.IGNORECASE
            )

            title = re.sub(
                r"\b(?:due\s+)?(?:on|by)?\s*\d{4}-\d{2}-\d{2}\b",
                "",
                title,
                flags=re.IGNORECASE
            )

            title = re.sub(
                r"\s+",
                " ",
                title
            ).strip()

            title = re.sub(
                r"[,\-:\?\.]+$",
                "",
                title
            ).strip()

            if not title:
                title = "New Task"

            return title

    return text


# =========================================================
# TASK PRIORITY
# =========================================================

def extract_task_priority(message):

    text = message.lower()

    if re.search(
        r"\bhigh\s+priority\b",
        text
    ):
        return "high"

    if re.search(
        r"\bmedium\s+priority\b",
        text
    ):
        return "medium"

    if re.search(
        r"\blow\s+priority\b",
        text
    ):
        return "low"

    return "medium"


# =========================================================
# TASK DUE DATE
# =========================================================

def extract_task_due_date(message):

    from datetime import datetime, timedelta

    text = message.lower()

    now = datetime.now()


    if "tomorrow" in text:

        return (
            now.date()
            + timedelta(days=1)
        ).isoformat()


    if "today" in text:

        return now.date().isoformat()


    date_match = re.search(
        r"\b(20\d{2})-(\d{2})-(\d{2})\b",
        text
    )


    if date_match:

        return (
            f"{date_match.group(1)}-"
            f"{date_match.group(2)}-"
            f"{date_match.group(3)}"
        )


    return None


# =========================================================
# REMINDER TITLE EXTRACTION
# =========================================================

def extract_reminder_title(message):

    text = message.strip()

    patterns = [
        r"^create\s+(?:a\s+)?reminder\s+(?:to\s+)?(.+)$",
        r"^add\s+(?:a\s+)?reminder\s+(?:to\s+)?(.+)$",
        r"^set\s+(?:a\s+)?reminder\s+(?:to\s+)?(.+)$",
        r"^remind\s+me\s+to\s+(.+)$",
        r"^don'?t let me forget to\s+(.+)$",
        r"^do not let me forget to\s+(.+)$"
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )


        if match:

            title = match.group(1).strip()


            title = re.sub(
                r"\btomorrow\b",
                "",
                title,
                flags=re.IGNORECASE
            )


            title = re.sub(
                r"\btoday\b",
                "",
                title,
                flags=re.IGNORECASE
            )


            title = re.sub(
                r"\bat\s+\d{1,2}:\d{2}\b",
                "",
                title,
                flags=re.IGNORECASE
            )


            title = re.sub(
                r"\bat\s+\d{1,2}(?:\s*:\s*\d{2})?\s*(?:am|pm)\b",
                "",
                title,
                flags=re.IGNORECASE
            )


            title = re.sub(
                r"\b(?:on|by|due\s+on|due\s+by)?\s*\d{4}-\d{2}-\d{2}\b",
                "",
                title,
                flags=re.IGNORECASE
            )


            title = re.sub(
                r"\bat\s*$",
                "",
                title,
                flags=re.IGNORECASE
            )


            title = re.sub(
                r"\bon\s*$",
                "",
                title,
                flags=re.IGNORECASE
            )


            title = re.sub(
                r"\bby\s*$",
                "",
                title,
                flags=re.IGNORECASE
            )


            title = re.sub(
                r"\s+",
                " ",
                title
            ).strip()


            title = re.sub(
                r"[,\-:\?\.]+$",
                "",
                title
            ).strip()


            return title


    return text


# =========================================================
# TASK ID EXTRACTION
# =========================================================

def extract_task_id(message):

    match = re.search(
        r"\b\d+\b",
        message
    )

    if match:

        return int(
            match.group()
        )

    return None


# =========================================================
# REMINDER ID EXTRACTION
# =========================================================

def extract_reminder_id(message):

    match = re.search(
        r"\b\d+\b",
        message
    )

    if match:

        return int(
            match.group()
        )

    return None
