"""
带 Langfuse 可观测性的评估工作流

按照 Langfuse 最佳实践实现:
- 正确的 SDK 初始化和认证
- 分层追踪: Root Trace → 评估节点 → LLM 调用
- 自动捕获 LLM 输入输出、token 使用和延迟
- 记录业务指标（评估分数）

需要在 .env 文件中设置:
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_PUBLIC_KEY=your_public_key

本地自托管时还需要:
LANGFUSE_HOST=http://localhost:3000
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# 尝试导入 langfuse (v4.x)
try:
    from langfuse import Langfuse
    from langfuse import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    # 创建 mock 装饰器和占位符
    def observe(**kwargs):
        def decorator(func):
            return func
        return decorator
    class Langfuse:
        def __init__(self, **kwargs): pass
        def flush(self): pass
        def flush_async(self): pass

from loguru import logger

from .config import config
from .rule_loader import get_dimension_rules, list_available_dimensions
from .extract_department import extract_department
from .database import Database
from .models import DimensionScore, EvaluationSource, EvaluationResult, EvaluationStatus
from .report_generator import generate_evaluation_report


# Langfuse 客户端实例
_langfuse_client: Optional[Langfuse] = None


def _init_langfuse() -> Optional[Langfuse]:
    """初始化 Langfuse"""
    if not LANGFUSE_AVAILABLE:
        return None

    try:
        # 从环境变量或配置文件获取配置
        secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "local-secret-key")
        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "local-public-key")
        host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")

        client = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=host
        )

        # 检查连接
        client.auth_check()

        logger.info(f"Langfuse 初始化成功: {host}")
        return client

    except Exception as e:
        logger.warning(f"Langfuse 初始化失败: {e}")
        return None


# 初始化 Langfuse
_langfuse_client = _init_langfuse()


def get_langfuse() -> Optional[Langfuse]:
    """获取 Langfuse 客户端"""
    return _langfuse_client


# ============== 带追踪的节点函数 ==============

@observe(name="init_evaluation")
def init_evaluation(requirement_id: str, requirement_title: str, requirement_content: str) -> Dict[str, Any]:
    """初始化评估"""
    logger.info("=== 初始化评估 ===")

    state = {
        "start_time": datetime.now(),
        "requirement_id": requirement_id or f"req_{int(datetime.now().timestamp())}",
        "requirement_title": requirement_title or "未命名需求",
        "requirement_content": requirement_content,
    }

    logger.info(f"评估初始化完成: requirement_id={state['requirement_id']}")
    return state


@observe(name="extract_department_info")
def extract_info_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """提取部门/系统信息"""
    logger.info("=== 提取部门/系统信息 ===")

    department, system = extract_department(
        content=state.get("requirement_content", ""),
        title=state.get("requirement_title", ""),
        department=None,
        system=None
    )

    state["department"] = department
    state["system"] = system

    logger.info(f"部门/系统提取结果: department={department}, system={system}")
    return state


@observe(name="prepare_dimensions")
def prepare_dimensions_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """准备评估维度列表"""
    logger.info("=== 准备评估维度 ===")

    # 如果传入了指定维度，就只用指定的
    if state.get("dimensions"):
        dimension_list = state["dimensions"]
    else:
        dimension_list = list_available_dimensions()

    state["dimensions"] = dimension_list
    state["dimensions_evaluated"] = []

    logger.info(f"将评估 {len(dimension_list)} 个维度")
    return state


@observe(name="select_next_dimension")
def select_next_dimension_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """选择下一个要评估的维度"""
    dimensions = state.get("dimensions", [])
    evaluated = state.get("dimensions_evaluated", [])

    for dim in dimensions:
        if dim not in evaluated:
            state["current_dimension"] = dim
            logger.info(f"选择评估维度: {dim}")
            return state

    state["current_dimension"] = ""
    logger.info("所有维度评估完成")
    return state


@observe(name="load_rule")
def load_rule_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """加载评估规则"""
    dimension = state.get("current_dimension", "")

    logger.info(f"加载规则: dimension={dimension}")
    rule = get_dimension_rules(dimension)
    state["rule"] = rule or ""

    return state


@observe(name="evaluate_dimension", capture_input=True)
def run_evaluation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """运行评估

    单个维度评估，会自动记录：
    - 维度名称
    - 规则加载
    - LLM 调用（通过 Langfuse 自动追踪）
    - 评估分数
    """
    from .llm_client import call_llm
    from .prompts import get_dimension_prompt
    from .nodes.result_parser import parse_llm_output

    dimension = state.get("current_dimension", "")
    rule = state.get("rule", "")
    content = state.get("requirement_content", "")

    if not rule:
        logger.warning(f"维度 {dimension} 没有规则，跳过")
        return state

    try:
        prompt = get_dimension_prompt(dimension, rule, content)
        llm_output = call_llm(prompt)

        score = parse_llm_output(llm_output, dimension)

        if score:
            state.setdefault("dimension_scores", []).append(score.model_dump())
            state.setdefault("dimensions_evaluated", []).append(dimension)
            logger.info(f"评估完成: {dimension}, score={score.score}")
        else:
            logger.warning(f"评估结果解析失败: {dimension}")

    except Exception as e:
        logger.error(f"评估失败: {dimension}, error={e}")
        state["error"] = str(e)

    return state


@observe(name="aggregate_results")
def aggregate_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """汇总评估结果"""
    logger.info("=== 汇总评估结果 ===")

    dimension_scores = state.get("dimension_scores", [])

    if not dimension_scores:
        state["overall_score"] = 0
        state["overall_level"] = "未评估"
        return state

    total = sum(s.get("score", 0) for s in dimension_scores)
    avg_score = total / len(dimension_scores) if dimension_scores else 0

    if avg_score >= 90:
        level = "优秀"
    elif avg_score >= 75:
        level = "良好"
    elif avg_score >= 60:
        level = "一般"
    elif avg_score >= 40:
        level = "较差"
    else:
        level = "差"

    state["overall_score"] = avg_score
    state["overall_level"] = level

    if state.get("start_time"):
        state["evaluation_duration"] = (datetime.now() - state["start_time"]).total_seconds()

    logger.info(f"评估汇总: overall_score={avg_score:.1f}, level={level}")
    return state


@observe(name="save_results")
def save_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """保存评估结果"""
    logger.info("=== 保存评估结果 ===")

    try:
        db = Database(config.db_path)

        dimension_scores = []
        for score_dict in state.get("dimension_scores", []):
            dimension_scores.append(DimensionScore(**score_dict))

        result = EvaluationResult(
            requirement_id=state.get("requirement_id", "unknown"),
            requirement_title=state.get("requirement_title", ""),
            department=state.get("department"),
            system=state.get("system"),
            source=EvaluationSource.GENERAL,
            dimension_scores=dimension_scores,
            overall_score=state.get("overall_score", 0),
            overall_level=state.get("overall_level", ""),
            dimensions_evaluated=state.get("dimensions_evaluated", []),
            evaluation_time=datetime.now(),
            evaluation_duration=state.get("evaluation_duration"),
            status=EvaluationStatus.COMPLETED
        )

        db.save_evaluation(result)
        state["saved"] = True
        logger.info("评估结果已保存")

    except Exception as e:
        logger.error(f"保存失败: {e}")
        state["error"] = str(e)

    return state


@observe(name="generate_report")
def generate_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """生成评估报告"""
    logger.info("=== 生成评估报告 ===")

    try:
        dimension_scores = []
        for score_dict in state.get("dimension_scores", []):
            dimension_scores.append(DimensionScore(**score_dict))

        report = generate_evaluation_report(
            requirement_id=state.get("requirement_id", "unknown"),
            requirement_title=state.get("requirement_title", ""),
            department=state.get("department"),
            system=state.get("system"),
            dimension_scores=dimension_scores,
            evaluation_duration=state.get("evaluation_duration"),
            save=True
        )

        state["report"] = report.model_dump()
        logger.info("报告生成完成")

    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        state["error"] = str(e)

    return state


# ============== 主工作流 ==============

@observe(name="demand_quality_evaluation", capture_input=True)
def run_evaluation(
    requirement_content: str,
    requirement_id: str = None,
    requirement_title: str = None,
    department: str = None,
    system: str = None,
    dimensions: List[str] = None,
    enable_personalized: bool = True
) -> Dict[str, Any]:
    """运行评估（带 Langfuse 追踪）

    根 Trace - 包含整个评估工作流的完整追踪
    """
    # 构建初始状态
    state = init_evaluation(
        requirement_id=requirement_id,
        requirement_title=requirement_title,
        requirement_content=requirement_content
    )

    if department:
        state["department"] = department
    if system:
        state["system"] = system
    if dimensions:
        state["dimensions"] = dimensions

    # 执行评估流程
    state = extract_info_node(state)
    state = prepare_dimensions_node(state)

    # 逐个评估维度
    while True:
        state = select_next_dimension_node(state)

        if not state.get("current_dimension"):
            break

        state = load_rule_node(state)
        state = run_evaluation_node(state)

    # 汇总结果
    state = aggregate_results_node(state)
    state = save_results_node(state)
    state = generate_report_node(state)

    # 确保所有 span 都上报完成
    if _langfuse_client:
        _langfuse_client.flush()

    return {
        "requirement_id": state.get("requirement_id"),
        "requirement_title": state.get("requirement_title"),
        "department": state.get("department"),
        "system": state.get("system"),
        "overall_score": state.get("overall_score", 0),
        "overall_level": state.get("overall_level", "未评估"),
        "dimensions_evaluated": state.get("dimensions_evaluated", []),
        "dimension_scores": state.get("dimension_scores", []),
        "evaluation_duration": state.get("evaluation_duration"),
        "error": state.get("error")
    }


__all__ = [
    "run_evaluation",
    "get_langfuse",
    "LANGFUSE_AVAILABLE",
]