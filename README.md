# DataGen

DataGen is a user-friendly web interface designed to facilitate the creation of ready-to-use datasets for training machine learning models. It supports custom file inputs and offers additional functionality for web crawling and dataset generation. 

## Key Features

- **Custom File Input Support**: Users can upload files in various formats, and DataGen will process and generate structured datasets ready for model training.
- **Web Crawling for Dataset Generation**: 
   - DataGen enables web crawling for dataset generation, specifically targeting question and answer content on custom websites.
   - The web crawler is optimized for high accuracy, gathering only the most relevant, filtered question-and-answer pairs.

## Objective

The main purpose of DataGen is to provide a streamlined tool for creating high-quality, structured datasets that can be directly used to train machine learning models. The application supports:

- **High-Accuracy Dataset Generation**: Processes custom website content or uploaded files to ensure only relevant data is collected.
- **Flexible Output Options**: Generates datasets compatible with machine learning requirements, making it easier for users to immediately utilize data in model training workflows.

## Use Cases

DataGen can be applied in scenarios where curated question-and-answer datasets are required, including but not limited to:

- Chatbot training
- Question-answering models
- FAQ generation for customer service applications

---

Developed with an intuitive interface, DataGen allows users to easily collect and prepare datasets with minimal technical setup, making it accessible to both novice and expert data scientists.

---

# DataGen App Dockerized
## Prerequisites
Before you begin, make sure you have the following installed:

-> Docker: Ensure Docker Desktop is installed and running on your machine.

## Clone the Repository
To clone this repository to your local machine, run the following command:<br>
```git clone https://github.com/yourusername/datagen.git```<br>
```cd datagen```

## Building the Docker Image
Once you have cloned the repository, you can build the Docker image. This step will install all dependencies listed in requirements.txt inside a container.<br>

Open a terminal and navigate to the project directory.<br>
Run the following command to build the Docker image:<be>
```docker build -t datagen .```<be>

## Running the Application
To run the Dockerized Flask app, execute the following command:<br>
```docker run -p 5000:5000 datagen```<br>

Once the container starts, you can open your browser and navigate to:<br>
```http://localhost:5000```<br>

## Stopping the Application
If you want to stop the running Docker container, first, find the container ID:<br>
```docker ps```<br>

# Contributing
If you would like to contribute to this project, please follow these steps:<br>

-> Fork the repository.<br>
-> Clone your fork and create a new branch.<br>
-> Make your changes and test them.<br>
-> Open a pull request to the main repository.<br>


**Note**: DataGen supports the generation of datasets from a combination of sources, including both files and website content, ensuring flexibility and comprehensiveness in data gathering.

# License
This project is licensed under the MIT License - see the LICENSE file for details.
