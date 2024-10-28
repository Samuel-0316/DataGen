'''from mlx_lm import load, generate
import pandas as pd

# Load the model and tokenizer outside the loop
model, tokenizer = load("mlx-community/quantized-gemma-2b-it")

def generate_question_answer(paragraph):
    # Create a prompt to generate a question-answer pair based on the paragraph
    prompt = f"generate question and answer as formatted like ques= , ans= for this paragraph: '{paragraph}'"
    response = generate(model, tokenizer, prompt=prompt, verbose=True, max_tokens=100)
    return response.strip()

# Dummy paragraph input
paragraph = "The mitochondria is the powerhouse of the cell. It provides energy for various cellular functions by generating ATP through cellular respiration."

# Generate the question and answer
response_text = generate_question_answer(paragraph)

# Split the generated response into question and answer parts
# Assuming the response follows the format "question: ... answer: ..."
if "answer:" in response_text:
    question, answer = response_text.split("answer:", 1)
    question = question.replace("question:", "").strip()
    answer = answer.strip()
else:
    print("The response format was unexpected.")
    question, answer = response_text, ""

# Prepare data for CSV
data = [{"question": question, "answer": answer}]
df = pd.DataFrame(data)

# Save to CSV (append mode to not overwrite previous data)
csv_file = "questions_answers.csv"
df.to_csv(csv_file, index=False, mode='a', header=not pd.io.common.file_exists(csv_file))

print(f"Question-Answer pair saved to {csv_file}:\nQuestion: {question}\nAnswer: {answer}")

'''


'''
from mlx_lm import load, generate
import pandas as pd
import os
import re

# Load the model and tokenizer outside the loop
model, tokenizer = load("mlx-community/quantized-gemma-2b-it")

def generate_question_answer(paragraph):
    # Create a prompt to generate a question-answer pair based on the paragraph
    prompt = f"generate question and answer as formatted like ques= , ans= for this paragraph: '{paragraph}'"
    response = generate(model, tokenizer, prompt=prompt, verbose=True, max_tokens=100)
    return response.strip()

# Dummy paragraph input
paragraph = "Java persistence using Hibernate refers to the mechanism of managing and interacting with a relational database in Java applications using the Hibernate ORM (Object-Relational Mapping) framework. Hibernate simplifies database operations by automatically mapping Java classes to database tables, and it allows developers to work with Java objects rather than SQL statements."

# Generate the question and answer
response_text = generate_question_answer(paragraph)

# Use regular expressions to extract question and answer parts without prefixes
# This pattern captures text after "Ques:" or "question:" as the question
# and text after "Ans:" or "answer:" as the answer.
question_match = re.search(r"(?:Ques:|question:)\s*(.*?)(?=\s*(?:Ans:|answer:|$))", response_text, re.IGNORECASE)
answer_match = re.search(r"(?:Ans:|answer:)\s*(.*)", response_text, re.IGNORECASE)

# Extract matched question and answer, or assign empty strings if not found
question = question_match.group(1).strip() if question_match else ""
answer = answer_match.group(1).strip() if answer_match else ""

# Prepare data for CSV
data = [{"question": question, "answer": answer}]
df = pd.DataFrame(data)

# Save to CSV (append mode to avoid overwriting previous data)
csv_file = "questions_answers.csv"
df.to_csv(csv_file, index=False, mode='a', header=not os.path.exists(csv_file))

print(f"Question-Answer pair saved to {csv_file}:\nQuestion: {question}\nAnswer: {answer}")'''

# model.py
from flask import Flask, request, jsonify
import pandas as pd
import os
import re
from mlx_lm import load, generate

app = Flask(__name__)

# Load the model and tokenizer outside the loop
model, tokenizer = load("mlx-community/quantized-gemma-2b-it")

# Generate Q&A from a given paragraph
def generate_question_answer(paragraph):
    prompt = f"generate question and answer as formatted like ques= , ans= for this paragraph: '{paragraph}'"
    response = generate(model, tokenizer, prompt=prompt, verbose=True, max_tokens=100)
    return response.strip()

# Process each chunk and append to CSV
@app.route('/process_chunk', methods=['POST'])
def process_chunk():
    data = request.json
    chunk = data.get('chunk', '')

    # Generate Q&A pair
    response_text = generate_question_answer(chunk)
    question_match = re.search(r"(?:Ques:|question:)\s*(.*?)(?=\s*(?:Ans:|answer:|$))", response_text, re.IGNORECASE)
    answer_match = re.search(r"(?:Ans:|answer:)\s*(.*)", response_text, re.IGNORECASE)

    question = question_match.group(1).strip() if question_match else ""
    answer = answer_match.group(1).strip() if answer_match else ""

    # Append data to CSV
    data = [{"question": question, "answer": answer}]
    df = pd.DataFrame(data)
    csv_file = "questions_answers.csv"
    df.to_csv(csv_file, index=False, mode='a', header=not os.path.exists(csv_file))

    return jsonify({"message": "Chunk processed", "question": question, "answer": answer}), 200

if __name__ == '__main__':
    app.run(port=5001)