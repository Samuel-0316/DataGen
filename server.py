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
# import spacy
import openai
import json
from textblob import TextBlob

# Initialize Spacy NLP model and OpenAI API
# nlp = spacy.load("en_core_web_sm")
openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure your API key is set in environment variables

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

Global_data = ""
process_log = []  # To store function call logs
qa_pairs_json = ""

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

# Function to send chunk to Azure OpenAI for processing
def send_chunk_to_LLM(chunk):
    global qa_pairs_json  # Specify that we are using the global variable

    # Replace with your actual Azure OpenAI API key and endpoint
    API_KEY = "ca4f7fa7152749218fa8462c3a60aeea"
    ENDPOINT = "https://khazi18gpt.openai.azure.com/openai/deployments/Khazi18GPT/chat/completions?api-version=2024-02-15-preview"

    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    }

    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant that generates question-answer pairs in JSON format only. "
                    "Each answer should be a single word. Generate no more than 5 questions and answers "
                    "based on the provided content. Respond in JSON format without any additional text. "
                    "Format the output as [{'question': 'Your question?', 'answer': 'Answer'}]."
                )
            },
            {
                "role": "user",
                "content": f"Generate questions and answers in JSON format for this text: {chunk}"
            }
        ],
        "temperature": 0.5,
        "top_p": 0.9,
        "max_tokens": 150
    }

    retry_count = 0
    max_retries = 5  # Number of retries
    backoff_factor = 2  # Exponential backoff factor

    while retry_count < max_retries:
        try:
            response = requests.post(ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]
            print(content)

            # Load the new response content into a list
            try:
                new_qa_pairs = json.loads(content)
            except json.JSONDecodeError:
                print("Error: Could not parse the output as JSON.")
                return "[]"

            # Load existing data from qa_pairs_json if present, else initialize with an empty list
            existing_qa_pairs = json.loads(qa_pairs_json) if qa_pairs_json else []

            # Append the new data
            existing_qa_pairs.extend(new_qa_pairs)

            # Update the global variable with the combined data
            qa_pairs_json = json.dumps(existing_qa_pairs)

            return qa_pairs_json

        except requests.RequestException as e:
            if response.status_code == 429:  # Too Many Requests
                retry_count += 1
                wait_time = backoff_factor ** retry_count
                print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                log_function_call("send_chunk_to_LLM", f"Error: {e}")
                qa_pairs_json = json.dumps({"error": f"Error communicating with LLM: {e}"})
                return qa_pairs_json

    # If retries are exhausted, return an error message
    qa_pairs_json = json.dumps({"error": "Rate limit exceeded. Please try again later."})
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
    """
    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    """
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
    """
    for i, chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")
        response = send_chunk_to_LLM(chunk)
        responses.append(response)
        time.sleep(20)
    """
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
    """
    doc = nlp(Global_data)
    sentences = [sent.text for sent in doc.sents]
    chunk_size = 4
    chunks = [''.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    """
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
    """
    for i, chunk in enumerate(chunks):
        print(f"Chunk{i+1}:\n{chunk}\n")
        response = send_chunk_to_LLM(chunk)
        responses.append(response)
        time.sleep(20)
    """
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
    app.run(host="127.0.0.1", port=5000, debug=True)
