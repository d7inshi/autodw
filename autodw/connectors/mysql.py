import mysql.connector
from typing import List, Dict, Tuple, Optional, Union
from .base import BaseConnector
from mysql.connector import Error
from mysql.connector.cursor import MySQLCursor

class MySQLConnector(BaseConnector):
    """MySQL数据库连接器实现"""
    def __init__(self, connection_string: str):
        """
        MySQL连接器构造函数
        :param connection_string: MySQL连接字符串 (格式: mysql://user:password@host:port/database)
        """
        super().__init__(connection_string)
        self.config = self._parse_connection_string(connection_string)
        
    def _parse_connection_string(self, conn_str: str) -> Dict[str, str]:
        """解析MySQL连接字符串为配置字典"""
        try:
            # 移除协议前缀 (mysql://)
            parts = conn_str.split("://")[1].split("@")
            user_pass, host_db = parts[0], parts[1]
            
            # 提取用户名和密码
            user, password = user_pass.split(":")
            
            # 提取主机、端口和数据库
            host_port, database = host_db.split("/")
            host, port = host_port.split(":") if ":" in host_port else (host_port, "3306")
            
            return {
                'host': host,
                'user': user,
                'password': password,
                'database': database,
                'port': int(port)
            }
        except Exception as e:
            raise ValueError(f"无效的连接字符串: {conn_str}") from e

    def connect(self) -> bool:
        """建立MySQL数据库连接[6,9](@ref)"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                port=self.config['port']
            )
            self._log_success("Connection")
            return True
        except Error as e:
            self._log_error("Connection", e)
            return False

    def disconnect(self):
        """关闭数据库连接[9](@ref)"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self._log_success("Disconnection")

    def get_tables(self) -> List[str]:
        """获取所有表名[9](@ref)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s
            """, (self.config['database'],))
            return [row[0] for row in cursor.fetchall()]
        except Error as e:
            self._log_error("Get tables", e)
            return []

    def get_columns(self, table_name: str) -> List[Dict[str, Union[str, bool, None]]]:
        """获取表结构信息[9](@ref)"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    COLUMN_NAME AS `name`,
                    COLUMN_TYPE AS `type`,
                    IS_NULLABLE = 'YES' AS `nullable`,
                    COLUMN_KEY = 'PRI' AS `primary_key`,
                    COLUMN_DEFAULT AS `default`
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """, (self.config['database'], table_name))
            
            columns = []
            for row in cursor.fetchall():
                # 标准化类型名称
                col_type = row['type'].upper().split('(')[0]
                columns.append({
                    'name': row['name'],
                    'type': col_type,
                    'nullable': bool(row['nullable']),
                    'primary_key': bool(row['primary_key']),
                    'default': row['default']
                })
            return columns
        except Error as e:
            self._log_error(f"Get columns for {table_name}", e)
            return []

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """获取外键关系[9](@ref)"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    COLUMN_NAME AS `column`,
                    REFERENCED_TABLE_NAME AS `foreign_table`,
                    REFERENCED_COLUMN_NAME AS `foreign_column`
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE 
                    TABLE_SCHEMA = %s AND
                    TABLE_NAME = %s AND
                    REFERENCED_TABLE_NAME IS NOT NULL
            """, (self.config['database'], table_name))
            
            return cursor.fetchall()
        except Error as e:
            self._log_error(f"Get foreign keys for {table_name}", e)
            return []

    def get_primary_keys(self, table_name: str) -> List[str]:
        """获取主键列名列表（按顺序）[9](@ref)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SHOW KEYS FROM `{table_name}` WHERE Key_name = 'PRIMARY'")
            
            # 按主键顺序排序
            primary_keys = [(row[4], row[2]) for row in cursor.fetchall()]  # (seq_in_index, column_name)
            primary_keys.sort(key=lambda x: x[0])
            
            return [col for _, col in primary_keys]
        except Error as e:
            self._log_error(f"Get primary keys for {table_name}", e)
            return []

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Tuple]:
        """执行SQL查询并返回结果[6,9](@ref)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            
            # 获取列名用于构建字典格式结果
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            return []
        except Error as e:
            self._log_error(f"Execute query: {query}", e)
            return []
    
    def get_table_schema(self, table_name: str) -> Dict:
        """获取完整表结构描述（包含主键信息）"""
        return {
            'table': table_name,
            'columns': self.get_columns(table_name),
            'primary_keys': self.get_primary_keys(table_name),
            'foreign_keys': self.get_foreign_keys(table_name)
        }
    
    def get_database_schema(self) -> Dict[str, Dict]:
        """获取整个数据库的模式描述"""
        schema = {}
        for table in self.get_tables():
            schema[table] = self.get_table_schema(table)
        return schema