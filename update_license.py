import json
import os
import requests

# Use Kaggle API v1 directly
token = os.environ.get('KAGGLE_API_TOKEN', '')
if token.startswith('KGAT_'):
    headers = {'Authorization': f'Bearer {token}'}
else:
    # parse as user:key
    import base64
    headers = {'Authorization': f'Basic {base64.b64encode(token.encode()).decode()}'}

with open('output/dataset-metadata.json') as f:
    meta = json.load(f)

payload = {
    'title': meta['title'],
    'subtitle': meta.get('subtitle', ''),
    'description': meta.get('description', ''),
    'isPrivate': meta.get('isPrivate', False),
    'licenses': meta.get('licenses', []),
    'keywords': meta.get('keywords', []),
}

resp = requests.post(
    'https://www.kaggle.com/api/v1/datasets/bdelanghe/tmdb-movie-vad-emotion-scores',
    json=payload,
    headers=headers
)
print(resp.status_code, resp.text[:500])
