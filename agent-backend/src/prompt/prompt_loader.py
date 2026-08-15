import sys
import os

from src.configs.config_loader import prompt_config
from src.logger.logger import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def get_project_root() -> str:
    """
    获取项目根目录
    :return: 项目根目录路径
    """
    # 从当前文件所在目录向上两级（app/utils -> app -> backend）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(current_dir)
    project_root = os.path.dirname(src_dir)
    return project_root

def get_abstract_path(relative_path: str) -> str:
    """
    根据传入的相对路径，获取项目根目录下的绝对路径
    :param relative_path: 相对项目根目录的路径
    :return: 绝对路径
    """
    project_path = get_project_root()
    # 确保路径格式正确，处理不同操作系统的路径分隔符
    abstract_path = os.path.normpath(os.path.join(project_path, relative_path))
    return abstract_path

def load_prompt(prompt_type: str='agent_prompt') -> str:
    try:
        if prompt_type not in prompt_config:
            logger.error(f"【prompt】提示词配置中不存在类型: {prompt_type}")
            raise KeyError(f"不存在提示词类型: {prompt_type}")

        prompt_path=get_abstract_path(prompt_config[prompt_type])
    except Exception as e:
        logger.error(f"【prompt】提示词类型校验异常 | {e}")
        raise e
    
    try:
        return open(prompt_path, encoding='utf-8').read()
    except Exception as e:
        logger.error(f"【prompt】提示词文件加载失败 | path={prompt_path} | {e}")
        raise e
   
    
