from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ParsedSQL:
    query_type: str  # SELECT/INSERT/UPDATE/DELETE
    tables: List[str]
    columns: List[str]
    conditions: List[str]
    joins: List[Dict[str, str]]
    limit: Optional[int] = None
    group_by: Optional[List[str]] = None
    order_by: Optional[List[Dict[str, str]]] = None  # {column: str, order: 'ASC'/'DESC'}

class BaseSQLParser(ABC):
    @abstractmethod
    def parse(self, sql: str) -> ParsedSQL:
        """将SQL语句解析为结构化对象"""
        pass

    @abstractmethod
    def reconstruct(self, parsed: ParsedSQL) -> str:
        """将结构化对象重建为SQL语句"""
        pass