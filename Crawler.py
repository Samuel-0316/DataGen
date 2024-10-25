import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

def extract_data_from_webpage(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all text content
        text_content = soup.get_text(separator=' ', strip=True)

        # Extract all hyperlinks for crawling purposes only (not saving to file)
        links = []
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            if is_valid_url(full_url):
                links.append(full_url)

        return text_content, links
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None, []

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.scheme in ['http', 'https'])

def write_to_file(filename, data):
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(data + '\n')

def crawl_single_page(url):
    print(f"Extracting from: {url}")
    text_content, _ = extract_data_from_webpage(url)  # Ignore links
    if text_content:
        write_to_file('single_page_content.txt', text_content)
    print("Extraction complete for single page.")

def crawl_website(start_url, max_pages=50):
    visited = set()  # To keep track of visited URLs
    to_visit = [start_url]

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        print(f"Crawling: {current_url}")
        text_content, links = extract_data_from_webpage(current_url)

        if text_content:
            write_to_file('crawled_content.txt', text_content)

        # Only add links that haven't been visited
        for link in links:
            if link not in visited and link not in to_visit:
                to_visit.append(link)

        visited.add(current_url)
        time.sleep(1)

    print("Crawling complete.")

def main():
    start_url = input("Enter the website URL: ")
    mode = input("Choose mode: (1) Single Page Extraction (2) Full Site Crawl: ")

    if mode == '1':
        crawl_single_page(start_url)
    elif mode == '2':
        max_pages = int(input("Enter the maximum number of pages to crawl: "))
        crawl_website(start_url, max_pages)
    else:
        print("Invalid mode selected.")

if __name__ == "__main__":
    main()