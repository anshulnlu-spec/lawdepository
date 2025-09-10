def scrape_links_from_url(url):
    """
    Scrape document links from a webpage.
    Returns a list of URLs that appear to be documents.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert relative URLs to absolute
            full_url = urljoin(url, href)
            
            # Filter for document-like URLs
            if any(ext in full_url.lower() for ext in ['.pdf', '.doc', '.docx', '.html', '.htm']):
                links.append(full_url)
            elif any(keyword in full_url.lower() for keyword in ['act', 'law', 'regulation', 'bill', 'statute']):
                links.append(full_url)
        
        print(f"Found {len(links)} potential document links from {url}")
        return list(set(links))  # Remove duplicates
        
    except Exception as e:
        print(f"Error scraping links from {url}: {e}")
        return []
