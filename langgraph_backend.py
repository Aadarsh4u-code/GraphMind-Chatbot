from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
import streamlit as st
import sqlite3
import requests
import os


from dotenv import load_dotenv


load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# -------------------
# 1. LLMs 
# -------------------

hugging_face_llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    # repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
    task="conversational", 
    max_new_tokens=512,
    do_sample=False,
    repetition_penalty=1.03
)
llm = ChatHuggingFace(llm=hugging_face_llm)

# -------------------
# 2. Tools
# -------------------
search_tool = DuckDuckGoSearchRun(region="us-en")


# ---------- Calculator Tool ---------------------
@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    # print("called calculator*******************************************************")
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}


# ---------- Stock Price Tool ---------------------
@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL as ALPHA_VANTAGE_API_KEY.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    print(url,'url*********************')
    r = requests.get(url)
    # print("called getstockprice*******************************************************")
    return r.json()

# ---------- Add all tools in a list and bind them with llm ---------------------
tools = [search_tool, calculator, get_stock_price]
llm_with_tools = llm.bind_tools(tools)


# -------------------
# 3. State
# -------------------

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]



# -------------------
# 4. Nodes
# -------------------

def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# ---------- Add Node with tools (Tool Node) ---------------------
tool_node = ToolNode(tools)



# -------------------
# 5. Checkpointer to Stored conversation history in Sqlite DB
# -------------------
# Ensure db folder exists
os.makedirs("db", exist_ok=True)
db_path = os.path.join("db", "chatbot.db")
conn = sqlite3.connect(database=db_path, check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)


# -------------------
# 6. Graph
# -------------------


graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")

graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge('tools', 'chat_node')
# graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)


# -------------------
# 7. Helper for list of threads
# -------------------

def retrieve_all_threads():
    try:
        all_threads = set()
        # Make sure checkpointer.list() returns a list safely
        for checkpoint in checkpointer.list(None) or []:
            thread_id = checkpoint.config.get('configurable', {}).get('thread_id')
            if thread_id:
                all_threads.add(thread_id)
        return list(all_threads)
    except Exception as e:
        st.warning(f"Failed to retrieve threads: {e}")
        return []




# -------------------
# 8. Example Run
# -------------------
# if __name__ == "__main__":

#     # Test
#     CONFIG = {'configurable': {'thread_id':'thread-2'}}
#     response = chatbot.invoke(
#                 # {'messages': [HumanMessage(content='What is the stock price of IBM?')]},  
#                 # {'messages': [HumanMessage(content='add 3 and 4')]}, 
#                 {'messages': [HumanMessage(content='What is the capital of France?')]}, 
#                 config=CONFIG,
#             )

#     print("response",response)

