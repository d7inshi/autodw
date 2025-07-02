import sqlite3
from typing import List, Dict, Tuple, Optional, Union
from .base import BaseConnector
import os
import re

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
            self.connection = None  # 关键修复：关闭后将连接置空
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
    
    def get_columns(
        self, 
        table_name: str, 
        include_samples: bool = False, 
        sample_size: int = 5, 
        sample_method: str = "random"
    ) -> List[Dict[str, any]]:
        """
        获取表列信息，可选包含采样值
        :param include_samples: 是否包含采样值
        :param sample_size: 采样数量
        :param sample_method: 采样方法 ("random" 或 "frequency")
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            
            columns = []
            for row in cursor.fetchall():
                col_info = {
                    'name': row[1],
                    'type': row[2].upper(),
                    'nullable': not bool(row[3]),
                    'primary_key': bool(row[5]),
                    'default': row[4]
                }
                # 添加采样值
                if include_samples and sample_size > 0:
                    try:
                        col_info['samples'] = self.sample_column_values(
                            table_name, 
                            col_info['name'], 
                            sample_size, 
                            sample_method
                        )
                    except Exception as e:
                        self._log_error(f"采样列 {table_name}.{col_info['name']} 失败", e)
                        col_info['samples'] = []
                columns.append(col_info)
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
        try:
            cursor = self.connection.cursor()
            # 1. 查找主键索引（名为 "sqlite_autoindex_<table>_<N>" 的索引）
            cursor.execute(f"PRAGMA index_list({table_name})")
            pk_index_name = None
            for row in cursor.fetchall():
                if row[1].startswith("sqlite_autoindex"):  # 自动生成的主键索引
                    pk_index_name = row[1]
                    break
            
            # 2. 若存在主键索引，提取其包含的列
            if pk_index_name:
                cursor.execute(f"PRAGMA index_info({pk_index_name})")
                # 按索引顺序排序（列在复合主键中的定义顺序）
                index_rows = sorted(cursor.fetchall(), key=lambda x: x[0])  # 按索引中的顺序号排序
                return [row[2] for row in index_rows]  # 返回列名
            
            # 3. 无主键索引时回退到 PRAGMA table_info
            cursor.execute(f"PRAGMA table_info({table_name})")
            primary_key_cols = []
            for row in cursor.fetchall():
                pk_index = row[5]
                if pk_index > 0:
                    primary_key_cols.append((pk_index, row[1]))
            primary_key_cols.sort(key=lambda x: x[0])
            return [col for _, col in primary_key_cols] if primary_key_cols else []
        
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
    
    def _extract_db_id(self) -> str:
        """从db_path解析数据库ID（去掉路径和扩展名）"""
        # 获取文件名（不带路径）
        filename = os.path.basename(self.db_path)
        
        # 移除扩展名（.sqlite或.db）[6,7](@ref)
        if filename.endswith(".sqlite"):
            return filename[:-7]  # 移除7个字符（.sqlite）
        elif filename.endswith(".db"):
            return filename[:-3]  # 移除3个字符（.db）
        else:
            return filename
    
    def get_table_schema(
        self, 
        table_name: str, 
        include_samples: bool = False, 
        sample_size: int = 5, 
        sample_method: str = "random"
    ) -> Dict:
        """
        获取完整表结构描述，可选包含采样值
        :param include_samples: 是否包含列采样值
        :param sample_size: 采样数量
        :param sample_method: 采样方法 ("random" 或 "frequency")
        """
        return {
            'table': table_name,
            'columns': self.get_columns(table_name, include_samples, sample_size, sample_method),
            'primary_keys': self.get_primary_keys(table_name),
            'foreign_keys': self.get_foreign_keys(table_name)
        }

    def sample_column_values(
        self, 
        table_name: str, 
        column_name: str, 
        sample_size: int, 
        sample_method: str = "random"
    ) -> List:
        """
        采样指定表的列值，支持随机采样和按频率采样
        :param table_name: 目标表名
        :param column_name: 目标列名
        :param sample_size: 采样数量
        :param sample_method: 采样方法 ("random" 或 "frequency")
        :return: 采样值列表
        """
        if sample_size <= 0:
            return []

        if sample_method not in ["random", "frequency"]:
            raise ValueError("采样方法必须是 'random' 或 'frequency'")

        try:
            cursor = self.connection.cursor()
            # 使用双引号包裹标识符，避免SQL关键字冲突
            if sample_method == "random":
                query = f'SELECT "{column_name}" FROM "{table_name}" ORDER BY RANDOM() LIMIT ?'
                cursor.execute(query, (sample_size,))
            else:  # frequency
                query = f'''
                    SELECT "{column_name}" 
                    FROM "{table_name}" 
                    GROUP BY "{column_name}" 
                    ORDER BY COUNT(*) DESC 
                    LIMIT ?
                '''
                cursor.execute(query, (sample_size,))
            
            return [row[0] for row in cursor.fetchall()]
        
        except sqlite3.Error as e:
            self._log_error(f"采样 {table_name}.{column_name} ({sample_method})", e)
            return []

    def _build_spider_format_schema(
        self, 
        include_samples: bool = False, 
        sample_size: int = 5, 
        sample_method: str = "random"
    ) -> Dict:
        """构建Spider格式的核心逻辑，支持动态扩展采样值"""
        db_id = self._extract_db_id()
        result = {
            "column_names_original": [[-1, "*"]],
            "column_types": ["text"],
            "db_id": db_id,
            "foreign_keys": [],
            "primary_keys": [],
            "table_names_original": []
        }
        
        # 若需采样值，则扩展字段
        if include_samples:
            result["column_samples"] = []  # 新增采样值字段

        # --- 公共逻辑（表结构/列信息/主外键）--- #
        tables = self.get_tables()
        result["table_names_original"] = tables
        table_name_to_idx = {table: idx for idx, table in enumerate(tables)}
        column_to_idx = {}
        ref_map = {}

        for table_idx, table in enumerate(tables):
            # 动态控制采样行为：include_samples传递至下层
            table_schema = self.get_table_schema(table, include_samples, sample_size, sample_method)
            
            for col_info in table_schema["columns"]:
                col_name = col_info["name"]
                col_type = col_info["type"].lower()
                
                col_idx = len(result["column_names_original"])
                result["column_names_original"].append([table_idx, col_name])
                result["column_types"].append(col_type)
                
                # 动态添加采样值（仅在include_samples=True时执行）
                if include_samples:
                    result["column_samples"].append({
                        "column_index": col_idx,
                        "values": col_info.get("samples", [])
                    })
                
                column_to_idx[(table_idx, col_name)] = col_idx
                ref_map[(table, col_name)] = col_idx
        # 处理主键
        for table_idx, table in enumerate(tables):
            table_schema = self.get_table_schema(table, include_samples, sample_size, sample_method)
            for pk_col in table_schema["primary_keys"]:
                if (table_idx, pk_col) in column_to_idx:
                    col_idx = column_to_idx[(table_idx, pk_col)]
                    result["primary_keys"].append(col_idx)
        
        # 处理外键
        for table_idx, table in enumerate(tables):
            table_schema = self.get_table_schema(table, include_samples, sample_size, sample_method)
            for fk in table_schema["foreign_keys"]:
                src_col = fk["column"]
                src_table = table
                tgt_col = fk["foreign_column"]
                tgt_table = fk["foreign_table"]
                
                # 查找源列和目标列的索引
                src_key = (src_table, src_col)
                tgt_key = (tgt_table, tgt_col)
                
                if src_key in ref_map and tgt_key in ref_map:
                    src_idx = ref_map[src_key]
                    tgt_idx = ref_map[tgt_key]
                    result["foreign_keys"].append([src_idx, tgt_idx])
        
        return result
    
    def get_database_schema(
        self, 
        format: str = "default", 
        include_samples: bool = False, 
        sample_size: int = 5, 
        sample_method: str = "random"
    ) -> Union[Dict[str, Dict], Dict]:
        if format == "default":
            schema = {}
            for table in self.get_tables():
                schema[table] = self.get_table_schema(
                    table, 
                    include_samples, 
                    sample_size, 
                    sample_method
                )
            return schema

        elif format in ("spider", "spider_with_samples"):
            # 统一入口：动态控制采样行为
            return self._build_spider_format_schema(
                include_samples=(format == "spider_with_samples"),  # 关键判断
                sample_size=sample_size,
                sample_method=sample_method
            )
        
        else:
            raise ValueError(f"Unsupported format: {format}")