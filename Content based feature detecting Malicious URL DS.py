import pandas as pd
import numpy as np
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report

def is_valid_url(url):
    """ Check if the URL contains a scheme, if not, it is likely a relative URL. """
    parsed_url = urlparse(url)
    return bool(parsed_url.scheme)

def get_links_from_webpage(url):
    """ Fetch and extract absolute links from the given webpage. """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return [urljoin(url, tag['href']) for tag in soup.find_all('a', href=True) if is_valid_url(urljoin(url, tag['href']))]
    except requests.RequestException as e:
        print(f"Error fetching webpage: {e}")
        return []

def get_html_content(url):
    """ Fetch the HTML content from the given URL if it's valid. """
    if not is_valid_url(url):
        print(f"Invalid URL detected: {url}")
        return ""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching webpage content: {e}")
        return ""

def extract_content_features(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    features = {
        'presence_iframe': int(bool(soup.find('iframe'))),
        'count_eval': sum(1 for script in soup.find_all('script') if 'eval(' in script.text),
        'count_escape': sum(1 for script in soup.find_all('script') if 'escape(' in script.text),
        'count_unescape': sum(1 for script in soup.find_all('script') if 'unescape(' in script.text),
        'count_find': sum(1 for script in soup.find_all('script') if 'find(' in script.text),
        'count_exec': sum(1 for script in soup.find_all('script') if 'exec(' in script.text),
        'count_search': sum(1 for script in soup.find_all('script') if 'search(' in script.text),
        'count_link': sum(1 for script in soup.find_all('script') if 'link(' in script.text),
        'count_all_functions': sum(1 for script in soup.find_all('script') if any(func in script.text for func in ['eval(', 'escape(', 'unescape(', 'find(', 'exec(', 'search(', 'link('])),
        'presence_windows_open': int(bool(sum(1 for script in soup.find_all('script') if 'window.open(' in script.text))),
        'lines_count': sum(len(script.text.splitlines()) for script in soup.find_all('script'))
    }
    return list(features.values())

def tokenizer(url):
    tokens = re.split('[/:?=&]', url)
    tokens = filter(lambda token: token.strip() != '', tokens)
    enhanced_tokens = []
    for token in tokens:
        subtokens = re.split('[.-@]', token)
        enhanced_tokens.extend([sub for sub in subtokens if sub not in ['com', 'www', 'http', 'https']])
    return enhanced_tokens

def vectorize_data(data_frame, vectorizer, content_features, fit=False):
    if fit:
        X = vectorizer.fit_transform(data_frame['URLs'])
    else:
        X = vectorizer.transform(data_frame['URLs'])
    X = np.hstack([X.toarray(), content_features])
    return X

def train_model(data_frame):
    vectorizer = TfidfVectorizer(tokenizer=tokenizer, lowercase=False)
    content_features = [extract_content_features(get_html_content(url)) for url in data_frame['URLs']]
    X = vectorize_data(data_frame, vectorizer, content_features, fit=True)
    model = MultinomialNB()
    model.fit(X, data_frame['Class'])
    return model, vectorizer

def predict(model, vectorizer, urls):
    content_features = [extract_content_features(get_html_content(url)) for url in urls]
    X = vectorize_data(pd.DataFrame(urls, columns=['URLs']), vectorizer, content_features)
    return model.predict(X)

url_df = pd.read_csv('Malicious URLs.csv')
train_df, test_df = train_test_split(url_df, test_size=0.2, random_state=42)
model, vectorizer = train_model(train_df)
test_urls = get_links_from_webpage(input("Enter the URL to analyze: "))
predictions = predict(model, vectorizer, test_urls)

result_df = pd.DataFrame({
    'URL': test_urls,
    'Prediction': ['Malicious' if pred == 1 else 'Benign' for pred in predictions]
})

print(result_df)

