# 使用上下文管理器自动处理连接
with SQLiteConnector('example.db') as db:
    # 获取所有表名
    print("Tables:", db.get_tables())
    
    # 获取特定表结构
    users_schema = db.get_table_schema('users')
    print("Users schema:", users_schema)
    
    # 执行自定义查询
    results = db.execute_query("SELECT * FROM users WHERE age > ?", (25,))
    print("Query results:", results)