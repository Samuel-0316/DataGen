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

process_log = []  # To store function call logs

# Log function calls for dynamic frontend display
def log_function_call(func_name, status="Started", data=None):
    entry = {"function": func_name, "status": status}
    if data:
        entry["data"] = data  # Include data in the log if provided
    process_log.append(entry)

# PDF, DOCX, and TXT File Extraction Functions
def extract_text_from_pdf(file):
    log_function_call("extract_text_from_pdf")
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            pdf_text += page.extract_text() or ""
        log_function_call("extract_text_from_pdf", "Completed")
        return pdf_text
    except Exception as e:
        log_function_call("extract_text_from_pdf", f"Error: {e}")
        return f"Error reading PDF: {e}"

def extract_text_from_docx(file):
    log_function_call("extract_text_from_docx")
    try:
        doc = docx.Document(file)
        doc_text = "\n".join([para.text for para in doc.paragraphs])
        log_function_call("extract_text_from_docx", "Completed")
        return doc_text
    except Exception as e:
        log_function_call("extract_text_from_docx", f"Error: {e}")
        return f"Error reading DOCX: {e}"

def extract_text_from_txt(file):
    log_function_call("extract_text_from_txt")
    try:
        text = file.read().decode('utf-8')
        log_function_call("extract_text_from_txt", "Completed")
        return text
    except Exception as e:
        log_function_call("extract_text_from_txt", f"Error: {e}")
        return f"Error reading TXT: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process')
def process():
    return render_template('process.html')

# Function to send chunk to model for processing
def send_chunk_to_model(chunk):
    log_function_call("send_chunk_to_model")
    try:
        response = requests.post(
            "http://10.20.31.198:5001/process_chunk",
            json={"chunk": chunk},
            headers={"Content-Type": "application/json"}
        )
        # log_function_call("send_chunk_to_model", "Completed")
        return response.json()
    except requests.exceptions.RequestException as e:
        log_function_call("send_chunk_to_model", f"Error: {e}")
        return {"error": f"Error communicating with model: {e}"}

@app.route('/upload_file', methods=['POST'])                                                 
def upload_file():
    if 'file' not in request.files:
        log_function_call("upload_file", "Error: No file part")
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']

    if file.filename == '':
        log_function_call("upload_file", "Error: No selected file")
        return jsonify({"error": "No selected file"}), 400

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension == '.pdf':
        Global_data = extract_text_from_pdf(file)
    elif file_extension == '.docx':
        Global_data = extract_text_from_docx(file)
    elif file_extension == '.txt':
        Global_data = extract_text_from_txt(file)
    else:
        log_function_call("upload_file", "Error: Unsupported file format")
        return jsonify({"error": "Unsupported file format"}), 400

    if Global_data.startswith("Error"):
        log_function_call("upload_file", f"Error in text extraction")
        return jsonify({"error": Global_data}), 500

    log_function_call("NLP_processing", "Started")
    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    responses = []
    log_function_call("NLP_processing", "Completed")

    for i, chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")
        response = send_chunk_to_model(chunk)
        responses.append(response)

    log_function_call("Successfully sent all chunks to model", "Completed")

    return jsonify({"text": Global_data, "chunks": chunks, "model_responses": responses}), 200

#----------------------------------------------------------------------

# Webpage and Website Crawling Functions
def extract_data_from_webpage(url):
    log_function_call("extract_data_from_webpage")
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        links = [urljoin(url, link['href']) for link in soup.find_all('a', href=True) if is_valid_url(urljoin(url, link['href']))]
        log_function_call("extract_data_from_webpage", "Completed")
        return text_content, links
    except requests.exceptions.RequestException as e:
        log_function_call("extract_data_from_webpage", f"Error: {e}")
        return None, []

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.scheme in ['http', 'https'])

def crawl_website(start_url, max_pages=50):
    log_function_call("crawl_website")
    visited = set()
    to_visit = [start_url]
    crawled_content = ""
    crawled_links = []

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
        crawled_links.append(current_url)

    log_function_call("crawl_website", "Completed")
    return crawled_content, crawled_links

@app.route('/extract_webpage', methods=['POST'])
def extract_webpage():
    data = request.json
    url = data.get('url')

    if not url or not is_valid_url(url):
        return jsonify({"error": "Valid URL is required"}), 400

    Global_data, links = extract_data_from_webpage(url)
    if Global_data is None:
        return jsonify({"error": "Unable to retrieve webpage content"}), 500
    
    log_function_call("NLP_processing", "Started")
    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    responses = []
    log_function_call("NLP_processing", "Completed")

    for i, chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")
        response = send_chunk_to_model(chunk)
        responses.append(response)

    log_function_call("Successfully sent all chunks to model", "Completed")

    return jsonify({"text_content": Global_data, "model_responses": responses}), 200

@app.route('/crawl_webpage', methods=['POST'])
def crawl_webpage():
    data = request.json
    start_url = data.get('url')
    max_pages = int(data.get('max_pages', 50))

    if not start_url or not is_valid_url(start_url):
        return jsonify({"error": "Valid URL is required"}), 400

    # Crawl the website and get crawled content and links
    Global_data, crawled_links = crawl_website(start_url, max_pages)

    # Log the crawled links
    log_function_call("crawl_webpage", "Crawling Completed", data={"crawled_links": crawled_links})

    log_function_call("NLP_processing", "Started")
    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    responses = []
    log_function_call("NLP_processing", "Completed")

    for i, chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")
        response = send_chunk_to_model(chunk)
        responses.append(response)

    log_function_call("Successfully sent all chunks to model", "Completed")

    return jsonify({"crawled_content": Global_data, "crawled_links": crawled_links, "model_responses": responses}), 200

# Endpoint to retrieve log data
@app.route('/get_process_log', methods=['GET'])
def get_process_log():
    log_data = jsonify(process_log)  # Save the log data to be returned
    process_log.clear()  # Clear the log after saving it
    return log_data, 200

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
