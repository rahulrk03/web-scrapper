"""
Configuration Management for Web Scraping Framework

This module handles configuration loading, validation, and management
for the web scraping framework.
"""

import json
import yaml
import os
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages configuration for the web scraping framework.
    Supports YAML, JSON, and dictionary configurations.
    """
    
    def __init__(self, config_source: Optional[Union[str, Dict, Path]] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_source: Path to config file, dictionary, or None for defaults
        """
        self.config = self._load_default_config()
        
        if config_source:
            if isinstance(config_source, dict):
                self._merge_config(config_source)
            else:
                self._load_config_file(config_source)
        
        # Load environment variables
        self._load_env_variables()
        
        # Validate configuration
        self._validate_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            'scraping': {
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 1,
                'use_selenium': False,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            },
            'extraction': {
                'selectors': {},
                'extract_links': True,
                'extract_images': True,
                'extract_text': True,
                'max_text_length': 10000
            },
            'output': {
                'format': 'json',
                'filename': 'scraped_data',
                'directory': './output',
                'timestamp': True
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': None
            }
        }
    
    def _load_config_file(self, file_path: Union[str, Path]):
        """
        Load configuration from a file (YAML or JSON).
        
        Args:
            file_path: Path to configuration file
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"Configuration file not found: {file_path}")
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    logger.error(f"Unsupported config file format: {path.suffix}")
                    return
                
                self._merge_config(config_data)
                logger.info(f"Configuration loaded from {file_path}")
                
        except Exception as e:
            logger.error(f"Error loading config file {file_path}: {str(e)}")
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """
        Merge new configuration with existing configuration.
        
        Args:
            new_config: New configuration to merge
        """
        self._deep_merge(self.config, new_config)
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Recursively merge two dictionaries."""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _load_env_variables(self):
        """Load configuration from environment variables."""
        env_mapping = {
            'SCRAPER_TIMEOUT': ('scraping', 'timeout', int),
            'SCRAPER_MAX_RETRIES': ('scraping', 'max_retries', int),
            'SCRAPER_USE_SELENIUM': ('scraping', 'use_selenium', bool),
            'SCRAPER_OUTPUT_FORMAT': ('output', 'format', str),
            'SCRAPER_OUTPUT_DIR': ('output', 'directory', str),
            'SCRAPER_LOG_LEVEL': ('logging', 'level', str),
        }
        
        for env_var, (section, key, type_func) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if type_func == bool:
                        value = value.lower() in ['true', '1', 'yes', 'on']
                    else:
                        value = type_func(value)
                    
                    if section not in self.config:
                        self.config[section] = {}
                    self.config[section][key] = value
                    
                except ValueError as e:
                    logger.warning(f"Invalid value for {env_var}: {value} ({e})")
    
    def _validate_config(self):
        """Validate configuration values."""
        # Validate timeout
        if self.config['scraping']['timeout'] <= 0:
            logger.warning("Invalid timeout value, using default")
            self.config['scraping']['timeout'] = 30
        
        # Validate max_retries
        if self.config['scraping']['max_retries'] < 0:
            logger.warning("Invalid max_retries value, using default")
            self.config['scraping']['max_retries'] = 3
        
        # Validate output format
        valid_formats = ['json', 'csv', 'xlsx', 'docx', 'txt']
        if self.config['output']['format'] not in valid_formats:
            logger.warning(f"Invalid output format, using 'json'")
            self.config['output']['format'] = 'json'
        
        # Create output directory if it doesn't exist
        output_dir = Path(self.config['output']['directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to configuration value
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to configuration value
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_scraper_config(self) -> Dict[str, Any]:
        """Get configuration formatted for scraper classes."""
        return {
            'timeout': self.get('scraping.timeout'),
            'max_retries': self.get('scraping.max_retries'),
            'retry_delay': self.get('scraping.retry_delay'),
            'headers': self.get('scraping.headers'),
            'use_selenium': self.get('scraping.use_selenium'),
            'selectors': self.get('extraction.selectors')
        }
    
    def save_config(self, file_path: Union[str, Path], format_type: str = 'yaml'):
        """
        Save current configuration to file.
        
        Args:
            file_path: Path to save configuration
            format_type: Format to save ('yaml' or 'json')
        """
        path = Path(file_path)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                if format_type.lower() == 'yaml':
                    yaml.dump(self.config, f, default_flow_style=False, indent=2)
                elif format_type.lower() == 'json':
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"Unsupported format: {format_type}")
            
            logger.info(f"Configuration saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving config to {file_path}: {str(e)}")


def create_sample_config(file_path: str = 'config.yaml'):
    """
    Create a sample configuration file.
    
    Args:
        file_path: Path where to create the sample config
    """
    sample_config = {
        'scraping': {
            'timeout': 30,
            'max_retries': 3,
            'retry_delay': 1,
            'use_selenium': False,
            'headers': {
                'User-Agent': 'Custom Web Scraper 1.0'
            }
        },
        'extraction': {
            'selectors': {
                'title': 'h1',
                'content': '.content, .main, article',
                'links': 'a[href]'
            },
            'extract_links': True,
            'extract_images': True,
            'extract_text': True,
            'max_text_length': 10000
        },
        'targets': [
            {
                'name': 'example_site',
                'url': 'https://example.com',
                'selectors': {
                    'title': 'h1.page-title',
                    'description': '.description'
                }
            }
        ],
        'output': {
            'format': 'docx',
            'filename': 'scraped_data',
            'directory': './output',
            'timestamp': True,
            'docx_template': None
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(levelname)s - %(message)s',
            'file': 'scraper.log'
        }
    }
    
    config_manager = ConfigManager(sample_config)
    config_manager.save_config(file_path, 'yaml')
    print(f"Sample configuration created: {file_path}")


if __name__ == "__main__":
    # Example usage
    print("Configuration Management System")
    print("==============================")
    
    # Create sample config
    create_sample_config('sample_config.yaml')
    
    # Load and display config
    config = ConfigManager('sample_config.yaml')
    print(f"\nLoaded configuration:")
    print(f"Timeout: {config.get('scraping.timeout')}")
    print(f"Output format: {config.get('output.format')}")
    print(f"Output directory: {config.get('output.directory')}")