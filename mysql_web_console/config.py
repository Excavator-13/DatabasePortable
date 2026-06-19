# 配置读取模块：从 .env 文件加载 MySQL 连接参数
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库连接配置字典，各字段含义及默认值：
#   host     - MySQL 服务器地址，默认 127.0.0.1
#   port     - MySQL 服务器端口，默认 3306
#   user     - 数据库用户名，默认 root
#   password - 数据库密码，默认空字符串
#   db       - 目标数据库名，默认空字符串（需在 .env 中指定）
db_config = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "db": os.getenv("DB_NAME", ""),
}