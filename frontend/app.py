import streamlit as st
import requests
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

# Sidebar for file upload
with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file and st.button("Process Document"):
        with st.spinner("Processing..."):
            files = {"file": uploaded_file}
            response = requests.post(
                f"{API_URL}/upload/{st.session_state.session_id}",
                files=files
            )
            if response.status_code == 200:
                st.success(f"{response.json()['message']}")
                st.info(f"Chunks created: {response.json()['chunk_count']}")
            else:
                st.error(f"Error: {response.json()['detail']}")

    st.divider()
    st.caption(f"Session ID: {st.session_state.session_id[:8]}...")


# Main chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message['content'])
        if "sources" in message:
            with st.expander("View sources"):
                for i, source in enumerate(message["sources"]):
                    st.text(f"Source {i+1}: {source}")
