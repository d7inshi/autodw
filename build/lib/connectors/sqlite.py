import sqlite3
from typing import List, Dict, Tuple, Optional
from .base import BaseConnector

class SQLiteConnector(BaseConnector):
    """SQLite数据库连接器实现"""
    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.db_path = db_path
    
    def connect(self) -> bool:
        try:
            self.connection = sqlite3.connect(self.db_path)
            # 启用外键约束支持
            self.connection.execute("PRAGMA foreign_keys = ON")
            self._log_success("Connection")
            return True
        except sqlite3.Error as e:
            self._log_error("Connection", e)
            return False
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            self._log_success("Disconnection")
    
    def get_tables(self) -> List[str]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
            """)
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self._log_error("Get tables", e)
            return []
    
    def get_columns(self, table_name: str) -> List[Dict[str, str]]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row[1],
                    'type': row[2].upper(),
                    'nullable': not bool(row[3]),
                    'primary_key': bool(row[5]),
                    'default': row[4]
                })
            return columns
        except sqlite3.Error as e:
            self._log_error(f"Get columns for {table_name}", e)
            return []
    
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            
            foreign_keys = []
            for row in cursor.fetchall():
                foreign_keys.append({
                    'column': row[3],  # 当前表列名
                    'foreign_table': row[2],  # 外联表名
                    'foreign_column': row[4]  # 外联列名
                })
            return foreign_keys
        except sqlite3.Error as e:
            self._log_error(f"Get foreign keys for {table_name}", e)
            return []

    def get_primary_keys(self, table_name: str) -> List[str]:
        """获取主键列名列表（按主键顺序）[7,9](@ref)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            
            # 收集所有主键列及其顺序
            primary_key_cols = []
            for row in cursor.fetchall():
                pk_index = row[5]  # 主键顺序值
                if pk_index > 0:
                    primary_key_cols.append((pk_index, row[1]))  # (顺序, 列名)
            
            # 按主键顺序排序并返回列名列表
            primary_key_cols.sort(key=lambda x: x[0])
            return [col for _, col in primary_key_cols]
        except sqlite3.Error as e:
            self._log_error(f"Get primary keys for {table_name}", e)
            return []
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Tuple]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except sqlite3.Error as e:
            self._log_error(f"Execute query: {query}", e)
            return []
    
    def get_table_schema(self, table_name: str) -> Dict:
        """获取完整表结构描述（包含主键信息）"""
        return {
            'table': table_name,
            'columns': self.get_columns(table_name),
            'primary_keys': self.get_primary_keys(table_name),  # 新增主键信息
            'foreign_keys': self.get_foreign_keys(table_name)
        }
    
    def get_database_schema(self) -> Dict[str, Dict]:
        """获取整个数据库的模式描述"""
        schema = {}
        for table in self.get_tables():
            schema[table] = self.get_table_schema(table)
        return schema