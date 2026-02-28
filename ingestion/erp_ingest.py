import requests

def ingest_erp(api_url):
    response = requests.get(api_url)
    return response.json()