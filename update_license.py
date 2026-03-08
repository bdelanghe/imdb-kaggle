import json
import kagglehub.gcs_upload as gcs
from kagglehub.kaggle_api_extended import KaggleApiExtended

api = KaggleApiExtended()
api.authenticate()

with open('output/dataset-metadata.json') as f:
    meta = json.load(f)

# Use kaggle CLI to update metadata
import subprocess, os

env = os.environ.copy()
result = subprocess.run(
    ['kaggle', 'datasets', 'metadata', '-p', 'output'],
    capture_output=True, text=True, env=env
)
print("metadata:", result.stdout, result.stderr)
