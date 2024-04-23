import requests
from bs4 import BeautifulSoup
import pandas as pd

# Fetch and parse the HTML content of a URL
def get_html_content(url):
    try:
        response = requests.get(url, timeout=5)  # Added timeout for safety
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error: Received status code {response.status_code}")
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return ""

# Extract HTML and JavaScript features
def extract_features(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    features = {
        'presence_iFrame': bool(soup.find('iframe')),
        'count_eval': html_content.count('eval('),
        'count_escape': html_content.count('escape('),
        'count_unescape': html_content.count('unescape('),
        'count_find': html_content.count('find('),
        'count_exec': html_content.count('exec('),
        'count_search': html_content.count('search('),
        'count_link': html_content.count('link('),
        'presence_windows_open': 'window.open(' in html_content,
        'lines_count': html_content.count('\n')
    }
    features['count_all_functions'] = sum(features[f'count_{func}'] for func in ['eval', 'escape', 'unescape', 'find', 'exec', 'search', 'link'])
    return features

# Interactive function to check a new URL
def check_url():
    url = input("Enter a URL to check: ")
    html_content = get_html_content(url)
    if html_content:
        features = extract_features(html_content)
        print("\nExtracted Features:")
        for key, value in features.items():
            print(f"{key}: {value}")
    else:
        print("Failed to retrieve or parse URL content.")

if __name__ == '__main__':
    check_url()




