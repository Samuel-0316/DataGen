from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import docx
import os

app = Flask(__name__)
CORS(app)

def extract_text_from_pdf(file):
    """Extract text from a PDF file."""
    pdf_reader = PyPDF2.PdfReader(file)
    pdf_text = ""
    for page_num, page in enumerate(pdf_reader.pages):
        pdf_text += page.extract_text() or ""
    return pdf_text

def extract_text_from_docx(file):
    """Extract text from a DOCX file."""
    doc = docx.Document(file)
    doc_text = "\n".join([para.text for para in doc.paragraphs])
    return doc_text

def extract_text_from_txt(file):
    """Extract text from a TXT file."""
    return file.read().decode('utf-8')  # Decoding the file content as it's binary.

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['pdf']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Determine the file extension
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension == '.pdf':
        # Read PDF
        text = extract_text_from_pdf(file)
    elif file_extension == '.docx':
        # Read DOCX
        text = extract_text_from_docx(file)
    elif file_extension == '.txt':
        # Read TXT
        text = extract_text_from_txt(file)
    else:
        return jsonify({"error": "Unsupported file format"}), 400

    # Print to the terminal
    print(f"File content from {file.filename}:\n", text)

    return jsonify({"message": "File received and printed to terminal"}), 200

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)