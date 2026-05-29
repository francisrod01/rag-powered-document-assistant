import streamlit as st
import uuid

# API configuration
API_URL = "http://backend:8000"

# Initialize session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

st.set_page_config(page_title="RAG-powered Document Assistant", layout="wide")
st.title("RAG-powered Document Assistant")

# Main chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message['content'])
        if "sources" in message:
            with st.expander("View sources"):
                for i, source in enumerate(message["sources"]):
                    st.text(f"Source {i+1}: {source}")
