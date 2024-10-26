from mlx_lm import load, generate
import pandas as pd

# Load the model and tokenizer outside the loop
model, tokenizer = load("mlx-community/quantized-gemma-2b-it")

def generate_question_answer(paragraph):
    # Create a prompt to generate a question-answer pair based on the paragraph
    prompt = f"Generate a question and answer pair in CSV format with the columns 'question' and 'answer' based on the following paragraph: '{paragraph}'"
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