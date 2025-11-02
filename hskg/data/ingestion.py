""
Data ingestion module for HSKG.
Handles data collection from various sources including files, APIs, and web scraping.
"""
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from bs4 import BeautifulSoup
import requests


class DataSource(Enum):
    """Enumeration of supported data sources."""
    FILE = "file"
    WEB = "web"
    API = "api"
    DATABASE = "database"


class DataIngestor(ABC):
    """Abstract base class for data ingestion."""
    
    def __init__(self, source: DataSource):
        self.source = source
    
    @abstractmethod
    def fetch(self, **kwargs) -> Any:
        """Fetch data from the specified source."""
        pass


class FileIngestor(DataIngestor):
    """Handles data ingestion from various file formats."""
    
    def __init__(self):
        super().__init__(DataSource.FILE)
    
    def fetch(self, file_path: Union[str, Path], file_type: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """
        Load data from a file.
        
        Args:
            file_path: Path to the file
            file_type: Type of file (csv, json, excel, etc.). If None, inferred from file extension.
            **kwargs: Additional arguments passed to the underlying pandas read function.
            
        Returns:
            DataFrame containing the loaded data
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_type = file_type or file_path.suffix[1:].lower()  # Remove the dot
        
        if file_type == 'csv':
            return pd.read_csv(file_path, **kwargs)
        elif file_type in ['xls', 'xlsx']:
            return pd.read_excel(file_path, **kwargs)
        elif file_type == 'json':
            return pd.read_json(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")


class WebScraper(DataIngestor):
    """Handles web scraping for data collection."""
    
    def __init__(self):
        super().__init__(DataSource.WEB)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch(self, url: str, parser: str = 'html.parser', **kwargs) -> BeautifulSoup:
        """
        Scrape content from a web page.
        
        Args:
            url: URL of the web page to scrape
            parser: Parser to use (default: 'html.parser')
            **kwargs: Additional arguments for requests.get()
            
        Returns:
            BeautifulSoup object containing the parsed HTML
        """
        try:
            response = requests.get(url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return BeautifulSoup(response.text, parser)
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch {url}: {str(e)}")


class DataIngestionFactory:
    """Factory class for creating appropriate data ingestor instances."""
    
    @staticmethod
    def get_ingestor(source: DataSource) -> DataIngestor:
        """
        Get an appropriate data ingestor for the specified source.
        
        Args:
            source: Type of data source
            
        Returns:
            An instance of the appropriate DataIngestor subclass
        """
        if source == DataSource.FILE:
            return FileIngestor()
        elif source == DataSource.WEB:
            return WebScraper()
        # Add more ingestor types as needed
        else:
            raise ValueError(f"Unsupported data source: {source}")
