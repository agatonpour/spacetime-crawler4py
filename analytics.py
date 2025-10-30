import json
import os
from collections import Counter
from urllib.parse import urlparse
import re

class Analytics:
    def __init__(self, save_file="analytics.json"):
        self.save_file = save_file
        self.data = self._load()
    
    def _load(self):
        """Load analytics from file or create new"""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        # default structure
        return {
            "unique_urls": set(),  # will convert to list when saving
            "longest_page": {"url": "", "word_count": 0},
            "word_frequencies": {},
            "subdomains": {}  # subdomain -> set of urls
        }
    
    def _save(self):
        """Save analytics to file"""
        # convert sets to lists for JSON serialization
        save_data = {
            "unique_urls": list(self.data["unique_urls"]),
            "longest_page": self.data["longest_page"],
            "word_frequencies": self.data["word_frequencies"],
            "subdomains": {k: list(v) for k, v in self.data["subdomains"].items()}
        }
        with open(self.save_file, 'w') as f:
            json.dump(save_data, f, indent=2)
    
    def add_page(self, url, text_content):
        """
        Track a page's analytics
        url: the page URL (defragged)
        text_content: the text content of the page (no HTML tags)
        """
        # convert loaded data back to sets if needed
        if isinstance(self.data["unique_urls"], list):
            self.data["unique_urls"] = set(self.data["unique_urls"])
        for subdomain in self.data["subdomains"]:
            if isinstance(self.data["subdomains"][subdomain], list):
                self.data["subdomains"][subdomain] = set(self.data["subdomains"][subdomain])
        
        # 1. Track unique URL
        self.data["unique_urls"].add(url)
        
        # 2. Count words in page
        words = self._tokenize(text_content)
        word_count = len(words)
        
        # Update longest page
        if word_count > self.data["longest_page"]["word_count"]:
            self.data["longest_page"] = {
                "url": url,
                "word_count": word_count
            }
        
        # 3. Update word frequencies (filter stop words later)
        for word in words:
            self.data["word_frequencies"][word] = self.data["word_frequencies"].get(word, 0) + 1
        
        # 4. Track subdomains (only for uci.edu)
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        if "uci.edu" in hostname:
            # extract subdomain
            subdomain = hostname
            if subdomain not in self.data["subdomains"]:
                self.data["subdomains"][subdomain] = set()
            self.data["subdomains"][subdomain].add(url)
        
        # save periodically (every page)
        self._save()
    
    def _tokenize(self, text):
        """Extract words from text"""
        # lowercase and extract words (alphanumeric sequences)
        words = re.findall(r'\b[a-z0-9]+\b', text.lower())
        return words
    
    def get_unique_page_count(self):
        """Get number of unique pages"""
        if isinstance(self.data["unique_urls"], list):
            return len(self.data["unique_urls"])
        return len(self.data["unique_urls"])
    
    def get_longest_page(self):
        """Get the longest page info"""
        return self.data["longest_page"]
    
    def get_top_words(self, n=50, stop_words=None):
        """
        Get top N most common words
        stop_words: set of words to ignore
        """
        if stop_words is None:
            stop_words = set()
        
        # filter out stop words
        filtered_freq = {
            word: count for word, count in self.data["word_frequencies"].items()
            if word not in stop_words
        }
        
        # get top N
        counter = Counter(filtered_freq)
        return counter.most_common(n)
    
    def get_subdomains(self):
        """Get subdomain stats, sorted alphabetically"""
        subdomain_counts = []
        for subdomain, urls in self.data["subdomains"].items():
            if isinstance(urls, list):
                count = len(urls)
            else:
                count = len(urls)
            subdomain_counts.append((subdomain, count))
        
        # sort alphabetically
        subdomain_counts.sort(key=lambda x: x[0])
        return subdomain_counts
    
    def generate_report(self, stop_words_file="stop_words.txt"):
        """Generate the report for submission"""
        # load stop words
        stop_words = set()
        if os.path.exists(stop_words_file):
            with open(stop_words_file, 'r') as f:
                stop_words = set(line.strip().lower() for line in f)
        
        report = []
        report.append("=" * 60)
        report.append("WEB CRAWLER ANALYTICS REPORT")
        report.append("=" * 60)
        report.append("")
        
        # 1. Unique pages
        report.append(f"1. Number of unique pages: {self.get_unique_page_count()}")
        report.append("")
        
        # 2. Longest page
        longest = self.get_longest_page()
        report.append(f"2. Longest page (by word count):")
        report.append(f"   URL: {longest['url']}")
        report.append(f"   Word count: {longest['word_count']}")
        report.append("")
        
        # 3. Top 50 words
        report.append("3. 50 most common words:")
        top_words = self.get_top_words(50, stop_words)
        for i, (word, count) in enumerate(top_words, 1):
            report.append(f"   {i}. {word}: {count}")
        report.append("")
        
        # 4. Subdomains
        report.append("4. Subdomains in uci.edu domain:")
        subdomains = self.get_subdomains()
        for subdomain, count in subdomains:
            report.append(f"   {subdomain}, {count}")
        report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)

