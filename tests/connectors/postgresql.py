# 创建连接器
connector = PostgreSQLConnector("postgresql://user:password@localhost:5432/mydb")

# 使用上下文管理器
with connector:
    # 设置schema
    connector.set_schema("my_schema")
    
    # 获取所有表
    print("Tables:", connector.get_tables())
    
    # 获取用户表结构
    users_schema = connector.get_table_schema('users')
    print("Users schema:", users_schema)
    
    # 执行参数化查询
    results = connector.execute_query(
        "SELECT * FROM users WHERE age > %s AND status = %s",
        (25, 'active')
    )
    print("Query results:", results)
    
    # 获取整个数据库模式
    full_schema = connector.get_database_schema()
    print("Database schema:", full_schema)