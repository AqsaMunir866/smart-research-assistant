import os
import json
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import your PDF generator function
from pdf_generator import generate_pdf_report

load_dotenv()

# Ensure Tavily key is in OS environment
tavily_key = os.getenv("TAVILY_API_KEY")
if tavily_key:
    os.environ["TAVILY_API_KEY"] = tavily_key

# Page Configuration
st.set_page_config(page_title="Smart Research Assistant", page_icon="🤖", layout="centered")

# Custom CSS for Sleek Gemini-Style Sidebar & Footer
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* Sticky footer styling */
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 8px;
        width: 100%;
        text-align: center;
        color: #888888;
        font-size: 13px;
        z-index: 99999;
        background-color: transparent;
    }

    /* Move chat input up slightly for footer */
    [data-testid="stChatInput"] {
        bottom: 35px !important;
    }

    /* Custom CSS to turn bulky sidebar buttons into sleek text list items */
    div[data-testid="stSidebar"] div.stButton > button {
        border: none !important;
        background-color: transparent !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #c9d1d9 !important;
        padding: 6px 10px !important;
        border-radius: 6px !important;
        width: 100% !important;
        box-shadow: none !important;
        transition: background-color 0.2s ease, color 0.2s ease;
    }

    /* Hover effect for history items */
    div[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #21262d !important;
        color: #ffffff !important;
    }

    /* Highlight active chat session */
    div[data-testid="stSidebar"] div.stButton > button:disabled {
        background-color: #1f2937 !important;
        color: #60a5fa !important;
        opacity: 1 !important;
    }

    /* Compact styling for the popover (⚙️) dropdown menu */
    div[data-testid="stSidebar"] div[data-testid="stPopover"] > button {
        border: none !important;
        background-color: transparent !important;
        color: #8b949e !important;
        padding: 2px 6px !important;
        box-shadow: none !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stPopover"] > button:hover {
        color: #ffffff !important;
        background-color: #21262d !important;
    }

    /* Tight, fixed-size popover context menu */
    div[data-testid="stPopoverBody"] {
        padding: 8px !important;
        max-width: 180px !important;
        min-width: 170px !important;
        overflow: hidden !important;
        border-radius: 8px !important;
    }

    div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {
        gap: 4px !important;
    }

    /* Compact input field */
    div[data-testid="stPopoverBody"] input {
        font-size: 11px !important;
        padding: 2px 6px !important;
        height: 28px !important;
        border-radius: 4px !important;
    }

    /* Compact buttons inside menu */
    div[data-testid="stPopoverBody"] button {
        font-size: 11px !important;
        padding: 2px 6px !important;
        min-height: 26px !important;
        height: 26px !important;
        border-radius: 4px !important;
        line-height: 1 !important;
        margin: 0 !important;
    }

    blockquote {
        border-left: 4px solid #2563EB !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        padding: 10px 16px !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
    }
    </style>
    
    <div class="custom-footer">
        Powered by Aqsa Rana
    </div>
