from abc import ABC, abstractmethod
from typing import Dict, Any, Union, Type
from ..connectors.base import BaseConnector
import logging

logger = logging.getLogger("autodw.serializers")

class Serializer(ABC):
    """数据库模式序列化抽象基类"""
    
    @abstractmethod
    def serialize(self, schema_data: Dict[str, Any], db_name: str = "database") -> str:
        """
        将数据库模式数据序列化为特定格式
        
        参数:
            schema_data: 从连接器获取的原始模式数据
            db_name: 数据库名称
            
        返回:
            序列化后的字符串
        """
        pass


class BaseSerializer(Serializer):
    """BASE_FORMAT序列化器实现"""
    
    def serialize(self, schema_data: Dict[str, Any], db_name: str = "database") -> str:
        """
        生成BASE_FORMAT格式的序列化字符串:
          表名: 列1 (样例1, 样例2), 列2 (样例3, 样例4) | 外键关系
        """
        # 1. 处理表数据
        table_strings = []
        for table_name, table_data in schema_data.items():
            column_strings = []
            
            for column in table_data["columns"]:
                # 处理样例数据
                samples = ", ".join(map(str, column.get("samples", [])[:3]))
                column_strings.append(f"{column['name']} ({samples})")
            
            table_strings.append(f"{table_name} : {', '.join(column_strings)}")
        
        # 2. 处理外键关系
        foreign_keys = []
        for table_name, table_data in schema_data.items():
            for fk in table_data["foreign_keys"]:
                foreign_keys.append(
                    f"{table_name}.{fk['column']}={fk['foreign_table']}.{fk['foreign_column']}"
                )
        
        # 3. 组合所有部分
        return " | ".join(table_strings + foreign_keys)


class DatabaseSchemaSerializer:
    """直接连接数据库生成序列化输出的高级接口"""
    
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
        初始化数据库模式序列化器
        
        参数:
            connector: 数据库连接器实例
            serializer_class: 序列化类型 (BaseSerializer 或 MSchemaSerializer)
            db_name: 自定义数据库名称 (默认为连接器提取的ID)
            include_samples: 是否包含样例数据
            sample_size: 样例数据数量
            sample_method: 采样方法 ("random" 或 "frequency")
        """
        assert serializer_type in ["default", "mschema"], "序列化类型不存在"
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
        """建立数据库连接"""
        if not self.connector.connect():
            raise ConnectionError("数据库连接失败")
    
    def disconnect(self):
        """关闭数据库连接"""
        self.connector.disconnect()
    
    def generate(self) -> str:
        """获取序列化输出"""
        try:
            self.connect()
            
            # 获取数据库模式
            schema_data = self.connector.get_database_schema(
                format="default",
                include_samples=self.include_samples,
                sample_size=self.sample_size,
                sample_method=self.sample_method
            )
            
            # 确定数据库名称
            db_name = self.db_name or getattr(
                self.connector, "_extract_db_id", lambda: "database"
            )()
            
            # 使用指定序列化器生成输出
            serializer = self.serializer_class()
            return serializer.serialize(schema_data, db_name)
            
        except Exception as e:
            logger.error(f"序列化失败: {str(e)}")
            raise
        finally:
            self.disconnect()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

class MSchemaSerializer(Serializer):
    """M_SCHEMA_FORMAT序列化器实现"""
    
    def serialize(self, schema_data: Dict[str, Any], db_name: str = "database") -> str:
        """
        生成M_SCHEMA_FORMAT格式的序列化字符串:
          [DB_ID] db_name
          [Schema]
          #Table: table_name
          [
            (列定义),
            ...
          ]
          [Foreign keys]
          外键关系
        """
        # 1. 数据库标识头
        result = [f"[DB_ID] {db_name}", "[Schema]"]
        
        # 2. 处理每个表
        for table_name, table_data in schema_data.items():
            result.append(f"#Table: {table_name}")
            result.append("[")
            
            # 处理列
            for column in table_data["columns"]:
                # 构建列描述
                description_parts = []
                
                # 数据类型
                desc = f"{column['name']}: {column['type']}"
                
                # 主键标识
                if column['name'] in table_data["primary_keys"]:
                    desc += ", Primary Key"
                
                # 可空性
                desc += ", NOT NULL" if not column['nullable'] else ", NULL"
                
                # 外键映射
                for fk in table_data["foreign_keys"]:
                    if fk['column'] == column['name']:
                        desc += f", Maps to {fk['foreign_table']}({fk['foreign_column']})"
                
                # 添加示例数据
                samples = ", ".join(map(str, column.get("samples", [])[:3]))
                desc += f", Examples: [{samples}]"
                
                result.append(f"({desc})")
            
            result.append("]")
        
        # 3. 外键关系部分
        result.append("[Foreign keys]")
        foreign_keys = []
        for table_name, table_data in schema_data.items():
            for fk in table_data["foreign_keys"]:
                foreign_keys.append(
                    f"{table_name}.{fk['column']}={fk['foreign_table']}.{fk['foreign_column']}"
                )
        
        return "\n".join(result + foreign_keys)