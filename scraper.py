import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
from analytics import Analytics

# Initialize analytics tracker
analytics = Analytics()

# Trap detection - track seen URLs
seen = set()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    # Filter valid links and defragment them
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    # Add to seen set for trap detection
    seen.add(url)
    
    if resp.status != 200 or not getattr(resp, "raw_response", None):
        return []
    if "text/html" not in resp.raw_response.headers.get("Content-Type", ""):
        return []
    
    # Parse HTML
    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    
    # Remove script, style, and other non-content tags
    for t in soup(["script", "style", "noscript"]):
        t.extract()
    
    # Get text content for analytics (no HTML tags)
    text_content = soup.get_text(separator=' ', strip=True)
    
    # Track this page in analytics
    # Use the actual URL from response (defragged)
    actual_url, _ = urldefrag(resp.url)
    analytics.add_page(actual_url, text_content)
    
    # Extract links
    links = []
    for a in soup.find_all("a", href=True):
        u = urljoin(resp.raw_response.url, a["href"])
        u, _ = urldefrag(u)
        links.append(u)
    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Check if URL is in allowed domains
        hostname = parsed.netloc.lower()
        allowed_domains = [
            ".ics.uci.edu",
            ".cs.uci.edu",
            ".informatics.uci.edu",
            ".stat.uci.edu"
        ]
        
        # Check if hostname ends with any allowed domain or exactly matches (without subdomain)
        is_allowed = False
        for domain in allowed_domains:
            if hostname.endswith(domain) or hostname == domain[1:]:  # domain[1:] removes the leading dot
                is_allowed = True
                break
        
        if not is_allowed:
            return False
        
        # Trap detection - avoid revisiting same URLs
        if url in seen:
            return False
        
        # Check for low-value file extensions
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        
        return True

    except TypeError:
        print("TypeError for", parsed)
        raise
