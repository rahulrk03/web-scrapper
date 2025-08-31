"""
Web Scraper Framework - Main Scraper Classes

This module contains the core web scraping functionality including
base scraper classes, data extraction, and processing logic.
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebScraper:
    """
    Main web scraper class that handles HTTP requests, data extraction,
    and basic processing of web content.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the web scraper with configuration.
        
        Args:
            config: Dictionary containing scraper configuration
        """
        self.config = config or {}
        self.session = requests.Session()
        self.setup_session()
        
    def setup_session(self):
        """Setup the requests session with headers and configuration."""
        headers = self.config.get('headers', {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.headers.update(headers)
        
        # Set timeout
        self.timeout = self.config.get('timeout', 30)
        
        # Set retry configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1)
    
    def scrape(self, url: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """
        Scrape data from a URL.
        
        Args:
            url: Target URL to scrape
            method: HTTP method to use (GET, POST, etc.)
            **kwargs: Additional arguments for the request
            
        Returns:
            Dictionary containing scraped data
        """
        logger.info(f"Scraping {url}")
        
        for attempt in range(self.max_retries):
            try:
                response = self._make_request(url, method, **kwargs)
                if response.status_code == 200:
                    return self._extract_data(response, url)
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
        
        return {}
    
    def _make_request(self, url: str, method: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling."""
        request_kwargs = {
            'timeout': self.timeout,
            **kwargs
        }
        
        if method.upper() == 'GET':
            return self.session.get(url, **request_kwargs)
        elif method.upper() == 'POST':
            return self.session.post(url, **request_kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    def _extract_data(self, response: requests.Response, url: str) -> Dict[str, Any]:
        """
        Extract data from HTTP response.
        
        Args:
            response: HTTP response object
            url: Original URL
            
        Returns:
            Dictionary containing extracted data
        """
        content_type = response.headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            return self._extract_json_data(response)
        elif 'text/html' in content_type:
            return self._extract_html_data(response, url)
        else:
            return self._extract_text_data(response, url)
    
    def _extract_json_data(self, response: requests.Response) -> Dict[str, Any]:
        """Extract data from JSON response."""
        try:
            return {
                'type': 'json',
                'data': response.json(),
                'url': response.url,
                'status_code': response.status_code
            }
        except json.JSONDecodeError:
            return {
                'type': 'json_error',
                'error': 'Invalid JSON response',
                'url': response.url,
                'status_code': response.status_code
            }
    
    def _extract_html_data(self, response: requests.Response, url: str) -> Dict[str, Any]:
        """Extract data from HTML response."""
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Basic extraction
        data = {
            'type': 'html',
            'url': url,
            'title': self._safe_extract(soup, 'title'),
            'meta_description': self._get_meta_description(soup),
            'headings': self._extract_headings(soup),
            'links': self._extract_links(soup, url),
            'images': self._extract_images(soup, url),
            'text_content': self._extract_text(soup),
            'status_code': response.status_code
        }
        
        # Custom selectors from config
        selectors = self.config.get('selectors', {})
        for key, selector in selectors.items():
            data[key] = self._extract_by_selector(soup, selector)
        
        return data
    
    def _extract_text_data(self, response: requests.Response, url: str) -> Dict[str, Any]:
        """Extract data from plain text response."""
        return {
            'type': 'text',
            'url': url,
            'content': response.text,
            'status_code': response.status_code
        }
    
    def _safe_extract(self, soup: BeautifulSoup, tag: str) -> str:
        """Safely extract text from a tag."""
        element = soup.find(tag)
        return element.get_text(strip=True) if element else ""
    
    def _get_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description."""
        meta = soup.find('meta', attrs={'name': 'description'})
        return meta.get('content', '') if meta else ""
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract all headings."""
        headings = {}
        for i in range(1, 7):
            tag = f'h{i}'
            elements = soup.find_all(tag)
            headings[tag] = [elem.get_text(strip=True) for elem in elements]
        return headings
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all links."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            links.append({
                'text': link.get_text(strip=True),
                'url': absolute_url,
                'relative_url': href
            })
        return links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all images."""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                absolute_url = urljoin(base_url, src)
                images.append({
                    'src': absolute_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        return images
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text content."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_by_selector(self, soup: BeautifulSoup, selector: str) -> List[str]:
        """Extract text using CSS selector."""
        elements = soup.select(selector)
        return [elem.get_text(strip=True) for elem in elements]


class AdvancedScraper(WebScraper):
    """
    Advanced scraper with additional features like JavaScript support,
    form handling, and more sophisticated data extraction.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.use_selenium = config.get('use_selenium', False)
        if self.use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver (placeholder for now)."""
        # This would require selenium to be installed
        # and appropriate WebDriver setup
        logger.info("Selenium support would be initialized here")
        pass
    
    def scrape_with_js(self, url: str) -> Dict[str, Any]:
        """
        Scrape content that requires JavaScript execution.
        
        Args:
            url: Target URL
            
        Returns:
            Dictionary containing scraped data
        """
        if not self.use_selenium:
            logger.warning("JavaScript scraping requires Selenium configuration")
            return self.scrape(url)
        
        # Placeholder for Selenium-based scraping
        logger.info(f"Would use Selenium to scrape {url}")
        return self.scrape(url)


if __name__ == "__main__":
    # Example usage
    scraper = WebScraper()
    
    # Test with a simple HTML page
    test_config = {
        'selectors': {
            'paragraphs': 'p',
            'titles': 'h1, h2, h3'
        }
    }
    
    scraper = WebScraper(test_config)
    
    print("Web Scraper Framework")
    print("====================")
    print("Main scraper classes implemented:")
    print("- WebScraper: Basic web scraping functionality")
    print("- AdvancedScraper: Extended features (JS support, forms, etc.)")
    print("\nExample usage:")
    print("scraper = WebScraper()")
    print("data = scraper.scrape('https://example.com')")