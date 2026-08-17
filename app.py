import os
import json
import streamlit as st
from dotenv import load_dotenv

# Execute load_dotenv() FIRST before reading environment variables
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.tools import TavilySearchResults

# Import your PDF generator function
from pdf_generator import generate_pdf_report

# Safe secret retrieval helper function
def get_secret_key(key_name):
    val = os.getenv(key_name)
    if val:
        return val
    try:
        return st.secrets.get(key_name)
    except Exception:
        return None

# Cached function to instantiate model & tools
@st.cache_resource
def get_assistant_components():
    groq_key = get_secret_key("GROQ_API_KEY")
    tavily_key = get_secret_key("TAVILY_API_KEY")

    if not groq_key or not tavily_key:
        st.error("⚠️ API Keys are missing! Please check your Streamlit Secrets or local .env file.")

    llm = ChatGroq(
        model="qwen/qwen3.6-27b",
        temperature=0,
        groq_api_key=groq_key
    )

    search_tool = TavilySearchResults(
        max_results=3,
        tavily_api_key=tavily_key
    )

    llm_with_tools = llm.bind_tools([search_tool])

    return llm_with_tools, search_tool, llm

# Global initialization
llm_with_tools, search_tool, llm = get_assistant_components()

# Sync Tavily Key to OS environment for LangChain internal tool access
tavily_key_env = get_secret_key("TAVILY_API_KEY")
if tavily_key_env:
    os.environ["TAVILY_API_KEY"] = tavily_key_env

# Page Configuration
st.set_page_config(page_title="Smart Research Assistant", page_icon="🤖", layout="centered")

# Custom CSS for Sleek Gemini-Style Sidebar & Footer
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
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
    [data-testid="stChatInput"] { bottom: 35px !important; }
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
    }
    div[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #21262d !important;
        color: #ffffff !important;
    }
    div[data-testid="stSidebar"] div.stButton > button:disabled {
        background-color: #1f2937 !important;
        color: #60a5fa !important;
        opacity: 1 !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stPopover"] > button {
        border: none !important;
        background-color: transparent !important;
        color: #8b949e !important;
        padding: 2px 6px !important;
    }
    div[data-testid="stPopoverBody"] {
        padding: 8px !important;
        max-width: 180px !important;
        min-width: 170px !important;
        overflow: hidden !important;
        border-radius: 8px !important;
    }
    blockquote {
        border-left: 4px solid #2563EB !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        padding: 10px 16px !important;
        border-radius: 6px !important;
    }
    </style>
    <div class="custom-footer">Powered by Aqsa Rana</div>
""", unsafe_allow_html=True)

# Persistence Helpers
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
        st.error(f"Failed to save history: {e}")

# Session Management
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

if not st.session_state.active_session_id or st.session_state.active_session_id not in st.session_state.sessions:
    start_new_chat()

current_session = st.session_state.sessions[st.session_state.active_session_id]

# Sidebar UI
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

    if st.button("➕ New chat", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()

    st.divider()
    st.caption("Recent Searches")
    
    history_container = st.container(height=320, border=False)
    
    with history_container:
        for sess_id, sess_data in list(st.session_state.sessions.items()):
            title = sess_data["title"]
            display_title = title if len(title) <= 18 else title[:16] + "..."
            is_active = (sess_id == st.session_state.active_session_id)
            
            col_title, col_menu = st.columns([0.8, 0.2])
            
            with col_title:
                if st.button(f"💬 {display_title}", key=f"btn_{sess_id}", use_container_width=True, disabled=is_active):
                    st.session_state.active_session_id = sess_id
                    st.rerun()
            
            with col_menu:
                with st.popover("⚙️"):
                    st.markdown("**Options**")
                    new_name = st.text_input("Rename chat", value=title, key=f"edit_in_{sess_id}")
                    if st.button("Save Title", key=f"save_{sess_id}", use_container_width=True):
                        st.session_state.sessions[sess_id]["title"] = new_name
                        save_history_to_json()
                        st.rerun()
                    
                    st.divider()

                    ai_responses = [m["content"] for m in sess_data["messages"] if m["role"] == "assistant"]
                    clean_synthesis = "\n\n".join(ai_responses) if ai_responses else "No research content available."

                    try:
                        exec_pdf = generate_pdf_report(title, clean_synthesis)
                        st.download_button(
                            label="📄 Export PDF",
                            data=exec_pdf,
                            file_name=f"Research_Brief_{title.replace(' ', '_')[:12]}.pdf",
                            mime="application/pdf",
                            key=f"pdf_exec_{sess_id}",
                            use_container_width=True
                        )
                    except Exception as pdf_err:
                        st.error("Could not render PDF preview.")
                    
                    st.divider()
                    
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
    
    if st.button("🗑️ Clear All History", use_container_width=True):
        st.session_state.sessions = {}
        st.session_state.active_session_id = None
        save_history_to_json()
        start_new_chat()
        st.rerun()

# Main Chat
st.title("🧠 Smart Research Assistant")
st.caption("Powered by Groq & Tavily Search API")

messages = current_session["messages"]

for idx, message in enumerate(messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if message["role"] == "assistant" and idx == len(messages) - 1:
            st.markdown("---")
            if st.button(f"🌐 Regenerate in {target_language}", key=f"retrans_{idx}"):
                user_prompts = [m["content"] for m in messages if m["role"] == "user"]
                if user_prompts:
                    st.session_state.triggered_query = user_prompts[-1]
                    st.rerun()

retriggered_query = st.session_state.pop("triggered_query", None)
user_input = st.chat_input("Ask your research question here...")

query = retriggered_query or user_input

if query:
    if current_session["title"] == "New Chat":
        current_session["title"] = query

    if not retriggered_query:
        current_session["messages"].append({"role": "user", "content": query})
        save_history_to_json()
        with st.chat_message("user"):
            st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner(f"Synthesizing research in {target_language}..."):
            try:
                if research_mode == "⚡ Quick Summary":
                    depth_instruction = "Provide a concise summary highlighting essential facts."
                else:
                    depth_instruction = "Provide an exhaustive research report with headings, breakdowns, and detailed context."

                system_content = f"""You are an elite Smart Research Assistant.

CRITICAL WORKFLOW RULES:
1. If web search is needed, execute the search tool first.
2. Synthesize findings ENTIRELY in {target_language}.
3. {depth_instruction}

FINAL OUTPUT FORMATTING:
Start your final answer with a 3-bullet highlights section formatted as:

> 📊 **Key Stat / Highlight 1:** [Key insight or number]
> 📊 **Key Stat / Highlight 2:** [Key insight or number]
> 📊 **Key Stat / Highlight 3:** [Key insight or number]

Followed by your detailed research report.
"""
                langchain_history = [SystemMessage(content=system_content)]

                for msg in current_session["messages"]:
                    if msg["role"] == "user":
                        langchain_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        langchain_history.append(AIMessage(content=msg["content"]))

                response = llm_with_tools.invoke(langchain_history)
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        if tool_call["name"] in ["tavily_search", "tavily_search_results_json"]:
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