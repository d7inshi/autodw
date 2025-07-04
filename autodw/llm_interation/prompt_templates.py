# 思维链(CoT)SQL解析模板
COT_SQL_PARSE_TEMPLATE = """**Task**: Parse the following SQL query into structured components using Chain-of-Thought reasoning.

**Step-by-Step Instructions**:
1. Identify query type (SELECT/INSERT/UPDATE/DELETE)
2. Extract all table names
3. Identify all columns referenced (both selected and conditioned)
4. Parse JOIN conditions including table relationships
5. Extract WHERE/HAVING conditions
6. Identify GROUP BY and ORDER BY clauses
7. Detect LIMIT/OFFSET clauses

**Output Format**:
```json
{{
  "query_type": "<type>",
  "tables": ["table1", ...],
  "columns": ["col1", ...],
  "conditions": ["col1 > value", ...],
  "joins": [
    {{"left_table": "t1", "right_table": "t2", "condition": "t1.id = t2.fk"}}
  ],
  "group_by": ["col1", ...],
  "order_by": [{{"column": "col1", "order": "ASC/DESC"}}],
  "limit": <number>
}}