from abc import ABC, abstractmethod
from typing import Dict, Any, Union, Type
from ..connectors.base import BaseConnector
import logging

logger = logging.getLogger("autodw.serializers")

class Serializer(ABC):
    """Abstract base class for database schema serialization"""
    
    @abstractmethod
    def serialize(self, schema_data: Dict[str, Any], db_name: str = "database") -> str:
        """
        Serialize database schema data into a specific format
        
        Args:
            schema_data: Raw schema data obtained from the connector
            db_name: Database name
            
        Returns:
            Serialized string
        """
        pass


class BaseSerializer(Serializer):
    """Implementation of BASE_FORMAT serializer"""
    
    def serialize(self, schema_data: Dict[str, Any], db_name: str = "database") -> str:
        """
        Generate serialized string in BASE_FORMAT format:
          Table name: Column1 (sample1, sample2), Column2 (sample3, sample4) | Foreign key relationships
        """
        # 1. Process table data
        table_strings = []
        for table_name, table_data in schema_data.items():
            column_strings = []
            
            for column in table_data["columns"]:
                # Process sample data
                samples = ", ".join(map(str, column.get("samples", [])[:3]))
                column_strings.append(f"{column['name']} ({samples})")
            
            table_strings.append(f"{table_name} : {', '.join(column_strings)}")
        
        # 2. Process foreign key relationships
        foreign_keys = []
        for table_name, table_data in schema_data.items():
            for fk in table_data["foreign_keys"]:
                foreign_keys.append(
                    f"{table_name}.{fk['column']}={fk['foreign_table']}.{fk['foreign_column']}"
                )
        
        # 3. Combine all parts
        return " | ".join(table_strings + foreign_keys)


class DatabaseSchemaSerializer:
    """High-level interface for generating serialized output directly from database connection"""
    
    def __init__(
        self, 
        connector: BaseConnector,
        serializer_type: str = "default",
        db_name: str = None,
        include_samples: bool = True,
        sample_size: int = 3,
        sample_method: str = "random"
    ):
        """
        Initialize database schema serializer
        
        Args:
            connector: Database connector instance
            serializer_class: Serializer type (BaseSerializer or MSchemaSerializer)
            db_name: Custom database name (defaults to connector extracted ID)
            include_samples: Whether to include sample data
            sample_size: Number of samples
            sample_method: Sampling method ("random" or "frequency")
        """
        assert serializer_type in ["default", "mschema"], "Serializer type not supported"
        if serializer_type == "mschema":
            self.serializer_class = MSchemaSerializer
        else:
            self.serializer_class = BaseSerializer
        self.connector = connector
        self.db_name = db_name
        self.include_samples = include_samples
        self.sample_size = sample_size
        self.sample_method = sample_method
        
    def connect(self):
        """Establish database connection"""
        if not self.connector.connect():
            raise ConnectionError("Database connection failed")
    
    def disconnect(self):
        """Close database connection"""
        self.connector.disconnect()
    
    def generate(self) -> str:
        """Get serialized output"""
        try:
            self.connect()
            
            # Get database schema
            schema_data = self.connector.get_database_schema(
                format="default",
                include_samples=self.include_samples,
                sample_size=self.sample_size,
                sample_method=self.sample_method
            )
            
            # Determine database name
            db_name = self.db_name or getattr(
                self.connector, "_extract_db_id", lambda: "database"
            )()
            
            # Generate output using specified serializer
            serializer = self.serializer_class()
            return serializer.serialize(schema_data, db_name)
            
        except Exception as e:
            logger.error(f"Serialization failed: {str(e)}")
            raise
        finally:
            self.disconnect()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

class MSchemaSerializer(Serializer):
    """Implementation of M_SCHEMA_FORMAT serializer"""
    
    def serialize(self, schema_data: Dict[str, Any], db_name: str = "database") -> str:
        """
        Generate serialized string in M_SCHEMA_FORMAT format:
          [DB_ID] db_name
          [Schema]
          #Table: table_name
          [
            (column definition),
            ...
          ]
          [Foreign keys]
          Foreign key relationships
        """
        # 1. Database identification header
        result = [f"[DB_ID] {db_name}", "[Schema]"]
        
        # 2. Process each table
        for table_name, table_data in schema_data.items():
            result.append(f"#Table: {table_name}")
            result.append("[")
            
            # Process columns
            for column in table_data["columns"]:
                # Build column description
                description_parts = []
                
                # Data type
                desc = f"{column['name']}: {column['type']}"
                
                # Primary key indicator
                if column['name'] in table_data["primary_keys"]:
                    desc += ", Primary Key"
                
                # Nullability
                desc += ", NOT NULL" if not column['nullable'] else ", NULL"
                
                # Foreign key mapping
                for fk in table_data["foreign_keys"]:
                    if fk['column'] == column['name']:
                        desc += f", Maps to {fk['foreign_table']}({fk['foreign_column']})"
                
                # Add sample data
                samples = ", ".join(map(str, column.get("samples", [])[:3]))
                desc += f", Examples: [{samples}]"
                
                result.append(f"({desc})")
            
            result.append("]")
        
        # 3. Foreign keys section
        result.append("[Foreign keys]")
        foreign_keys = []
        for table_name, table_data in schema_data.items():
            for fk in table_data["foreign_keys"]:
                foreign_keys.append(
                    f"{table_name}.{fk['column']}={fk['foreign_table']}.{fk['foreign_column']}"
                )
        
        return "\n".join(result + foreign_keys)