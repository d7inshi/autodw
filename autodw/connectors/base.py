from abc import ABC, abstractmethod
import logging
from typing import Dict, List, Tuple, Optional

class BaseConnector(ABC):
    """Abstract base class for database connectors, defining unified interface specifications"""
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
        self.logger = logging.getLogger("autodw.connectors")
        self.logger.setLevel(logging.INFO)
        
    @abstractmethod
    def connect(self) -> bool:
        """Establish a database connection"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close the database connection"""
        pass
    
    @abstractmethod
    def get_tables(self) -> List[str]:
        """Get all table names"""
        pass
    
    @abstractmethod
    def get_columns(self, table_name: str) -> List[Dict[str, str]]:
        """
        Get table structure information
        :return: [{
            'name': Column name, 
            'type': Data type, 
            'nullable': Whether nullable,
            'primary_key': Whether primary key,
            'default': Default value
        }]
        """
        pass
    
    @abstractmethod
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """
        Get foreign key relationships
        :return: [{
            'column': Current table column name,
            'foreign_table': Foreign table name,
            'foreign_column': Foreign column name
        }]
        """
        pass
        
    @abstractmethod
    def get_primary_keys(self, table_name: str) -> List[str]:
        """Get list of primary key column names for a table (in order)"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Tuple]:
        """Execute SQL query and return results"""
        pass
    
    def __enter__(self):
        """Support context manager protocol"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Automatically close connection when exiting context"""
        self.disconnect()
    
    def _log_success(self, operation: str):
        self.logger.info(f"{operation} executed successfully")
    
    def _log_error(self, operation: str, error: Exception):
        self.logger.error(f"{operation} failed: {str(error)}")