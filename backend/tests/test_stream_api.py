import requests
import uuid
import json
import sys
import os
import urllib.request

API_URL = "http://localhost:8000"
session_id = str(uuid.uuid4())

output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output")
os.makedirs(output_dir, exist_ok=True)
pdf_path = os.path.join(output_dir, "sample.pdf")

if not os.path.exists(pdf_path):
    print(f"Downloading dummy PDF to {pdf_path}...")
    urllib.request.urlretrieve("https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf", pdf_path)

print(f"Uploading {pdf_path} for session {session_id}...")
with open(pdf_path, 'rb') as f:
    files = {"file": f}
    upload_res = requests.post(f"{API_URL}/upload/{session_id}", files=files)

print("Upload response:", upload_res.json())

if upload_res.status_code == 200:
    print("\nAsking question...")
    ask_req = {
        "question": "What is this document about?",
        "session_id": session_id
    }
    with requests.post(f"{API_URL}/ask_stream", json=ask_req, stream=True) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if line:
                data = json.loads(line)
                if "chunk" in data:
                    sys.stdout.write(data["chunk"])
                    sys.stdout.flush()
                if "sources" in data:
                    print("\n\nSources:")
                    for s in data["sources"]:
                        print(f" - {s}")
