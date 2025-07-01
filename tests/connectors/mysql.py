# 创建连接器
connector = MySQLConnector("mysql://user:password@localhost:3306/mydb")

# 使用上下文管理器
with connector:
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