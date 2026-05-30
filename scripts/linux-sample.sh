mkdir ./output

# Option A: Create a simple text file, then convert to PDF (if you have `enscript` or `pandoc`)
echo "This is a test document about RAG systems and AI assistants." > ./output/sample.txt
# Use any method to convert to PDF, or just download a sample PDF:

# Option B: Download a real sample PDF from the web
curl -L -o ./output/sample.pdf "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

# Option C: Use a known local PDF if you have one
# Then retry the upload
curl -X POST http://localhost:8000/upload/test_session -F "file=@./output/sample.pdf"
