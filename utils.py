"""
Utility Functions for Web Scraping Framework

This module contains various utility functions used throughout
the web scraping framework.
"""

import re
import time
import hashlib
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Raw text to clean
        max_length: Maximum length to truncate to
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E\u00A0-\uFFFF]', '', text)
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    
    return text


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalize and clean URL.
    
    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs
        
    Returns:
        Normalized URL
    """
    if not url:
        return ""
    
    # Convert relative URLs to absolute
    if base_url and not url.startswith(('http://', 'https://')):
        url = urllib.parse.urljoin(base_url, url)
    
    # Parse and rebuild URL to normalize
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(parsed)


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name
    """
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower()
    except:
        return ""


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def generate_filename(base_name: str, extension: str = "", 
                     timestamp: bool = True, url: Optional[str] = None) -> str:
    """
    Generate a filename for scraped data.
    
    Args:
        base_name: Base filename
        extension: File extension (with or without dot)
        timestamp: Whether to add timestamp
        url: URL to derive name from
        
    Returns:
        Generated filename
    """
    filename = base_name
    
    # Add URL-based suffix if provided
    if url:
        domain = extract_domain(url)
        if domain:
            # Clean domain name for filename
            clean_domain = re.sub(r'[^\w\-.]', '_', domain)
            filename = f"{filename}_{clean_domain}"
    
    # Add timestamp
    if timestamp:
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename}_{timestamp_str}"
    
    # Add extension
    if extension:
        if not extension.startswith('.'):
            extension = f".{extension}"
        filename = f"{filename}{extension}"
    
    return filename


def create_url_hash(url: str) -> str:
    """
    Create a hash of URL for caching or deduplication.
    
    Args:
        url: URL to hash
        
    Returns:
        SHA256 hash of URL
    """
    return hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]


def rate_limit(delay: float = 1.0):
    """
    Simple rate limiting decorator.
    
    Args:
        delay: Delay in seconds between calls
    """
    def decorator(func):
        last_called = [0.0]
        
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < delay:
                time.sleep(delay - elapsed)
            last_called[0] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class UrlFilter:
    """
    Utility class for filtering URLs based on patterns and rules.
    """
    
    def __init__(self):
        self.include_patterns = []
        self.exclude_patterns = []
        self.allowed_domains = []
        self.blocked_domains = []
    
    def add_include_pattern(self, pattern: str):
        """Add regex pattern for URLs to include."""
        self.include_patterns.append(re.compile(pattern))
    
    def add_exclude_pattern(self, pattern: str):
        """Add regex pattern for URLs to exclude."""
        self.exclude_patterns.append(re.compile(pattern))
    
    def add_allowed_domain(self, domain: str):
        """Add domain to allowed list."""
        self.allowed_domains.append(domain.lower())
    
    def add_blocked_domain(self, domain: str):
        """Add domain to blocked list."""
        self.blocked_domains.append(domain.lower())
    
    def should_process(self, url: str) -> bool:
        """
        Check if URL should be processed based on filters.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL should be processed
        """
        # Check if URL is valid
        if not is_valid_url(url):
            return False
        
        domain = extract_domain(url)
        
        # Check blocked domains
        if domain in self.blocked_domains:
            return False
        
        # Check allowed domains (if specified)
        if self.allowed_domains and domain not in self.allowed_domains:
            return False
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.search(url):
                return False
        
        # Check include patterns (if specified)
        if self.include_patterns:
            for pattern in self.include_patterns:
                if pattern.search(url):
                    return True
            return False
        
        return True


