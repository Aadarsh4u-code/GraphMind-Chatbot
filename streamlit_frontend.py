import streamlit as st
from langgraph_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
from utils import add_thread, generate_thread_id, load_conversation, reset_chat


# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])






# **************************************** Sidebar UI *********************************
st.sidebar.title("💬 Custom Chat UI ")

if st.sidebar.button("New Chat", type='primary'):
    reset_chat()

st.sidebar.header("My Conversations")



for thread_id in st.session_state.get('chat_threads', [])[::-1]:
    
    # Load messages for this thread
    messages = load_conversation(thread_id, chatbot)  # returns list of HumanMessage/AIMessage

    # Prepare message_history for session state
    temp_messages = []
    first_user_msg = None

    if messages:
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})
        
        # Get first user message for display
        first_user_msg = next(
            (msg.content for msg in messages if isinstance(msg, HumanMessage)), 
            None
        )

    # Update message_history for current thread
    if st.session_state.get('thread_id') == thread_id:
        st.session_state['message_history'] = temp_messages

    # Sidebar button title
    if first_user_msg:
        button_title = " ".join(first_user_msg.split()[:4])  # first 4 words
    else:
        button_title = "Current Chat"

    # Display button
    if st.sidebar.button(button_title, key=str(thread_id)):
        st.session_state['thread_id'] = thread_id
        st.session_state['message_history'] = temp_messages



# **************************************** Main UI ************************************

# Loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input("Type Here ...")

if user_input:

    # First add the message to chat_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # **************** Streaming Setup ******************
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    with st.chat_message('assistant'):

        # --- First: Show "Thinking..." ---
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("🤔 Thinking...")

        # --- Now: Stream AI response ---
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]}, 
                config=CONFIG,
                stream_mode= 'messages'
            )
        )
        # --- Remove "Thinking..." once output is ready ---
        thinking_placeholder.empty()

    # Save AI response 
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    
st.write(st.session_state)











# messages = [
#     {"sender": "ai", "message": "Hello! How can I help you today?"},
#     {"sender": "user", "message": "Tell me about LangGraph."},
#     {"sender": "ai", "message": "LangGraph is a framework for stateful AI apps."},
# ]

# for msg in messages:
#     if msg["sender"] == "user":
#         col1, col2 = st.columns([2, 1])
#         with col2:
#             st.markdown(
#                 f"<div style='background-color:#2563eb;color:white;padding:8px;border-radius:12px;text-align:right;'>{msg['message']}</div>",
#                 unsafe_allow_html=True,
#             )
#     else:
#         col1, col2 = st.columns([1, 2])
#         with col1:
#             st.markdown(
#                 f"<div style='background-color:#e5e7eb;color:black;padding:8px;border-radius:12px;text-align:left;'>{msg['message']}</div>",
#                 unsafe_allow_html=True,
#             )
