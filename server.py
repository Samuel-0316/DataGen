'''from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import PyPDF2
import docx
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import spacy
nlp = spacy.load("en_core_web_sm")

app = Flask(__name__, static_folder="static", template_folder="templates")  # Specify static and template folders
CORS(app)

Global_data = ""

# PDF, DOCX, and TXT File Extraction Functions
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            pdf_text += page.extract_text() or ""
        return pdf_text
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        doc_text = "\n".join([para.text for para in doc.paragraphs])
        return doc_text
    except Exception as e:
        return f"Error reading DOCX: {e}"

def extract_text_from_txt(file):
    try:
        return file.read().decode('utf-8')
    except Exception as e:
        return f"Error reading TXT: {e}"

# Serve the frontend page
@app.route('/')
def index():
    return render_template('index.html')  # Main HTML page for the frontend

@app.route('/terminal')
def terminal():
    return render_template('terminal.html')  # Serve the terminal.html page


# Endpoint for PDF, DOCX, and TXT Upload
@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension == '.pdf':
        Global_data = extract_text_from_pdf(file)
    elif file_extension == '.docx':
        Global_data = extract_text_from_docx(file)
    elif file_extension == '.txt':
        Global_data = extract_text_from_txt(file)
    else:
        return jsonify({"error": "Unsupported file format"}), 400

    if Global_data.startswith("Error"):
        return jsonify({"error": Global_data}), 500
    
    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0,len(sentences),chunk_size)]
    for i,chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")

    return jsonify({"text": Global_data}), 200
# -----------------------------------------------------------------------------------------------
# Webpage Extraction and Crawling Functions
def extract_data_from_webpage(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)

        links = []
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            if is_valid_url(full_url):
                links.append(full_url)

        return text_content, links
    except requests.exceptions.RequestException as e:
        return None, []

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.scheme in ['http', 'https'])

def crawl_website(start_url, max_pages=50):
    visited = set()
    to_visit = [start_url]
    crawled_content = ""

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        text_content, links = extract_data_from_webpage(current_url)
        if text_content:
            crawled_content += text_content + "\n\n"

        for link in links:
            if link not in visited and link not in to_visit:
                to_visit.append(link)

        visited.add(current_url)

    return crawled_content

@app.route('/extract_webpage', methods=['POST'])
def extract_webpage():
    data = request.json
    url = data.get('url')

    if not url or not is_valid_url(url):
        return jsonify({"error": "Valid URL is required"}), 400

    Global_data, links = extract_data_from_webpage(url)
    if Global_data is None:
        return jsonify({"error": "Unable to retrieve webpage content"}), 500
    
    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0,len(sentences),chunk_size)]
    for i,chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")

    return jsonify({"text_content": Global_data, "links": links}), 200


@app.route('/crawl_webpage', methods=['POST'])
def crawl_webpage():
    data = request.json
    start_url = data.get('url')
    max_pages = int(data.get('max_pages', 50))  # Ensure max_pages is an integer

    if not start_url or not is_valid_url(start_url):
        return jsonify({"error": "Valid URL is required"}), 400

    Global_data = crawl_website(start_url, max_pages)
    
    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0,len(sentences),chunk_size)]
    for i,chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")

    return jsonify({"crawled_content": Global_data}), 200

# Error handler for 404
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Resource not found"}), 404

# Error handler for 500
@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)'''
    
# Required imports and configurations
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import PyPDF2
import docx
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import spacy
nlp = spacy.load("en_core_web_sm")

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

Global_data = ""

# PDF, DOCX, and TXT File Extraction Functions
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            pdf_text += page.extract_text() or ""
        return pdf_text
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        doc_text = "\n".join([para.text for para in doc.paragraphs])
        return doc_text
    except Exception as e:
        return f"Error reading DOCX: {e}"

def extract_text_from_txt(file):
    try:
        return file.read().decode('utf-8')
    except Exception as e:
        return f"Error reading TXT: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/terminal')
def terminal():
    return render_template('terminal.html')

# Function to send chunk to model for processing
def send_chunk_to_model(chunk):
    try:
        response = requests.post(
            "http://10.20.45.196:5001/process_chunk",
            json={"chunk": chunk},
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error communicating with model: {e}"}

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension == '.pdf':
        Global_data = extract_text_from_pdf(file)
    elif file_extension == '.docx':
        Global_data = extract_text_from_docx(file)
    elif file_extension == '.txt':
        Global_data = extract_text_from_txt(file)
    else:
        return jsonify({"error": "Unsupported file format"}), 400

    if Global_data.startswith("Error"):
        return jsonify({"error": Global_data}), 500

    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    responses = []

    for i, chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")
        response = send_chunk_to_model(chunk)
        responses.append(response)

    return jsonify({"text": Global_data, "model_responses": responses}), 200

def extract_data_from_webpage(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)

        links = []
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            if is_valid_url(full_url):
                links.append(full_url)

        return text_content, links
    except requests.exceptions.RequestException as e:
        return None, []

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.scheme in ['http', 'https'])

def crawl_website(start_url, max_pages=50):
    visited = set()
    to_visit = [start_url]
    crawled_content = ""

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        text_content, links = extract_data_from_webpage(current_url)
        if text_content:
            crawled_content += text_content + "\n\n"

        for link in links:
            if link not in visited and link not in to_visit:
                to_visit.append(link)

        visited.add(current_url)

    return crawled_content

@app.route('/extract_webpage', methods=['POST'])
def extract_webpage():
    data = request.json
    url = data.get('url')

    if not url or not is_valid_url(url):
        return jsonify({"error": "Valid URL is required"}), 400

    Global_data, links = extract_data_from_webpage(url)
    if Global_data is None:
        return jsonify({"error": "Unable to retrieve webpage content"}), 500
    
    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    responses = []

    for i, chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")
        response = send_chunk_to_model(chunk)
        responses.append(response)

    return jsonify({"text_content": Global_data, "links": links, "model_responses": responses}), 200

@app.route('/crawl_webpage', methods=['POST'])
def crawl_webpage():
    data = request.json
    start_url = data.get('url')
    max_pages = int(data.get('max_pages', 50))

    if not start_url or not is_valid_url(start_url):
        return jsonify({"error": "Valid URL is required"}), 400

    Global_data = crawl_website(start_url, max_pages)
    
    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    responses = []

    for i, chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")
        response = send_chunk_to_model(chunk)
        responses.append(response)

    return jsonify({"crawled_content": Global_data, "model_responses": responses}), 200

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)