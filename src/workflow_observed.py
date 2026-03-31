"""
带 Laminar 可观测性的评估工作流

需要在 .env 文件中设置:
LMNR_PROJECT_API_KEY=your_api_key

或使用本地自托管 Laminar:
LMNR_BASE_URL=http://localhost:5667/v1
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# 尝试导入 lmnr
try:
    from lmnr import Laminar, observe
    LMNR_AVAILABLE = True
except ImportError:
    LMNR_AVAILABLE = False
    # 创建 mock 装饰器
    def observe(**kwargs):
        def decorator(func):
            return func
        return decorator

from loguru import logger

from .config import config
from .rule_loader import get_dimension_rules, list_available_dimensions
from .extract_department import extract_department
from .database import Database
from .models import DimensionScore, EvaluationSource, EvaluationResult, EvaluationStatus
from .report_generator import generate_evaluation_report


def _init_laminar():
    """初始化 Laminar"""
    if not LMNR_AVAILABLE:
        return None

    api_key = os.environ.get("LMNR_PROJECT_API_KEY", "local-dev")
    base_url = os.environ.get("LMNR_BASE_URL", None)

    try:
        Laminar.initialize(
            project_api_key=api_key,
            base_url=base_url
        )
        logger.info("Laminar 初始化成功")
        return True
    except Exception as e:
        logger.warning(f"Laminar 初始化失败: {e}")
        return False


# 初始化 Laminar
_laminar_initialized = _init_laminar()


# ============== 带追踪的节点函数 ==============

@observe(name="init_evaluation", metadata={"stage": "init"})
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


@observe(name="extract_department_info", metadata={"stage": "extract"})
def extract_info_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """提取部门/系统信息"""
    logger.info("=== 提取部门/系统信息 ===")

    department, system = extract_department(
        content=state.get("requirement_content", ""),
        title=state.get("requirement_title", ""),
        department=None,  # 自动提取
        system=None
    )

    state["department"] = department
    state["system"] = system

    logger.info(f"部门/系统提取结果: department={department}, system={system}")
    return state


@observe(name="prepare_dimensions", metadata={"stage": "prepare"})
def prepare_dimensions_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """准备评估维度列表"""
    logger.info("=== 准备评估维度 ===")

    dimension_list = list_available_dimensions()
    state["dimensions"] = dimension_list
    state["dimensions_evaluated"] = []

    logger.info(f"将评估 {len(dimension_list)} 个维度")
    return state


@observe(name="select_next_dimension", metadata={"stage": "select"})
def select_next_dimension_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """选择下一个要评估的维度"""
    dimensions = state.get("dimensions", [])
    evaluated = state.get("dimensions_evaluated", [])

    # 找到下一个未评估的维度
    for dim in dimensions:
        if dim not in evaluated:
            state["current_dimension"] = dim
            logger.info(f"选择评估维度: {dim}")
            return state

    # 所有维度都已评估
    state["current_dimension"] = ""
    logger.info("所有维度评估完成")
    return state


@observe(name="load_rule", metadata={"stage": "load"})
def load_rule_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """加载评估规则"""
    dimension = state.get("current_dimension", "")

    logger.info(f"加载规则: dimension={dimension}")
    rule = get_dimension_rules(dimension)
    state["rule"] = rule or ""

    return state


@observe(name="evaluate_dimension", metadata={"stage": "evaluate"})
def run_evaluation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """运行评估"""
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
        # 调用 LLM
        prompt = get_dimension_prompt(dimension, rule, content)
        llm_output = call_llm(prompt)

        # 解析结果
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


@observe(name="aggregate_results", metadata={"stage": "aggregate"})
def aggregate_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """汇总评估结果"""
    logger.info("=== 汇总评估结果 ===")

    dimension_scores = state.get("dimension_scores", [])

    if not dimension_scores:
        state["overall_score"] = 0
        state["overall_level"] = "未评估"
        return state

    # 计算总体评分
    total = sum(s.get("score", 0) for s in dimension_scores)
    avg_score = total / len(dimension_scores) if dimension_scores else 0

    # 计算等级
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

    # 计算耗时
    if state.get("start_time"):
        state["evaluation_duration"] = (datetime.now() - state["start_time"]).total_seconds()

    logger.info(f"评估汇总: overall_score={avg_score:.1f}, level={level}")
    return state


@observe(name="save_results", metadata={"stage": "save"})
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


@observe(name="generate_report", metadata={"stage": "report"})
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

@observe(name="run_evaluation", metadata={"module": "workflow"})
def run_evaluation(
    requirement_content: str,
    requirement_id: str = None,
    requirement_title: str = None,
    department: str = None,
    system: str = None,
    dimensions: List[str] = None,
    enable_personalized: bool = True
) -> Dict[str, Any]:
    """运行评估（带 Laminar 追踪）"""

    # 构建初始状态
    state = init_evaluation(
        requirement_id=requirement_id,
        requirement_title=requirement_title,
        requirement_content=requirement_content
    )

    # 添加可选参数
    if department:
        state["department"] = department
    if system:
        state["system"] = system

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
    "LMNR_AVAILABLE",
]