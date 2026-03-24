"""LLM 评估节点"""
from typing import Dict, Any, Optional
from loguru import logger

from ..llm_client import call_llm, reset_llm_client
from ..prompts import get_dimension_prompt
from ..config import config


def llm_evaluator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LLM 评估节点

    该节点负责调用 LLM 对需求文档进行质量评估。

    输入状态:
        - requirement_content: 需求文档内容
        - dimension: 要评估的维度
        - rule: 评估规则
        - requirement_id: 需求ID
        - attempt: 重试次数

    输出状态:
        - llm_output: LLM 原始输出
        - error: 错误信息（如有）
    """
    requirement_content = state.get("requirement_content", "")
    dimension = state.get("dimension", "")
    rule = state.get("rule", "")
    requirement_id = state.get("requirement_id", "unknown")
    attempt = state.get("attempt", 1)

    max_retries = config.evaluation_config.get("max_retries", 3)

    logger.info(f"开始 LLM 评估: requirement_id={requirement_id}, dimension={dimension}, attempt={attempt}")

    if not requirement_content:
        return {
            "error": "需求文档内容为空",
            "llm_output": None
        }

    if not dimension:
        return {
            "error": "评估维度为空",
            "llm_output": None
        }

    if not rule:
        logger.warning(f"维度 {dimension} 没有对应的规则，跳过评估")
        return {
            "llm_output": None,
            "skip": True,
            "skip_reason": f"维度 {dimension} 没有对应规则"
        }

    try:
        # 构建提示词
        prompt = get_dimension_prompt(dimension, rule, requirement_content)

        # 调用 LLM
        llm_output = call_llm(prompt)

        logger.info(f"LLM 评估完成: dimension={dimension}, 输出长度={len(llm_output)}")

        return {
            "llm_output": llm_output,
            "error": None
        }

    except Exception as e:
        logger.error(f"LLM 评估失败: {e}, attempt={attempt}/{max_retries}")

        # 检查是否需要重试
        if attempt < max_retries:
            logger.info(f"准备重试: attempt={attempt + 1}")
            return {
                "llm_output": None,
                "error": str(e),
                "attempt": attempt + 1,
                "retry": True
            }

        return {
            "llm_output": None,
            "error": f"LLM 调用失败，已重试 {attempt} 次: {str(e)}"
        }


def create_evaluator_node():
    """创建评估节点（供 LangGraph 使用）"""
    return llm_evaluator_node