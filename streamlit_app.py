import streamlit as st
import requests
import json
import time
import uuid

from app.voice.speech_to_text import listen_and_recognize
from app.voice.text_to_speech import speak

st.set_page_config(
    page_title="AI Personal Assistant",
    layout="centered",
    initial_sidebar_state="collapsed"
)

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500&family=Inter:wght@300;400;500;600&display=swap');

    :root {
        --bg-base: #09090b;
        --bg-surface: #18181b;
        --bg-surface-hover: #27272a;
        --text-main: #f4f4f5;
        --text-muted: #a1a1aa;
        --accent: #22d3ee;
        --accent-glow: rgba(34, 211, 238, 0.4);
        --border: #27272a;
    }

    [data-testid="stAppViewContainer"] { background-color: var(--bg-base); color: var(--text-main); font-family: 'Inter', sans-serif; }
    [data-testid="stHeader"] { display: none; }
    footer { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    [data-testid="stSidebar"] { display: none; }
    .block-container { padding-top: 4rem !important; max-width: 800px !important; }

    /* Header */
    .header-container { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin-bottom: 2rem; }
    .header-title { font-size: 1.2rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-main); }
    .header-status { font-family: 'Fira Code', monospace; font-size: 0.8rem; color: #10b981; display: flex; align-items: center; gap: 0.5rem; }
    .status-dot { width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981; animation: pulse 2s infinite; }
    
    @keyframes pulse { 0% { opacity: 1; box-shadow: 0 0 8px #10b981; } 50% { opacity: 0.5; box-shadow: 0 0 2px #10b981; } 100% { opacity: 1; box-shadow: 0 0 8px #10b981; } }

    /* Subtitle & State */
    .subtitle { text-align: center; font-size: 1rem; color: var(--text-muted); letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 3rem; }
    
    .agent-state-container { text-align: center; margin-bottom: 3rem; min-height: 80px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .state-icon { font-size: 2rem; margin-bottom: 0.5rem; color: var(--accent); }
    .state-text { font-family: 'Fira Code', monospace; font-size: 0.9rem; color: var(--accent); letter-spacing: 0.05em; text-transform: uppercase; }

    /* Animations for states */
    .spin { animation: spin 1.5s linear infinite; }
    @keyframes spin { 100% { transform: rotate(360deg); } }
    .pulse-glow { animation: pulseGlow 1.5s infinite; }
    @keyframes pulseGlow { 0% { text-shadow: 0 0 5px var(--accent); transform: scale(1); } 50% { text-shadow: 0 0 20px var(--accent); transform: scale(1.1); } 100% { text-shadow: 0 0 5px var(--accent); transform: scale(1); } }
    .wave { display: inline-block; animation: wave 1.2s infinite; }
    @keyframes wave { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }

    /* Chat Messages */
    .chat-scroll { max-height: 40vh; overflow-y: auto; padding-right: 10px; display: flex; flex-direction: column; gap: 1.5rem; margin-bottom: 2rem; }
    .chat-scroll::-webkit-scrollbar { width: 6px; }
    .chat-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    .chat-role { font-family: 'Fira Code', monospace; font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.1em; }
    .chat-bubble { padding: 1.2rem; border-radius: 8px; background: var(--bg-surface); border: 1px solid var(--border); line-height: 1.6; font-size: 0.95rem; color: var(--text-main); }
    .chat-bubble.user { border-left: 2px solid var(--text-muted); }
    .chat-bubble.assistant { border-left: 2px solid var(--accent); }

    /* Input Bar */
    .input-wrapper { display: flex; align-items: center; background: var(--bg-surface); border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem; transition: all 0.3s ease; }
    .input-wrapper:focus-within { border-color: var(--accent); box-shadow: 0 0 15px var(--accent-glow); }
    
    div[data-testid="stTextInput"] { margin-bottom: 0 !important; }
    div[data-testid="stTextInput"] input { background: transparent !important; border: none !important; box-shadow: none !important; color: var(--text-main) !important; font-family: 'Inter', sans-serif !important; font-size: 1rem !important; padding: 0.5rem 1rem !important; }
    div[data-testid="stTextInput"] input:focus { border: none !important; box-shadow: none !important; }
    
    /* Buttons */
    div[data-testid="stButton"] button { background: transparent; border: none; color: var(--text-muted); padding: 0.5rem 1rem; border-radius: 6px; transition: all 0.2s; }
    div[data-testid="stButton"] button:hover { background: var(--bg-surface-hover); color: var(--text-main); }
    
    .mic-btn-wrapper div[data-testid="stButton"] button { background: transparent; border: none; color: var(--accent); font-size: 1.4rem; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
    .mic-btn-wrapper div[data-testid="stButton"] button:hover { background: var(--accent-dim); transform: scale(1.05); }

    /* Try Saying Tags */
    .try-saying { text-align: center; margin-top: 1.5rem; margin-bottom: 2rem; }
    .try-saying-label { font-family: 'Fira Code', monospace; font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.8rem; }
    .tag-container { display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; }
    .tag { background: var(--bg-surface); border: 1px solid var(--border); color: var(--text-muted); font-size: 0.85rem; padding: 0.4rem 1rem; border-radius: 20px; cursor: pointer; transition: all 0.2s; }
    .tag:hover { background: var(--bg-surface-hover); border-color: var(--accent); color: var(--text-main); }

    /* Divider */
    .divider { height: 1px; background: var(--border); width: 100%; margin: 2rem 0; }

    /* Activity Feed */
    .activity-section { margin-top: 2rem; }
    .activity-title { font-family: 'Fira Code', monospace; font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem; }
    .activity-item { display: flex; align-items: center; gap: 1rem; padding: 0.8rem 0; border-bottom: 1px dashed var(--border); font-family: 'Inter', sans-serif; font-size: 0.85rem; color: var(--text-main); }
    .activity-icon { color: #10b981; font-size: 1rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# STATE INITIALIZATION
# ---------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "agent_state" not in st.session_state:
    st.session_state.agent_state = "ready"
if "session_messages" not in st.session_state:
    st.session_state.session_messages = [{"role": "ASSISTANT", "content": "How can I assist you today?"}]
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None
if "pending_source" not in st.session_state:
    st.session_state.pending_source = None
if "last_spoken_text" not in st.session_state:
    st.session_state.last_spoken_text = None

def get_recent_activity():
    try:
        from app.database.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, tool_name, arguments, status FROM tool_activity WHERE session_id=? ORDER BY id DESC LIMIT 3", (st.session_state.session_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

def handle_quick_command(cmd):
    st.session_state.session_messages.append({"role": "USER", "content": cmd})
    st.session_state.pending_input = cmd
    st.session_state.pending_source = "text"
    st.session_state.agent_state = "thinking"

# ---------------------------------------------------------
# LAYOUT
# ---------------------------------------------------------

# Header
st.markdown("""
<div class="header-container">
    <div class="header-title">AI Personal Assistant</div>
    <div class="header-status"><div class="status-dot"></div>ONLINE</div>
</div>
""", unsafe_allow_html=True)

# Subtitle
st.markdown('<div class="subtitle">Understand. Think. Act.</div>', unsafe_allow_html=True)

# Dynamic State Indicator
state = st.session_state.agent_state
state_html = ""
if state == "ready":
    state_html = '<div class="agent-state-container"><div class="state-icon">◉</div><div class="state-text">Ready to assist</div></div>'
elif state == "listening":
    state_html = '<div class="agent-state-container"><div class="state-icon pulse-glow">🎙</div><div class="state-text">Listening...</div></div>'
elif state == "thinking":
    state_html = '<div class="agent-state-container"><div class="state-icon spin">🧠</div><div class="state-text">Understanding...</div></div>'
elif state == "executing":
    state_html = '<div class="agent-state-container"><div class="state-icon spin">⚡</div><div class="state-text">Executing...</div></div>'
elif state == "speaking":
    state_html = '<div class="agent-state-container"><div class="state-icon wave">🔊</div><div class="state-text">Speaking...</div></div>'
elif state == "completed":
    state_html = '<div class="agent-state-container"><div class="state-icon">✓</div><div class="state-text">Task Completed</div></div>'
else:
    state_html = f'<div class="agent-state-container"><div class="state-icon">◉</div><div class="state-text">{state}</div></div>'

st.markdown(state_html, unsafe_allow_html=True)

# Interrupt Buttons (Only if active)
if state in ["listening", "speaking"]:
    st.markdown('<div style="display:flex; justify-content:center; margin-top:-20px; margin-bottom:20px;">', unsafe_allow_html=True)
    if st.button("🛑 Stop"):
        st.session_state.agent_state = "ready"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Chat History (Only show last few if it gets too long, but scroll handles it)
if len(st.session_state.session_messages) > 0:
    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
    # Display the last 4 interactions to keep the UI clean and centered
    display_msgs = st.session_state.session_messages[-4:]
    for msg in display_msgs:
        role = msg["role"]
        content = msg["content"]
        role_class = role.lower()
        st.markdown(f'<div class="chat-role">{role}</div><div class="chat-bubble {role_class}">{content}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Input Box
st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)
input_col, mic_col = st.columns([90, 10])
with input_col:
    with st.form("chat_form", clear_on_submit=True):
        cols = st.columns([9, 1])
        with cols[0]:
            user_text = st.text_input("Ask anything...", label_visibility="collapsed", placeholder="Ask anything...")
        with cols[1]:
            submitted = st.form_submit_button("⏎")
        if submitted and user_text:
            st.session_state.session_messages.append({"role": "USER", "content": user_text})
            st.session_state.pending_input = user_text
            st.session_state.pending_source = "text"
            st.session_state.agent_state = "thinking"
            st.rerun()

with mic_col:
    st.markdown('<div class="mic-btn-wrapper">', unsafe_allow_html=True)
    if st.button("🎙"):
        st.session_state.agent_state = "listening"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Try Saying Suggestions
st.markdown("""
<div class="try-saying">
    <div class="try-saying-label">Try saying:</div>
    <div class="tag-container">
        <span class="tag">"Open YouTube"</span>
        <span class="tag">"Play music"</span>
        <span class="tag">"Open VS Code"</span>
        <span class="tag">"Remind me to study"</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Recent Activity
st.markdown('<div class="activity-section"><div class="activity-title">Recent Activity</div>', unsafe_allow_html=True)
activities = get_recent_activity()
if not activities:
    st.markdown('<div class="activity-item" style="color:var(--text-muted); justify-content:center;">No recent activity</div>', unsafe_allow_html=True)
else:
    for act in activities:
        icon = "✓" if act["status"] == "SUCCESS" else "✗"
        icon_color = "#10b981" if act["status"] == "SUCCESS" else "#ef4444"
        tool_fmt = act["tool_name"].replace("_", " ").title()
        
        args = {}
        try:
            if act["arguments"]:
                args = json.loads(act["arguments"])
        except:
            pass
            
        desc = tool_fmt
        if "app_name" in args: desc += f" ({args['app_name']})"
        elif "query" in args: desc += f" ({args['query']})"
        elif "title" in args: desc += f" ({args['title']})"
        elif "url" in args: desc += f" ({args['url']})"
            
        st.markdown(f'<div class="activity-item"><span style="color:{icon_color}; font-weight:bold;">{icon}</span> <span>Executed {desc}</span></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# BACKGROUND EXECUTION LOGIC
# ---------------------------------------------------------

if st.session_state.agent_state == "listening":
    success, text = listen_and_recognize()
    if success:
        st.session_state.session_messages.append({"role": "USER", "content": text})
        st.session_state.pending_input = text
        st.session_state.pending_source = "voice"
        st.session_state.agent_state = "thinking"
    else:
        st.session_state.agent_state = "ready"
        st.error(f"Voice error: {text}")
    st.rerun()

elif st.session_state.agent_state == "thinking":
    user_input = st.session_state.pending_input
    source = st.session_state.pending_source
    
    st.session_state.agent_state = "executing"
    try:
        response = requests.post("http://127.0.0.1:8000/chat", json={"message": user_input, "source": source, "session_id": st.session_state.session_id}, timeout=45)
        data = response.json()
        reply = data.get("message", "Action completed.")
        
        st.session_state.session_messages.append({"role": "ASSISTANT", "content": reply})
        
        if source == "voice":
            st.session_state.agent_state = "speaking"
            st.session_state.last_spoken_text = reply
        else:
            st.session_state.agent_state = "completed"
    except Exception as e:
        st.session_state.session_messages.append({"role": "ASSISTANT", "content": f"Backend connection failed: {e}"})
        st.session_state.agent_state = "ready"
        
    st.rerun()

elif st.session_state.agent_state == "speaking":
    text_to_speak = st.session_state.last_spoken_text
    if text_to_speak:
        speak(text_to_speak)
    st.session_state.agent_state = "completed"
    st.rerun()

elif st.session_state.agent_state == "completed":
    time.sleep(1.5)
    st.session_state.agent_state = "ready"
    st.rerun()
