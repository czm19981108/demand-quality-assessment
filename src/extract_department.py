"""部门/系统信息提取模块"""
import re
import yaml
from typing import Optional, Tuple, Dict, List
from loguru import logger

from .config import config


def extract_from_yaml_frontmatter(content: str) -> Optional[Tuple[str, str]]:
    """从 YAML frontmatter 中提取部门/系统信息

    支持的格式:
    ---
    department: 电商
    system: 订单系统
    ---
    """
    # 检查是否包含 YAML frontmatter
    if not content.strip().startswith('---'):
        return None

    # 找到第二个 ---
    first_newline = content.find('\n')
    if first_newline == -1:
        return None

    second_dash = content.find('\n---', first_newline + 1)
    if second_dash == -1:
        return None

    # 提取 YAML 内容
    yaml_content = content[3:second_dash].strip()

    try:
        data = yaml.safe_load(yaml_content)
        if not data:
            return None

        department = data.get('department')
        system = data.get('system')

        if department or system:
            logger.info(f"从 YAML frontmatter 提取: department={department}, system={system}")
            return (department, system)

    except yaml.YAMLError as e:
        logger.warning(f"YAML 解析失败: {e}")

    return None


def extract_by_keywords(content: str, title: str = "") -> Optional[str]:
    """通过关键词匹配提取部门信息

    按优先级:
    1. 从标题中匹配
    2. 从内容中匹配
    """
    # 合并标题和内容进行匹配
    search_text = f"{title}\n{content}"
    keywords = config.department_keywords

    matched_department = None
    max_matches = 0

    for dept, words in keywords.items():
        match_count = sum(1 for word in words if word in search_text)
        if match_count > max_matches:
            max_matches = match_count
            matched_department = dept

    if matched_department and max_matches >= 2:  # 至少匹配2个关键词
        logger.info(f"通过关键词匹配到部门: {matched_department}, 匹配词数={max_matches}")
        return matched_department

    return None


def extract_department(
    content: str,
    title: str = "",
    department: Optional[str] = None,
    system: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """提取部门/系统信息

    支持三种方式，按优先级:
    1. YAML frontmatter 元数据
    2. 关键词匹配
    3. 用户手动指定

    Args:
        content: 需求文档内容
        title: 需求标题（可选）
        department: 用户指定的部门（可选）
        system: 用户指定的系统（可选）

    Returns:
        (department, system) 元组
    """
    # 优先级1: 用户手动指定
    if department or system:
        logger.info(f"使用用户指定的部门/系统: department={department}, system={system}")
        return (department, system)

    # 优先级2: YAML frontmatter
    result = extract_from_yaml_frontmatter(content)
    if result:
        return result

    # 优先级3: 关键词匹配
    matched_dept = extract_by_keywords(content, title)
    if matched_dept:
        return (matched_dept, None)

    logger.info("未能提取到部门/系统信息")
    return (None, None)


def get_department_keywords() -> Dict[str, List[str]]:
    """获取部门关键词配置"""
    return config.department_keywords