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
            try:
                response = requests.post(
                    f"{API_URL}/upload/{st.session_state.session_id}",
                    files=files,
                    timeout=600
                )
                if response.status_code == 200:
                    st.success(f"{response.json()['message']}")
                    st.info(f"Chunks created: {response.json()['chunk_count']}")
                else:
                    detail = response.json().get("detail", "Unknown backend error")
                    st.error(f"Error: {detail}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Cannot connect to backend at {API_URL}. Error: {exc}")

    st.divider()

    st.header("Chat History")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    try:
        sess_response = requests.get(f"{API_URL}/sessions", timeout=5)
        if sess_response.status_code == 200:
            sessions = sess_response.json()
            if not sessions:
                st.caption("No past sessions found.")
            for s in sessions:
                sid = s['session_id']
                date_str = s['last_active'].split('T')[0]
                if st.button(f"Chat {sid[:6]} ({date_str})", key=f"btn_{sid}", use_container_width=True):
                    st.session_state.session_id = sid
                    hist_resp = requests.get(f"{API_URL}/history/{sid}", timeout=5)
                    if hist_resp.status_code == 200:
                        st.session_state.messages = hist_resp.json()
                    else:
                        st.session_state.messages = []
                    st.rerun()
    except Exception:
        st.caption("Could not load history.")

    st.divider()
    st.caption(f"Current Session: {st.session_state.session_id[:8]}...")


# Main chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message['content'])
        if "sources" in message:
            with st.expander("View sources"):
                for i, source in enumerate(message["sources"]):
                    st.markdown(f"**Source {i+1}:** {source}")

# Chat input
if prompt := st.chat_input("Ask a question about your document"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={
                        "question": prompt,
                        "session_id": st.session_state.session_id
                    },
                    timeout=600
                )
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data["sources"]
                    st.markdown(answer)
                    if sources:
                        with st.expander("Sources"):
                            for i, source in enumerate(sources):
                                st.markdown(f"**Source {i+1}:** {source}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                else:
                    detail = response.json().get("detail", "Unknown backend error")
                    st.error(f"Error: {detail}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Cannot connect to backend at {API_URL}. Error: {exc}")
