from abc import ABC, abstractmethod
import logging
from typing import Dict, List, Tuple, Optional

class BaseConnector(ABC):
    """数据库连接器抽象基类，定义统一接口规范"""
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
        self.logger = logging.getLogger("autodw.connectors")
        self.logger.setLevel(logging.INFO)
        
    @abstractmethod
    def connect(self) -> bool:
        """建立数据库连接"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """关闭数据库连接"""
        pass
    
    @abstractmethod
    def get_tables(self) -> List[str]:
        """获取所有表名"""
        pass
    
    @abstractmethod
    def get_columns(self, table_name: str) -> List[Dict[str, str]]:
        """
        获取表结构信息
        :return: [{
            'name': 列名, 
            'type': 数据类型, 
            'nullable': 是否可为空,
            'primary_key': 是否主键,
            'default': 默认值
        }]
        """
        pass
    
    @abstractmethod
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """
        获取外键关系
        :return: [{
            'column': 当前表列名,
            'foreign_table': 外联表名,
            'foreign_column': 外联列名
        }]
        """
        pass
        
    @abstractmethod
    def get_primary_keys(self, table_name: str) -> List[str]:
        """获取表的主键列名列表（按顺序）"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Tuple]:
        """执行SQL查询并返回结果"""
        pass
    
    def __enter__(self):
        """支持上下文管理器"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动关闭连接"""
        self.disconnect()
    
    def _log_success(self, operation: str):
        self.logger.info(f"{operation} executed successfully")
    
    def _log_error(self, operation: str, error: Exception):
        self.logger.error(f"{operation} failed: {str(error)}")