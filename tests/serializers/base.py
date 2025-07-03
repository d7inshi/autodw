from src.connectors.sqlite import SQLiteConnector
from src.serializers.base import DatabaseSchemaSerializer
import os
import logging

# 设置日志配置，便于查看测试详情
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Test")

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

def run_tests(db_path):
    """在单个数据库上运行所有测试"""
    logger.info(f"\n{'='*50}\n开始测试数据库: {db_path}\n{'='*50}")
    
    # 初始化连接
    db = SQLiteConnector(db_path)

    
    # 1. 测试连接
    with db:
        # 初始化模式序列转换器
        serial = DatabaseSchemaSerializer(connector=db, serializer_type="mschema")
        base_seq = serial.generate()
        logger.info(f"base sequence: {base_seq}")
    # 6. 测试断开连接
    test_disconnection(db)  # 在上下文管理器外部测试断开连接
    
    logger.info(f"\n{'='*50}\n测试完成: {db_path}\n{'='*50}\n")
    return True

if __name__ == "__main__":
    sqlite_root_path = "tests/resource/sqlite"
    
    # 遍历所有SQLite数据库文件进行测试
    for file in os.listdir(sqlite_root_path):
        if not file.endswith(".sqlite"): 
            continue
            
        db_path = os.path.join(sqlite_root_path, file)
        try:
            logger.info(f"\n{'#'*60}\n开始测试数据库文件: {file}\n{'#'*60}")
            run_tests(db_path)
        except Exception as e:
            logger.error(f"测试失败 {file}: {str(e)}", exc_info=True)