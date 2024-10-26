from flask import Flask, render_template, request
from mlx_lm import load, generate
import pandas as pd

app = Flask(__name__)

# Load the model and tokenizer outside the loop
model, tokenizer = load("mlx-community/quantized-gemma-2b-it")

def generate_question(paragraph):
    # Create a prompt to generate a question based on the paragraph
    prompt = f"Generate a question for the following paragraph: '{paragraph}'"
    response = generate(model, tokenizer, prompt=prompt, verbose=True, max_tokens=100)
    return response.strip()  # Strip to clean up the response

@app.route('/', methods=['GET', 'POST'])
def index():
    generated_question = ""
    if request.method == 'POST':
        input_text = request.form['input_text']  # User-provided answer
        generated_question = generate_question(input_text)  # Generate a question based on the input

        # Prepare data for CSV
        data = [{"question": generated_question, "answer": input_text}]
        df = pd.DataFrame(data)

        # Save to CSV (append mode to not overwrite previous data)
        df.to_csv("questions_answers.csv", index=False, mode='a', header=not pd.io.common.file_exists("questions_answers.csv"))

    return render_template('indi.html', generated_question=generated_question)

if __name__ == '__main__':
    app.run(debug=True)