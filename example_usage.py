#!/usr/bin/env python3
"""
Example usage of the Web Scraping Framework

This script demonstrates how to use the web scraping framework
to scrape data from websites and export it to DOCX format.
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from scraper import WebScraper, AdvancedScraper
from config import ConfigManager
from exporters import DataExporter
from utils import setup_logging, ProgressTracker, clean_text

def example_basic_scraping():
    """Example of basic web scraping functionality."""
    print("Basic Web Scraping Example")
    print("=" * 50)
    
    # Setup logging
    logger = setup_logging('INFO')
    
    # Create a simple configuration
    config = {
        'scraping': {
            'timeout': 30,
            'max_retries': 2,
            'headers': {
                'User-Agent': 'Web Scraping Framework Example 1.0'
            }
        },
        'extraction': {
            'selectors': {
                'main_content': 'main, .content, .post-content',
                'navigation': 'nav a',
                'sidebar': '.sidebar, .widget'
            }
        }
    }
    
    # Initialize scraper
    config_manager = ConfigManager(config)
    scraper = WebScraper(config_manager.get_scraper_config())
    
    # URLs to scrape (using httpbin.org for reliable testing)
    test_urls = [
        'https://httpbin.org/html',  # Returns sample HTML
        'https://httpbin.org/json',  # Returns JSON data
    ]
    
    scraped_data = []
    
    for url in test_urls:
        print(f"\nScraping: {url}")
        try:
            data = scraper.scrape(url)
            if data:
                print(f"✓ Successfully scraped {url}")
                print(f"  Data type: {data.get('type', 'unknown')}")
                if data.get('title'):
                    print(f"  Title: {data['title']}")
                scraped_data.append(data)
            else:
                print(f"✗ No data retrieved from {url}")
        except Exception as e:
            print(f"✗ Error scraping {url}: {str(e)}")
    
    return scraped_data

def example_data_export(data):
    """Example of exporting data to different formats."""
    print("\nData Export Example")
    print("=" * 50)
    
    if not data:
        print("No data to export")
        return
    
    # Create export configuration
    export_config = {
        'directory': './output',
        'filename': 'example_scrape',
        'timestamp': True
    }
    
    exporter = DataExporter(export_config)
    
    # Export to different formats
    formats = ['json', 'csv', 'txt']
    
    # Add DOCX if available
    try:
        import docx
        formats.append('docx')
    except ImportError:
        print("Note: python-docx not available, skipping DOCX export")
    
    # Add Excel if available
    try:
        import openpyxl
        formats.append('xlsx')
    except ImportError:
        print("Note: openpyxl not available, skipping Excel export")
    
    exported_files = []
    
    for format_type in formats:
        try:
            filepath = exporter.export(data, format_type)
            exported_files.append(filepath)
            print(f"✓ Exported to {format_type.upper()}: {filepath}")
        except Exception as e:
            print(f"✗ Error exporting to {format_type}: {str(e)}")
    
    return exported_files

def example_configuration_usage():
    """Example of using configuration files."""
    print("\nConfiguration Management Example")
    print("=" * 50)
    
    # Create a sample configuration file
    from config import create_sample_config
    
    config_file = 'example_config.yaml'
    create_sample_config(config_file)
    print(f"✓ Created sample configuration: {config_file}")
    
    # Load and use the configuration
    config_manager = ConfigManager(config_file)
    
    print(f"Configuration loaded:")
    print(f"  Timeout: {config_manager.get('scraping.timeout')}")
    print(f"  Max retries: {config_manager.get('scraping.max_retries')}")
    print(f"  Output format: {config_manager.get('output.format')}")
    print(f"  Output directory: {config_manager.get('output.directory')}")
    
    return config_manager

def example_advanced_features():
    """Example of advanced framework features."""
    print("\nAdvanced Features Example")
    print("=" * 50)
    
    # Progress tracking
    print("Progress tracking:")
    tracker = ProgressTracker(5)
    
    for i in range(3):
        tracker.update(success=True)
        print(f"  Processed item {i+1}")
    
    for i in range(2):
        tracker.update(success=False, error="Sample error")
        print(f"  Failed item {i+4}")
    
    progress = tracker.get_progress()
    print(f"  Final stats: {progress['completed']} completed, {progress['failed']} failed")
    print(f"  Success rate: {progress['success_rate']:.1f}%")
    
    # Text cleaning utility
    print("\nText cleaning utility:")
    dirty_text = "   This    is   \n\n  messy    text   \t\t  "
    clean = clean_text(dirty_text)
    print(f"  Original: {repr(dirty_text)}")
    print(f"  Cleaned: {repr(clean)}")

def main():
    """Main function to run all examples."""
    print("Web Scraping Framework - Examples")
    print("=" * 60)
    print("This script demonstrates the main features of the framework:")
    print("- Basic web scraping")
    print("- Data export to multiple formats")
    print("- Configuration management")
    print("- Advanced utilities")
    print()
    
    try:
        # Create output directory
        Path('./output').mkdir(exist_ok=True)
        
        # Run examples
        scraped_data = example_basic_scraping()
        exported_files = example_data_export(scraped_data)
        config_manager = example_configuration_usage()
        example_advanced_features()
        
        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        print(f"Scraped {len(scraped_data)} URLs")
        print(f"Exported {len(exported_files)} files")
        
        if exported_files:
            print("\nExported files:")
            for filepath in exported_files:
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    print(f"  {filepath} ({size} bytes)")
        
        print("\nFramework features demonstrated:")
        print("✓ Web scraping with retry logic")
        print("✓ Multiple export formats")
        print("✓ Configuration management")
        print("✓ Progress tracking")
        print("✓ Text processing utilities")
        print("✓ Error handling")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())