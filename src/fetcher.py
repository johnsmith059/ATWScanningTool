import requests

def get_html(url):
    """Fetch HTML content from URL"""
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text
