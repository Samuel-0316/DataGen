from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Dummy data
data = [
    {"name": "Alice", "age": 30, "city": "New York"},
    {"name": "Bob", "age": 25, "city": "Los Angeles"},
    {"name": "Charlie", "age": 35, "city": "Chicago"}
]

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(data)

@app.route('/get_process_log', methods=['GET'])
def get_process_log():
    return jsonify({"message": "This is a dummy log response."})

if __name__ == '__main__':
    app.run(debug=True)
    
#Dummy Flask app for Downloading CSV