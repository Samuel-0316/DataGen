#!/bin/bash

# Check if the model directory already exists to avoid redundant downloads
if [ ! -d "./spacy_model" ]; then
  echo "Downloading spaCy model..."
  python -m spacy download en_core_web_sm -d ./spacy_model
fi