""", unsafe_allow_html=True)

# Initialize LLM & Tool
@st.cache_resource
@st.cache_resource
def load_assistant():
    # Retrieve secrets safely from either Streamlit Cloud or local .env
    groq_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    tavily_key = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

    if not groq_key:
        st.error("❌ GROQ_API_KEY is missing!")
    if not tavily_key:
        st.error("❌ TAVILY_API_KEY is missing!")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=groq_key
    )
    search_tool = TavilySearch(max_results=3)
    return llm.bind_tools([search_tool]), search_tool, llm

# ==========================================
# JSON PERSISTENCE HELPERS
# ==========================================
HISTORY_FILE = "chat_history.json"

def load_history_from_json():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history_to_json():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.sessions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Failed to save history to file: {e}")

# ==========================================
# MULTI-SESSION STATE MANAGEMENT
# ==========================================
if "sessions" not in st.session_state:
    st.session_state.sessions = load_history_from_json()

if "active_session_id" not in st.session_state:
    if st.session_state.sessions:
        st.session_state.active_session_id = list(st.session_state.sessions.keys())[0]
    else:
        st.session_state.active_session_id = None

def start_new_chat():
    new_id = f"session_{len(st.session_state.sessions) + 1}"
    st.session_state.active_session_id = new_id
    st.session_state.sessions[new_id] = {
        "title": "New Chat",
        "messages": []
    }
    save_history_to_json()

# Ensure at least one active chat session exists
if not st.session_state.active_session_id or st.session_state.active_session_id not in st.session_state.sessions:
    start_new_chat()

current_session = st.session_state.sessions[st.session_state.active_session_id]

# ==========================================
# SIDEBAR (CLEAN STYLE HISTORY)
# ==========================================
with st.sidebar:
    st.markdown("### 🤖 Smart Assistant")
    st.markdown("### 🎛️ Research Settings")

    research_mode = st.radio(
        "Select Depth Mode:",
        options=["⚡ Quick Summary", "🔍 Deep Research Mode"],
        index=0
    )

    st.markdown("### 🌐 Output Language")
    target_language = st.selectbox(
        "Select Report Language:",
        options=["English", "Urdu", "Spanish", "German", "French", "Arabic"],
        index=0
    )
    st.divider()

    # New Chat Button
    if st.button("➕ New chat", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()

    st.divider()
    st.caption("Recent Searches")
    
    # Scrollable container for recent chats
    history_container = st.container(height=320, border=False)
    
    with history_container:
        for sess_id, sess_data in list(st.session_state.sessions.items()):
            title = sess_data["title"]
            display_title = title if len(title) <= 18 else title[:16] + "..."
            is_active = (sess_id == st.session_state.active_session_id)
            
            # Row layout: 80% Title button, 20% Options menu (⚙️)
            col_title, col_menu = st.columns([0.8, 0.2])
            
            with col_title:
                if st.button(f"💬 {display_title}", key=f"btn_{sess_id}", use_container_width=True, disabled=is_active):
                    st.session_state.active_session_id = sess_id
                    st.rerun()
            
            with col_menu:
                with st.popover("⚙️"):
                    st.markdown("**Options**")
                    # 1. Edit Title
                    new_name = st.text_input("Rename chat", value=title, key=f"edit_in_{sess_id}")
                    if st.button("Save Title", key=f"save_{sess_id}", use_container_width=True):
                        st.session_state.sessions[sess_id]["title"] = new_name
                        save_history_to_json()
                        st.rerun()
                    
                    st.divider()

                    # AI Answers Export
                    ai_responses = [m["content"] for m in sess_data["messages"] if m["role"] == "assistant"]
                    clean_synthesis = "\n\n".join(ai_responses) if ai_responses else "No research content available."

                    # 2. Executive Research Brief PDF
                    exec_pdf = generate_pdf_report(title, clean_synthesis)
                    st.download_button(
                        label="📄 Export PDF",
                        data=exec_pdf,
                        file_name=f"Research_Brief_{title.replace(' ', '_')[:12]}.pdf",
                        mime="application/pdf",
                        key=f"pdf_exec_{sess_id}",
                        use_container_width=True
                    )
                    
                    st.divider()
                    
                    # 3. Delete Specific Chat
                    if st.button("🗑️ Delete", key=f"del_{sess_id}", type="primary", use_container_width=True):
                        del st.session_state.sessions[sess_id]
                        if st.session_state.active_session_id == sess_id:
                            remaining = list(st.session_state.sessions.keys())
                            if remaining:
                                st.session_state.active_session_id = remaining[0]
                            else:
                                start_new_chat()
                        save_history_to_json()
                        st.rerun()

    st.divider()
    
    # Clear All History Button
    if st.button("🗑️ Clear All History", use_container_width=True):
        st.session_state.sessions = {}
        st.session_state.active_session_id = None
        save_history_to_json()
        start_new_chat()
        st.rerun()

# ==========================================
# MAIN CHAT INTERFACE
# ==========================================
st.title("🧠 Smart Research Assistant")
st.caption("Powered by Llama 3.3 (Groq) & Tavily Search API")

# Display current conversation
messages = current_session["messages"]

for idx, message in enumerate(messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show dynamic re-translation trigger under the LAST assistant message
        if message["role"] == "assistant" and idx == len(messages) - 1:
            st.markdown("---")
            if st.button(f"🌐 Regenerate in {target_language}", key=f"retrans_{idx}"):
                user_prompts = [m["content"] for m in messages if m["role"] == "user"]
                if user_prompts:
                    st.session_state.triggered_query = user_prompts[-1]
                    st.rerun()

# Handle retrigger from language action OR normal user typing
retriggered_query = st.session_state.pop("triggered_query", None)
user_input = st.chat_input("Ask your research question here...")

query = retriggered_query or user_input

if query:
    # Set initial title from first query
    if current_session["title"] == "New Chat":
        current_session["title"] = query

    # Append message if manually typed
    if not retriggered_query:
        current_session["messages"].append({"role": "user", "content": query})
        save_history_to_json()
        with st.chat_message("user"):
            st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner(f"Synthesizing research in {target_language}..."):
            try:
                # Dynamic depth instruction
                if research_mode == "⚡ Quick Summary":
                    depth_instruction = (
                        "Provide a concise, direct summary. "
                        "Focus strictly on essential facts and key takeaways."
                    )
                else:
                    depth_instruction = (
                        "Provide an exhaustive, deep-dive research report. "
                        "Structure thoroughly with clear headings, detailed breakdowns, "
                        "pros/cons, and actionable next steps."
                    )

                # System Prompt
                system_content = f"""You are an elite Smart Research Assistant.

CRITICAL WORKFLOW RULES:
1. If web search is needed, execute the search tool first without generating body text.
2. Once search results are received, synthesize your final findings ENTIRELY in {target_language}.
3. {depth_instruction}

FINAL OUTPUT FORMATTING:
Start your final answer with a 3-bullet highlights section formatted EXACTLY as:

> 📊 **Key Stat / Highlight 1:** [Key insight or number]
> 📊 **Key Stat / Highlight 2:** [Key insight or number]
> 📊 **Key Stat / Highlight 3:** [Key insight or number]

Followed by your main detailed research brief in {target_language}.
"""
                # Construct message history
                langchain_history = [SystemMessage(content=system_content)]

                for msg in current_session["messages"]:
                    if msg["role"] == "user":
                        langchain_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        langchain_history.append(AIMessage(content=msg["content"]))

                response = llm_with_tools.invoke(langchain_history)
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        if tool_call["name"] == "tavily_search":
                            tool_args = tool_call["args"]
                            search_query = tool_args.get("query", query)
                            
                            tool_output = search_tool.invoke({"query": search_query})
                            
                            final_prompt = (
                                f"Search results: {tool_output}\n\n"
                                f"Provide a comprehensive, professional answer in {target_language} based on the search results and conversation history."
                            )
                            synthesis_messages = langchain_history + [HumanMessage(content=final_prompt)]
                            final_response = llm.invoke(synthesis_messages)
                            answer = final_response.content
                else:
                    answer = response.content
                
                st.markdown(answer)
                current_session["messages"].append({"role": "assistant", "content": answer})
                save_history_to_json()
                st.rerun()

            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                st.error(error_msg)