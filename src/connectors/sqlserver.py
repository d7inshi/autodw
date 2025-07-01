# import pyodbc
# from typing import List, Dict, Tuple, Optional, Union
# from .base import BaseConnector

# class SQLServerConnector(BaseConnector):
#     """SQL Server数据库连接器实现"""
#     def __init__(self, connection_string: str):
#         super().__init__(connection_string)
#         self.config = self._parse_connection_string(connection_string)
    
#     def _parse_connection_string(self, conn_str: str) -> Dict[str, str]:
#         """解析连接字符串为字典（兼容完整连接字符串或关键参数）[6,7](@ref)"""
#         if ";" in conn_str and "=" in conn_str:
#             # 直接使用完整连接字符串
#             return {"connection_string": conn_str}
#         else:
#             # 简写模式（示例：server:port/database?user=xxx&password=xxx）
#             parts = conn_str.split("/")
#             server_port, db_user = parts[0], parts[1]
#             server, port = server_port.split(":") if ":" in server_port else (server_port, "1433")
#             db, auth = db_user.split("?")
#             user = auth.split("&")[0].split("=")[1]
#             password = auth.split("&")[1].split("=")[1]
#             return {
#                 'server': server,
#                 'port': port,
#                 'database': db,
#                 'user': user,
#                 'password': password
#             }

#     def connect(self) -> bool:
#         """建立数据库连接[10](@ref)"""
#         try:
#             if "connection_string" in self.config:
#                 self.connection = pyodbc.connect(self.config["connection_string"])
#             else:
#                 conn_str = (
#                     f"DRIVER={{ODBC Driver 17 for SQL Server}};"
#                     f"SERVER={self.config['server']},{self.config['port']};"
#                     f"DATABASE={self.config['database']};"
#                     f"UID={self.config['user']};"
#                     f"PWD={self.config['password']};"
#                 )
#                 self.connection = pyodbc.connect(conn_str)
#             self._log_success("Connection")
#             return True
#         except pyodbc.Error as e:
#             self._log_error("Connection", e)
#             return False

#     def disconnect(self):
#         if self.connection:
#             self.connection.close()
#             self._log_success("Disconnection")

#     def get_tables(self) -> List[str]:
#         """获取当前数据库所有表名（排除系统表）[5](@ref)"""
#         try:
#             cursor = self.connection.cursor()
#             cursor.execute("""
#                 SELECT TABLE_NAME 
#                 FROM INFORMATION_SCHEMA.TABLES 
#                 WHERE TABLE_TYPE = 'BASE TABLE'
#                 AND TABLE_CATALOG = ?
#             """, self.config['database'])
#             return [row[0] for row in cursor.fetchall()]
#         except pyodbc.Error as e:
#             self._log_error("Get tables", e)
#             return []

#     def get_columns(self, table_name: str) -> List[Dict[str, Union[str, bool, None]]]:
#         """获取表结构信息（包含主键标识）[5](@ref)"""
#         try:
#             # 先获取主键列名集合
#             primary_keys = set(self.get_primary_keys(table_name))
            
#             cursor = self.connection.cursor()
#             cursor.execute("""
#                 SELECT 
#                     COLUMN_NAME,
#                     DATA_TYPE,
#                     IS_NULLABLE,
#                     COLUMN_DEFAULT
#                 FROM INFORMATION_SCHEMA.COLUMNS 
#                 WHERE TABLE_NAME = ?
#                 ORDER BY ORDINAL_POSITION
#             """, table_name)
            
#             columns = []
#             for row in cursor.fetchall():
#                 columns.append({
#                     'name': row.COLUMN_NAME,
#                     'type': row.DATA_TYPE.upper(),
#                     'nullable': row.IS_NULLABLE == 'YES',
#                     'primary_key': row.COLUMN_NAME in primary_keys,
#                     'default': row.COLUMN_DEFAULT
#                 })
#             return columns
#         except pyodbc.Error as e:
#             self._log_error(f"Get columns for {table_name}", e)
#             return []

#     def get_primary_keys(self, table_name: str) -> List[str]:
#         """获取主键列名列表（按索引顺序）[5](@ref)"""
#         try:
#             cursor = self.connection.cursor()
#             cursor.execute("""
#                 SELECT KU.COLUMN_NAME
#                 FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TC
#                 JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KU
#                   ON TC.CONSTRAINT_NAME = KU.CONSTRAINT_NAME
#                 WHERE TC.TABLE_NAME = ?
#                   AND TC.CONSTRAINT_TYPE = 'PRIMARY KEY'
#                 ORDER BY KU.ORDINAL_POSITION
#             """, table_name)
#             return [row[0] for row in cursor.fetchall()]
#         except pyodbc.Error as e:
#             self._log_error(f"Get primary keys for {table_name}", e)
#             return []

#     def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
#         """获取外键关系[5](@ref)"""
#         try:
#             cursor = self.connection.cursor()
#             cursor.execute("""
#                 SELECT 
#                     KCU.COLUMN_NAME AS 'column',
#                     RC.UNIQUE_CONSTRAINT_TABLE_NAME AS 'foreign_table',
#                     RC.UNIQUE_CONSTRAINT_COLUMN_NAME AS 'foreign_column'
#                 FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS RC
#                 JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU
#                   ON KCU.CONSTRAINT_NAME = RC.CONSTRAINT_NAME
#                 WHERE KCU.TABLE_NAME = ?
#             """, table_name)
            
#             return [
#                 {
#                     'column': row.column,
#                     'foreign_table': row.foreign_table,
#                     'foreign_column': row.foreign_column
#                 } 
#                 for row in cursor.fetchall()
#             ]
#         except pyodbc.Error as e:
#             self._log_error(f"Get foreign keys for {table_name}", e)
#             return []

#     def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Tuple]:
#         """执行SQL查询并返回字典列表结果"""
#         try:
#             cursor = self.connection.cursor()
#             cursor.execute(query, params or ())
            
#             # 转换为字典格式（列名作为键）
#             if cursor.description:
#                 columns = [col[0] for col in cursor.description]
#                 return [dict(zip(columns, row)) for row in cursor.fetchall()]
#             return []
#         except pyodbc.Error as e:
#             self._log_error(f"Execute query: {query}", e)
#             return []
    
#     def get_table_schema(self, table_name: str) -> Dict:
#         """获取完整表结构描述（包含主键和外键）"""
#         return {
#             'table': table_name,
#             'columns': self.get_columns(table_name),
#             'primary_keys': self.get_primary_keys(table_name),
#             'foreign_keys': self.get_foreign_keys(table_name)
#         }
    
#     def get_database_schema(self) -> Dict[str, Dict]:
#         """获取整个数据库模式描述"""
#         schema = {}
#         for table in self.get_tables():
#             schema[table] = self.get_table_schema(table)
#         return schema