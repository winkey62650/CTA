import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logger(name='CTA_Backtest', log_file='backtest.log', level=logging.INFO):
    """
    配置日志系统
    :param name: logger名称
    :param log_file: 日志文件名 (保存在 logs/ 目录下)
    :param level: 日志级别
    :return: logger对象
    """
    # 1. 创建 logs 目录
    root_path = Path(__file__).parent.parent
    log_path = root_path / 'logs'
    log_path.mkdir(exist_ok=True)
    
    log_file_path = log_path / log_file

    # 2. 获取 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 3. 设置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 4. 文件 Handler (支持回滚，最大 10MB，保留 5 个文件)
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # 5. 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # 6. 添加 Handler
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
