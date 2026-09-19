import json
from app.database.database import get_connection
from app.security.security_models import AuditEvent
from app.security.sanitization import sanitize_dict
from datetime import datetime
from zoneinfo import ZoneInfo

def log_audit_event(session_id: str, event: AuditEvent):
    """Logs a sanitized security/audit event to the database."""
    conn = get_connection()
    cursor = conn.cursor()

    now_ist = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    sanitized_args = sanitize_dict(event.arguments or {})
    args_json = json.dumps(sanitized_args)

    # We must ensure the audit_logs table exists (it will be added to database.py)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            session_id TEXT,
            action TEXT,
            tool_name TEXT,
            risk_level TEXT,
            result TEXT,
            reason TEXT,
            arguments TEXT
        )
    ''')

    cursor.execute('''
        INSERT INTO audit_logs (timestamp, session_id, action, tool_name, risk_level, result, reason, arguments)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now_ist, session_id, event.action, event.tool_name, event.risk_level, event.result, event.reason, args_json))

    conn.commit()
    conn.close()

def get_recent_audit_logs(limit: int = 50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
