import streamlit as st
import requests
import uuid
import json
from typing import Any, Dict, Iterator

# API configuration
API_URL = "http://backend:8000"

# Initialize session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "upload_feedback" not in st.session_state:
    st.session_state.upload_feedback = None

st.set_page_config(page_title="RAG-powered Document Assistant", layout="wide")
st.title("RAG-powered Document Assistant")


def iter_stream_events(response: requests.Response) -> Iterator[Dict[str, Any]]:
    """Yield JSON events from a streaming response (NDJSON or SSE-style data lines)."""
    for raw_line in response.iter_lines(chunk_size=1, decode_unicode=True):
        if raw_line is None:
            continue

        # requests can still return bytes when stream encoding is not resolved.
        if isinstance(raw_line, bytes):
            line = raw_line.decode("utf-8", errors="ignore").strip()
        else:
            line = raw_line.strip()

        if not line:
            continue

        # Support SSE payloads if a proxy rewrites the stream format.
        if line.startswith("data:"):
            line = line[len("data:"):].strip()

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(event, dict):
            yield event

# Sidebar for file upload
with st.sidebar:
    st.header("Upload Document")

    upload_feedback = st.session_state.upload_feedback
    if isinstance(upload_feedback, dict):
        st.success(upload_feedback["message"])
        st.info(f"Chunks created: {upload_feedback['chunk_count']}")
        st.session_state.upload_feedback = None

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file and st.button("Process Document"):
        with st.spinner("Processing..."):
            files = {"file": uploaded_file}
            upload_session_id = str(uuid.uuid4())
            try:
                response = requests.post(
                    f"{API_URL}/upload/{upload_session_id}",
                    files=files,
                    timeout=600
                )
                if response.status_code == 200:
                    payload = response.json()
                    st.session_state.session_id = upload_session_id
                    st.session_state.messages = []
                    st.session_state.upload_feedback = {
                        "message": payload["message"],
                        "chunk_count": payload["chunk_count"],
                    }
                    st.rerun()
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
        message_placeholder = st.empty()
        message_placeholder.markdown("▌")
        full_response = ""
        sources = []
        try:
            response = requests.post(
                f"{API_URL}/ask_stream",
                json={
                    "question": prompt,
                    "session_id": st.session_state.session_id
                },
                headers={"Accept": "application/x-ndjson"},
                stream=True,
                timeout=600
            )
            response.raise_for_status()

            for data in iter_stream_events(response):
                if "chunk" in data:
                    full_response += data["chunk"]
                    message_placeholder.markdown(full_response + "▌")
                if "sources" in data:
                    sources = data["sources"]
            
            message_placeholder.markdown(full_response)
            
            if sources:
                with st.expander("Sources"):
                    for i, source in enumerate(sources):
                        st.markdown(f"**Source {i+1}:** {source}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": sources
            })
        except Exception as exc:
            message_placeholder.empty()
            st.error(f"Cannot connect or read from backend. Error: {exc}")
