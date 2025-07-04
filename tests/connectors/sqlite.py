from autodw.connectors.sqlite import SQLiteConnector
import os
import logging

# 设置日志配置，便于查看测试详情
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SQLiteConnectorTest")

def is_connection_active(conn):
    """检查连接是否真正关闭"""
    if conn is None:
        return False
    try:
        conn.execute("SELECT 1")
        return True
    except sqlite3.ProgrammingError:
        return False
    except AttributeError:
        return False
    except Exception:
        return False

def test_connection(db: SQLiteConnector):
    assert db.connect() is True, "连接数据库失败"
    assert db.connection is not None, "连接对象不应为None"
    logger.info(f"连接测试成功: {db.db_path}")
    return True

def test_disconnection(db: SQLiteConnector):
    """测试断开连接功能"""
    db.disconnect()
    
    # 验证连接对象状态
    assert db.connection is None, "断开连接后连接对象应被置为None"
    
    # 验证连接实际不可用
    assert not is_connection_active(db.connection), "连接对象未正确关闭"
    
    logger.info("断开连接测试成功")
    return True

def test_get_tables(db: SQLiteConnector):
    """测试获取表名功能"""
    tables = db.get_tables()
    assert isinstance(tables, list), "应返回列表"
    logger.info(f"获取表名: {tables}")
    return tables

def test_get_columns(db: SQLiteConnector, table_name: str):
    """测试获取列信息功能"""
    columns = db.get_columns(table_name)
    assert isinstance(columns, list), "应返回列表"
    logger.info(f"{table_name}表结构: {columns}")
    return columns

def test_get_primary_keys(db: SQLiteConnector, table_name: str):
    """测试获取主键功能"""
    pks = db.get_primary_keys(table_name)
    assert isinstance(pks, list), "应返回列表"
    logger.info(f"{table_name}表主键: {pks}")
    return pks

def test_get_foreign_keys(db: SQLiteConnector, table_name: str):
    """测试获取外键功能"""
    fks = db.get_foreign_keys(table_name)
    assert isinstance(fks, list), "应返回列表"
    logger.info(f"{table_name}表外键: {fks}")
    return fks

def test_execute_query(db: SQLiteConnector):
    """测试执行查询功能"""
    # 测试简单查询
    result = db.execute_query("SELECT 1 + 1")
    logger.info(f"执行查询 'SELECT 1 + 1' 结果: {result}")
    
    # 测试带参数查询
    result = db.execute_query("SELECT ? + ?", (3, 4))
    logger.info(f"执行查询 'SELECT ? + ?' 参数(3,4) 结果: {result}")
    
    # 测试表数据查询
    tables = db.get_tables()
    if tables:
        table_name = tables[0]  # 使用第一个表测试
        result = db.execute_query(f"SELECT COUNT(*) FROM {table_name}")
        logger.info(f"执行查询 'SELECT COUNT(*) FROM {table_name}' 结果: {result}")
    
    return True

def test_table_schema(db: SQLiteConnector, table_name: str):
    """测试获取表完整模式功能"""
    schema = db.get_table_schema(table_name)
    assert isinstance(schema, dict), "应返回字典"
    logger.info(f"{table_name}表完整模式: {schema}")
    return schema

def test_database_schema(db: SQLiteConnector):
    """测试获取数据库完整模式功能"""
    schema = db.get_database_schema(format="spider", include_samples=True, sample_method="random", exclude_tables=["sectors", "industries", "assets_products"], exclude_columns={"performance_metrics":["metric_id"], "users": ["user_id"]})
    assert isinstance(schema, dict), "应返回字典"
    logger.info(f"数据库模式包含 {len(schema)} 张表")
    logger.info(f"数据库模式JSON: {schema}")
    return schema

def run_tests(db_path):
    """在单个数据库上运行所有测试"""
    logger.info(f"\n{'='*50}\n开始测试数据库: {db_path}\n{'='*50}")
    
    # 初始化连接
    db = SQLiteConnector(db_path)
    
    # 1. 测试连接
    with db:
        test_connection(db)
        
        # 2. 测试获取表名
        tables = test_get_tables(db)
        
        # 3. 测试表相关功能
        for table in tables:
            # 跳过系统表
            if table.startswith("sqlite_"): 
                logger.info(f"跳过系统表: {table}")
                continue
            
            logger.info(f"\n{'='*20} 测试表 {table} {'='*20}")
            
            # 3.1 测试列信息
            test_get_columns(db, table)
            
            # 3.2 测试主键
            test_get_primary_keys(db, table)
            
            # 3.3 测试外键
            test_get_foreign_keys(db, table)
            
            # 3.4 测试表完整模式
            test_table_schema(db, table)
        
        # 4. 测试查询功能
        test_execute_query(db)
        
        # 5. 测试数据库模式
        test_database_schema(db)
    
    # 6. 测试断开连接
    test_disconnection(db)  # 在上下文管理器外部测试断开连接
    
    logger.info(f"\n{'='*50}\n测试完成: {db_path}\n{'='*50}\n")
    return True

if __name__ == "__main__":
    sqlite_root_path = "tests/resource/sqlite"
    
    # 遍历所有SQLite数据库文件进行测试
    for index, file in enumerate(os.listdir(sqlite_root_path)):
        if index > 0:
            break
        if not file.endswith(".sqlite"): 
            continue
            
        db_path = os.path.join(sqlite_root_path, file)
        try:
            logger.info(f"\n{'#'*60}\n开始测试数据库文件: {file}\n{'#'*60}")
            run_tests(db_path)
        except Exception as e:
            logger.error(f"测试失败 {file}: {str(e)}", exc_info=True)