# Required imports and configurations
import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import PyPDF2
import docx
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from textblob import TextBlob
import cohere
import nltk
nltk.data.path.append(os.path.join(os.path.dirname(__file__), "nltk_data"))

# Initialize the Cohere client
cohere_api_key = "PqaHJXfKE4ZOJx9plxcRk0xirubw8bGjFq17Y35N"
co = cohere.Client(cohere_api_key)

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Add CORS headers to all responses to handle cross-origin requests
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

Global_data = ""
process_log = []  # To store function call logs
qa_pairs_json = "[]"

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

def generate_response(prompt, max_tokens):
    """
    Generates a response using the Cohere API.
    """
    try:
        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.generations[0].text.strip()
    except Exception as e:
        print("Error:", e)
        return None

# Function to send chunk to Cohere for processing
def send_chunk_to_LLM(chunk):
    global qa_pairs_json

    prompt = (
        f"You are an AI assistant that generates question-answer pairs based on the content provided. "
        "Generate as many question-answer pairs as possible from the given content. "
        "The answers should be descriptive but not excessively long, providing clear and concise explanations. "
        "Respond only in JSON format, strictly in the following structure: "
        "[{'question': 'Your question?', 'answer': 'A descriptive yet concise answer.'}, ...]. "
        "Do not include any text outside the JSON. "
        f"\n\nContent: {chunk}"
    )

    max_retries = 5
    backoff_factor = 2

    for retry_count in range(max_retries):
        try:
            # Send the prompt to the API
            content = generate_response(prompt, max_tokens=1000)
            print("Raw content from Cohere API:", content)

            # Validate and fix JSON if needed
            try:
                # Try to parse the content as JSON
                new_qa_pairs = json.loads(content)
            except json.JSONDecodeError:
                # Attempt to fix common issues (e.g., unclosed strings)
                print("Malformed JSON detected. Attempting to fix...")
                fixed_content = content.strip().rstrip(",}") + "}"
                try:
                    new_qa_pairs = json.loads(fixed_content)
                except json.JSONDecodeError:
                    raise ValueError("Failed to parse JSON after attempting to fix.")

            # Merge with existing QA pairs
            existing_qa_pairs = json.loads(qa_pairs_json) if qa_pairs_json != "[]" else []
            existing_qa_pairs.extend(new_qa_pairs)

            # Update the global QA pairs JSON
            qa_pairs_json = json.dumps(existing_qa_pairs, indent=2)
            return qa_pairs_json

        except Exception as e:
            print(f"Error: {e}")
            if retry_count < max_retries - 1:
                wait_time = backoff_factor ** (retry_count + 1)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                qa_pairs_json = json.dumps({"error": f"Error communicating with LLM: {e}"})
                return qa_pairs_json

    qa_pairs_json = json.dumps({"error": "Unable to generate a response. Please try again later."})
    return qa_pairs_json

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
    # Create a TextBlob object
    blob = TextBlob(Global_data)
    # Split text into sentences (chunks)
    sentences = blob.sentences
    # Define chunk size (number of sentences per chunk)
    chunk_size = 5
    # Create chunks by grouping sentences into chunks of specified size
    chunks = [' '.join(str(sentence) for sentence in sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    print(chunks)
    print("\n")
    print(len(chunks))
    responses = []
    log_function_call("NLP_processing", "Completed")

    log_function_call("sending_chunk_to_LLM", "Started")
    for i, chunk in enumerate(chunks, start=1):
        print(f"Chunk {i}: {chunk}")
        response = send_chunk_to_LLM(chunk)
        responses.append(response)
        time.sleep(10)
    log_function_call("sending_chunk_to_LLM", "Completed")

    log_function_call("Successfully sent all chunks to LLM", "Completed")

    return jsonify({"text": Global_data, "chunks": chunks, "model_responses": responses}), 200

# The rest of the code remains the same as provided.

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

    # Create a TextBlob object
    blob = TextBlob(Global_data)
    # Split text into sentences (chunks)
    sentences = blob.sentences
    # Define chunk size (number of sentences per chunk)
    chunk_size = 5
    # Create chunks by grouping sentences into chunks of specified size
    chunks = [' '.join(str(sentence) for sentence in sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    responses = []
    log_function_call("NLP_processing", "Completed")


    log_function_call("sending_chunk_to_LLM", "Started")
    for i, chunk in enumerate(chunks, start=1):
        print(f"Chunk {i}: {chunk}")
        response = send_chunk_to_LLM(chunk)
        responses.append(response)
        time.sleep(10)
    log_function_call("sending_chunk_to_LLM", "Completed")

    log_function_call("Successfully sent all chunks to LLM", "Completed")

    return jsonify({"text_content": Global_data, "model_responses": responses}), 200

@app.route('/crawl_webpage', methods=['POST'])
def crawl_webpage():
    log_function_call("crawl_webpage", "Started")

    try:
        # Retrieve URL and max_pages from request data
        data = request.json
        start_url = data.get('url')
        max_pages = int(data.get('max_pages', 50))

        # Check if URL is provided and valid
        if not start_url or not is_valid_url(start_url):
            log_function_call("crawl_webpage", "Error: Invalid URL")
            return jsonify({"error": "Valid URL is required"}), 200  # Return 200 with error info

        # Global variable to store crawled data
        global Global_data
        Global_data, crawled_links = crawl_website(start_url, max_pages)
        
        log_function_call("crawl_webpage", "Crawling Completed", data={"crawled_links": crawled_links})

        # Process text with NLP and split into chunks
        log_function_call("NLP_processing", "Started")
        
        blob = TextBlob(Global_data)
        sentences = blob.sentences
        chunk_size = 5
        chunks = [' '.join(str(sentence) for sentence in sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
        
        responses = []
        log_function_call("NLP_processing", "Completed")

        # Send each chunk to the language model
        log_function_call("sending_chunk_to_LLM", "Started")
        for i, chunk in enumerate(chunks, start=1):
            print(f"Chunk {i}: {chunk}")
            response = send_chunk_to_LLM(chunk)
            responses.append(response)
            time.sleep(10)  # Add a delay if necessary
        log_function_call("sending_chunk_to_LLM", "Completed")

        log_function_call("crawl_webpage", "Successfully sent all chunks to LLM", "Completed")

        # Return the success response with crawled and processed data
        return jsonify({"crawled_content": Global_data, "crawled_links": crawled_links, "model_responses": responses}), 200

    except Exception as e:
        # Handle any exception, log the error, print it, and return a 200 response with error details
        log_function_call("crawl_webpage", f"Error: {e}")
        print(f"Error occurred in /crawl_webpage: {e}")
        return jsonify({
            "error": "An error occurred while processing the request.",
            "details": str(e)
        }), 200  # Custom error message, but with 200 status code

# Endpoint to retrieve log data
@app.route('/get_process_log', methods=['GET'])
def get_process_log():
    log_data = jsonify(process_log)  # Save the log data to be returned
    process_log.clear()  # Clear the log after saving it
    return log_data, 200

# Add a new route to get the QA pairs JSON
@app.route('/get_qa_pairs', methods=['GET'])
def get_qa_pairs():
    global qa_pairs_json
    return jsonify({"qa_pairs": qa_pairs_json}), 200

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)