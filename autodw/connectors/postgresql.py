import psycopg2
import psycopg2.extras
from typing import List, Dict, Tuple, Optional
from .base import BaseConnector

class PostgreSQLConnector(BaseConnector):
    """PostgreSQL数据库连接器实现"""
    def __init__(self, connection_string: str):
        """
        PostgreSQL连接器构造函数
        :param connection_string: PostgreSQL连接字符串 (格式: postgresql://user:password@host:port/database)
        """
        super().__init__(connection_string)
        self.config = self._parse_connection_string(connection_string)
        self.schema = "public"  # 默认使用public模式
        
    def _parse_connection_string(self, conn_str: str) -> Dict[str, str]:
        """解析PostgreSQL连接字符串为配置字典"""
        try:
            # 移除协议前缀 (postgresql://)
            parts = conn_str.split("://")[1].split("@")
            user_pass, host_db = parts[0], parts[1]
            
            # 提取用户名和密码
            user, password = user_pass.split(":")
            
            # 提取主机、端口和数据库
            if ":" in host_db:
                host_port, database = host_db.split("/")
                host, port = host_port.split(":")
            else:
                host = host_db.split("/")[0]
                database = host_db.split("/")[1]
                port = "5432"  # 默认端口
            
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
        """建立PostgreSQL数据库连接"""
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            # 获取当前连接使用的schema
            cursor = self.connection.cursor()
            cursor.execute("SELECT current_schema()")
            self.schema = cursor.fetchone()[0]
            cursor.close()
            
            self._log_success("Connection")
            return True
        except psycopg2.Error as e:
            self._log_error("Connection", e)
            return False

    def disconnect(self):
        """关闭数据库连接"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            self._log_success("Disconnection")

    def get_tables(self) -> List[str]:
        """获取所有表名"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_type = 'BASE TABLE'
            """, (self.schema,))
            return [row[0] for row in cursor.fetchall()]
        except psycopg2.Error as e:
            self._log_error("Get tables", e)
            return []

    def get_columns(self, table_name: str) -> List[Dict[str, Union[str, bool, None]]]:
        """获取表结构信息"""
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("""
                SELECT 
                    column_name AS name,
                    udt_name AS type,
                    is_nullable = 'YES' AS nullable,
                    column_default AS default
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (self.schema, table_name))
            
            # 获取主键信息
            primary_keys = self.get_primary_keys(table_name)
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row['name'],
                    'type': row['type'].upper(),
                    'nullable': bool(row['nullable']),
                    'primary_key': row['name'] in primary_keys,
                    'default': row['default']
                })
            return columns
        except psycopg2.Error as e:
            self._log_error(f"Get columns for {table_name}", e)
            return []

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """获取外键关系"""
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("""
                SELECT 
                    kcu.column_name AS column,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                WHERE 
                    tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
            """, (self.schema, table_name))
            
            return [
                {
                    'column': row['column'],
                    'foreign_table': row['foreign_table'],
                    'foreign_column': row['foreign_column']
                } 
                for row in cursor.fetchall()
            ]
        except psycopg2.Error as e:
            self._log_error(f"Get foreign keys for {table_name}", e)
            return []

    def get_primary_keys(self, table_name: str) -> List[str]:
        """获取主键列名列表（按顺序）"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    kcu.column_name
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                WHERE 
                    tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
                ORDER BY kcu.ordinal_position
            """, (self.schema, table_name))
            
            return [row[0] for row in cursor.fetchall()]
        except psycopg2.Error as e:
            self._log_error(f"Get primary keys for {table_name}", e)
            return []

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Tuple]:
        """执行SQL查询并返回结果"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            
            # 获取列名用于构建字典格式结果
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            return []
        except psycopg2.Error as e:
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
    
    def set_schema(self, schema: str):
        """设置当前连接使用的schema"""
        try:
            self.schema = schema
            if self.connection and not self.connection.closed:
                cursor = self.connection.cursor()
                cursor.execute(f"SET search_path TO {schema}")
                cursor.close()
                self._log_success(f"Set schema to {schema}")
        except psycopg2.Error as e:
            self._log_error(f"Set schema to {schema}", e)