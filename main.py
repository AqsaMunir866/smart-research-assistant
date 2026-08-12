import os
from dotenv import load_dotenv

# Load environment variables from .env file first
load_dotenv()

from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

# 1. Initialize Groq LLM (automatically pulls GROQ_API_KEY from environment)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# 2. Initialize Tavily Search Tool (automatically pulls TAVILY_API_KEY from environment)
search_tool = TavilySearch(max_results=3)

# 3. Bind tools to the model
llm_with_tools = llm.bind_tools([search_tool])

if __name__ == "__main__":
    query = "What are the latest updates in LangGraph framework?"
    query = "What is the capital of France?"
    query = "Compare Python and JavaScript for backend development."
    print(f"User Query: {query}\n")
    
    # 4. Invoke the model
    response = llm_with_tools.invoke(query)
    
    # 5. Check if the model wants to call a tool and execute it safely
    if response.tool_calls:
        print("--- Executing Tool Call ---")
        for tool_call in response.tool_calls:
            if tool_call["name"] == "tavily_search":
                tool_args = tool_call["args"]
                if isinstance(tool_args, dict) and "query" in tool_args:
                    search_query = tool_args["query"]
                else:
                    search_query = str(tool_args)
                
                tool_output = search_tool.invoke({"query": search_query})
                print(f"Tool Result Found! Length of results: {len(str(tool_output))}\n")
                
                final_prompt = f"User query: {query}\n\nSearch results: {tool_output}\n\nProvide a final comprehensive answer:"
                final_response = llm.invoke(final_prompt)
                
                print("--- Final Synthesized Answer ---")
                print(final_response.content)
    else:
        print(response.content)