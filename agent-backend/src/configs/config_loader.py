import yaml
import os

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

def load_config(
        config_path: str,
        encoding: str = 'utf-8'
) -> dict:
    with open(config_path, 'r', encoding=encoding) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config

chroma_config = load_config(config_path=get_abstract_path('src/configs/chroma.yaml'))
prompt_config = load_config(config_path=get_abstract_path('src/configs/prompt.yaml'))

# 兼容旧代码的别名
vector_store_config = chroma_config

if __name__ == '__main__':

    print(chroma_config)
    print(prompt_config)
