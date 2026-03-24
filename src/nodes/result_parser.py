"""结果解析节点"""
import json
import re
from typing import Dict, Any, Optional, List
from loguru import logger

from ..models import DimensionScore


def parse_llm_output(llm_output: str, dimension: str) -> Optional[DimensionScore]:
    """解析 LLM 输出，提取评估结果

    Args:
        llm_output: LLM 原始输出
        dimension: 维度名称

    Returns:
        DimensionScore 对象，解析失败返回 None
    """
    if not llm_output:
        return None

    # 尝试提取 JSON
    json_str = extract_json(llm_output)
    if not json_str:
        logger.warning(f"无法从 LLM 输出中提取 JSON: dimension={dimension}")
        return None

    try:
        data = json.loads(json_str)

        # 提取字段
        score = data.get("score", 0)
        level = data.get("level", "未评估")
        issues = data.get("issues", [])
        suggestions = data.get("suggestions", [])
        evidence = data.get("evidence", "")

        # 验证和规范化
        if not isinstance(score, (int, float)):
            # 尝试从字符串中提取数字
            score_match = re.search(r'\d+', str(score))
            score = float(score_match.group()) if score_match else 0

        score = max(0, min(100, float(score)))  # 限制在 0-100

        # 规范化等级
        level = normalize_level(level)

        # 确保是列表
        if not isinstance(issues, list):
            issues = [str(issues)] if issues else []
        if not isinstance(suggestions, list):
            suggestions = [str(suggestions)] if suggestions else []

        return DimensionScore(
            dimension=dimension,
            score=score,
            level=level,
            issues=issues,
            suggestions=suggestions,
            evidence=evidence
        )

    except json.JSONDecodeError as e:
        logger.warning(f"JSON 解析失败: {e}, dimension={dimension}")
        return None
    except Exception as e:
        logger.warning(f"结果解析异常: {e}, dimension={dimension}")
        return None


def extract_json(text: str) -> Optional[str]:
    """从文本中提取 JSON 内容

    尝试多种方式提取:
    1. 完整的 JSON 对象 {...}
    2. JSON 数组 [...]
    3. 代码块中的 JSON
    """
    text = text.strip()

    # 方式1: 查找代码块中的 JSON
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        return json_match.group(1)

    # 方式2: 查找独立的 JSON 对象
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        return json_match.group()

    # 方式3: 查找 JSON 数组（用于多维度评估）
    json_match = re.search(r'\[[\s\S]*\]', text)
    if json_match:
        return json_match.group()

    return None


def normalize_level(level: str) -> str:
    """规范化等级描述"""
    level_map = {
        "优秀": "优秀",
        "良好": "良好",
        "一般": "一般",
        "较差": "较差",
        "差": "差",
        "中": "一般",
        "及格": "一般",
        "不及格": "较差",
        "高": "优秀",
        "中上": "良好",
        "中下": "一般",
        "低": "较差",
    }

    # 精确匹配
    if level in level_map:
        return level_map[level]

    # 模糊匹配
    level_lower = level.lower()
    for key, value in level_map.items():
        if key in level_lower or level_lower in key:
            return value

    # 默认返回原始值
    return level


def result_parser_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """结果解析节点

    该节点负责解析 LLM 输出，提取评估结果。

    输入状态:
        - llm_output: LLM 原始输出
        - dimension: 评估维度

    输出状态:
        - dimension_score: 解析后的评估结果
        - parse_error: 解析错误（如有）
    """
    llm_output = state.get("llm_output", "")
    dimension = state.get("dimension", "")

    logger.info(f"开始解析 LLM 输出: dimension={dimension}")

    if state.get("skip"):
        logger.info(f"跳过解析: {state.get('skip_reason')}")
        return {
            "dimension_score": None,
            "parse_error": None,
            "skipped": True
        }

    if not llm_output:
        return {
            "dimension_score": None,
            "parse_error": "LLM 输出为空"
        }

    if not dimension:
        return {
            "dimension_score": None,
            "parse_error": "维度名称为空"
        }

    # 解析结果
    score = parse_llm_output(llm_output, dimension)

    if score is None:
        return {
            "dimension_score": None,
            "parse_error": f"无法解析 LLM 输出，dimension={dimension}"
        }

    logger.info(f"解析成功: dimension={dimension}, score={score.score}, level={score.level}")

    return {
        "dimension_score": score.model_dump(),
        "parse_error": None,
        "skipped": False
    }


def create_parser_node():
    """创建解析节点（供 LangGraph 使用）"""
    return result_parser_node