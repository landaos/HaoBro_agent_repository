import logging
import os
import sys
from datetime import datetime

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
logs_dir=os.path.join(project_dir,'logs')
os.makedirs(logs_dir,exist_ok=True)

DEFAULT_LOGGING_FORMAT = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_logger(name: str='AGENT', log_file: str = None, console_level: str = logging.INFO,file_level: str = logging.DEBUG) -> logging.Logger:
    """
    获取日志记录器
    :param name: 日志记录器名称
    :param log_file: 日志文件名
    :param console_level: 控制台日志级别
    :param file_level: 文件日志级别
    :return: 日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(DEFAULT_LOGGING_FORMAT)
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)

    if log_file is None:
        log_file=f'{name}_{datetime.now().strftime("%Y%m%d%H%M%S")}.log'

    logs_dir=os.path.join(project_dir,'logs')
    os.makedirs(logs_dir,exist_ok=True)

    file_handler = logging.FileHandler(os.path.join(logs_dir,log_file), encoding='utf-8')
    file_handler.setFormatter(DEFAULT_LOGGING_FORMAT)
    file_handler.setLevel(file_level)
    logger.addHandler(file_handler)

    return logger

logger = get_logger()


if __name__ == '__main__':
    # 测试创建日志文件
    logger = get_logger(log_file='test.log')
    print(f"项目根目录: {project_dir}")
    print(f"日志目录: {logs_dir}")
    logger.info('这是一条info日志')
    logger.debug('这是一条debug日志')
    logger.error('这是一条error日志')
    logger.warning('这是一条warning日志')
    print("日志测试完成，请检查logs目录是否创建")