class DataValidator:
    """
    Utility class for validating scraped data.
    """
    
    @staticmethod
    def validate_url_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean URL-based scraped data.
        
        Args:
            data: Raw scraped data
            
        Returns:
            Validated and cleaned data
        """
        validated = {}
        
        # Validate URL
        if 'url' in data:
            validated['url'] = normalize_url(data['url'])
        
        # Validate title
        if 'title' in data:
            validated['title'] = clean_text(data['title'], 200)
        
        # Validate text content
        if 'text_content' in data:
            validated['text_content'] = clean_text(data['text_content'])
        
        # Validate links
        if 'links' in data and isinstance(data['links'], list):
            validated['links'] = []
            for link in data['links']:
                if isinstance(link, dict) and 'url' in link:
                    clean_link = {
                        'url': normalize_url(link['url'], data.get('url')),
                        'text': clean_text(link.get('text', ''), 100)
                    }
                    if is_valid_url(clean_link['url']):
                        validated['links'].append(clean_link)
        
        # Validate images
        if 'images' in data and isinstance(data['images'], list):
            validated['images'] = []
            for img in data['images']:
                if isinstance(img, dict) and 'src' in img:
                    clean_img = {
                        'src': normalize_url(img['src'], data.get('url')),
                        'alt': clean_text(img.get('alt', ''), 100),
                        'title': clean_text(img.get('title', ''), 100)
                    }
                    if is_valid_url(clean_img['src']):
                        validated['images'].append(clean_img)
        
        # Copy other fields as-is
        for key, value in data.items():
            if key not in validated:
                validated[key] = value
        
        return validated
    
    @staticmethod
    def is_valid_scraped_data(data: Any) -> bool:
        """
        Check if data appears to be valid scraped content.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data appears valid
        """
        if not data:
            return False
        
        if isinstance(data, dict):
            # Should have at least a URL or some content
            has_url = 'url' in data and is_valid_url(data['url'])
            has_content = any(key in data for key in ['title', 'text_content', 'links', 'images'])
            return has_url or has_content
        
        if isinstance(data, list):
            # List should contain valid items
            return len(data) > 0 and all(DataValidator.is_valid_scraped_data(item) for item in data[:5])
        
        return False


class ProgressTracker:
    """
    Utility class for tracking scraping progress.
    """
    
    def __init__(self, total_items: int = 0):
        self.total_items = total_items
        self.completed_items = 0
        self.failed_items = 0
        self.start_time = datetime.now()
        self.errors = []
    
    def update(self, success: bool = True, error: Optional[str] = None):
        """Update progress tracking."""
        if success:
            self.completed_items += 1
        else:
            self.failed_items += 1
            if error:
                self.errors.append({
                    'timestamp': datetime.now(),
                    'error': error
                })
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress statistics."""
        elapsed_time = datetime.now() - self.start_time
        total_processed = self.completed_items + self.failed_items
        
        progress = {
            'total_items': self.total_items,
            'completed': self.completed_items,
            'failed': self.failed_items,
            'total_processed': total_processed,
            'elapsed_time': str(elapsed_time),
            'success_rate': (self.completed_items / total_processed * 100) if total_processed > 0 else 0
        }
        
        if self.total_items > 0:
            progress['percentage'] = (total_processed / self.total_items * 100)
            
            # Estimate remaining time
            if total_processed > 0:
                avg_time_per_item = elapsed_time.total_seconds() / total_processed
                remaining_items = self.total_items - total_processed
                estimated_remaining = timedelta(seconds=avg_time_per_item * remaining_items)
                progress['estimated_remaining'] = str(estimated_remaining)
        
        return progress
    
    def print_progress(self):
        """Print current progress to console."""
        progress = self.get_progress()
        
        print(f"\nProgress: {progress['completed']}/{progress['total_items']} completed")
        if 'percentage' in progress:
            print(f"Completion: {progress['percentage']:.1f}%")
        print(f"Success rate: {progress['success_rate']:.1f}%")
        print(f"Elapsed time: {progress['elapsed_time']}")
        if 'estimated_remaining' in progress:
            print(f"Estimated remaining: {progress['estimated_remaining']}")


def setup_logging(level: str = 'INFO', log_file: Optional[str] = None, 
                 log_format: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration for the framework.
    
    Args:
        level: Logging level
        log_file: Optional log file path
        log_format: Optional custom log format
        
    Returns:
        Configured logger
    """
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[]
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
    
    return logging.getLogger(__name__)


if __name__ == "__main__":
    # Example usage of utilities
    print("Web Scraping Framework Utilities")
    print("================================")
    
    # Test URL utilities
    test_url = "https://example.com/page?param=value"
    print(f"\nURL utilities:")
    print(f"Original URL: {test_url}")
    print(f"Domain: {extract_domain(test_url)}")
    print(f"URL hash: {create_url_hash(test_url)}")
    print(f"Is valid: {is_valid_url(test_url)}")
    
    # Test text cleaning
    dirty_text = "   This is   \n\n  dirty    text    with   extra   spaces   "
    clean = clean_text(dirty_text)
    print(f"\nText cleaning:")
    print(f"Original: {repr(dirty_text)}")
    print(f"Cleaned: {repr(clean)}")
    
    # Test filename generation
    filename = generate_filename("scraped_data", "json", True, test_url)
    print(f"\nGenerated filename: {filename}")
    
    # Test progress tracker
    print(f"\nProgress tracking:")
    tracker = ProgressTracker(10)
    for i in range(7):
        tracker.update(success=True)
    for i in range(2):
        tracker.update(success=False, error="Sample error")
    
    progress = tracker.get_progress()
    print(f"Completed: {progress['completed']}")
    print(f"Failed: {progress['failed']}")
    print(f"Success rate: {progress['success_rate']:.1f}%")