import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

# Load environment variables from .env file
load_dotenv()

# Page Configuration
st.set_page_config(page_title="Smart Research Assistant", page_icon="🤖", layout="centered")

# Custom Styling & Fixed Bottom Footer
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTextInput textarea { color: #ffffff; }
    
    /* Move chat input up slightly to make room for footer */
    [data-testid="stChatInput"] {
        bottom: 35px !important;
    }
    
    /* Sticky footer styling at the absolute bottom */
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
    </style>
    
    <div class="custom-footer">
        Powered by Aqsa Rana
    </div>
""", unsafe_allow_html=True)

st.title("🧠 Smart Research Assistant")
st.caption("Powered by Llama 3.3 (Groq) & Tavily Search API")

# Initialize LLM & Tool explicitly with API keys
@st.cache_resource
def load_assistant():
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    search_tool = TavilySearch(
        max_results=3,
        tavily_api_key=os.getenv("TAVILY_API_KEY")
    )
    return llm.bind_tools([search_tool]), search_tool, llm

llm_with_tools, search_tool, llm = load_assistant()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input box
if query := st.chat_input("Ask your research question here..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Searching the web and analyzing data..."):
            try:
                response = llm_with_tools.invoke(query)
                
                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        if tool_call["name"] == "tavily_search":
                            tool_args = tool_call["args"]
                            search_query = tool_args.get("query", query)
                            
                            # Execute search tool
                            tool_output = search_tool.invoke({"query": search_query})
                            
                            # Synthesize final answer
                            final_prompt = f"User query: {query}\n\nSearch results: {tool_output}\n\nProvide a comprehensive, professional answer based on the search results:"
                            final_response = llm.invoke(final_prompt)
                            answer = final_response.content
                else:
                    answer = response.content
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                st.error(error_msg)