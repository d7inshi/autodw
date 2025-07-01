from llm_integration.connector import LLMConnector
from sqlparse.llm_parser import LLMSQLParser

# 初始化连接器
connector = LLMConnector(api_key="your_api_key")

# 解析SQL
parser = LLMSQLParser(connector)
parsed = parser.parse("SELECT * FROM users WHERE age > 30")

print(parsed.tables)  # 输出: ['users']