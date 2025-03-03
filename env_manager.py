import os
import re
import logging

logger = logging.getLogger(__name__)

def update_env_file(key, value):
    """
    更新.env文件中的环境变量
    如果变量存在，则更新其值；如果不存在，则添加新变量
    """
    env_path = '.env'
    
    # 检查.env文件是否存在
    if not os.path.exists(env_path):
        logger.error(f"错误：找不到{env_path}文件")
        return False
    
    # 读取当前.env文件内容
    with open(env_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # 查找并更新指定的键值对
    key_pattern = re.compile(f'^{key}\s*=.*$')
    key_exists = False
    
    for i, line in enumerate(lines):
        if key_pattern.match(line):
            lines[i] = f"{key} = '{value}'\n"
            key_exists = True
            break
    
    # 如果键不存在，则添加到文件末尾
    if not key_exists:
        # 确保文件末尾有换行符
        if lines and not lines[-1].endswith('\n'):
            lines.append('\n')
        lines.append(f"{key} = '{value}'\n")
    
    # 写回文件
    with open(env_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)
    
    logger.info(f"已更新.env文件：{key} = '{value}'")
    return True