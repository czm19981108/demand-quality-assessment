"""LangGraph 工作流定义"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

# LangGraph 相关导入
try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph 未安装，部分功能不可用")

from .config import config
from .rule_loader import get_rule_provider, list_available_dimensions, get_dimension_rules
from .extract_department import extract_department
from .models import DimensionScore, EvaluationSource


# 定义状态类型
class EvaluationState(dict):
    """评估流程状态"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # 输入
    requirement_content: str = ""
    requirement_id: str = ""
    requirement_title: str = ""
    department: Optional[str] = None
    system: Optional[str] = None

    # 评估选项
    dimensions: List[str] = []
    enable_personalized: bool = True

    # 内部状态
    current_dimension: str = ""
    dimension_scores: List[Dict[str, Any]] = []
    dimensions_evaluated: List[str] = []
    evaluation_results: List[Dict[str, Any]] = []

    # 时间
    start_time: Optional[datetime] = None
    evaluation_duration: Optional[float] = None

    # 错误
    error: Optional[str] = None


def should_evaluate_dimension(state: EvaluationState) -> bool:
    """判断是否还有需要评估的维度"""
    return state.get("current_dimension") != ""


def should_run_personalized(state: EvaluationState) -> bool:
    """判断是否需要运行个性化评估"""
    department = state.get("department")
    enable_personalized = state.get("enable_personalized", True)
    return enable_personalized and department is not None


# 节点函数
def init_evaluation(state: EvaluationState) -> EvaluationState:
    """初始化评估"""
    logger.info("=== 初始化评估 ===")

    # 设置时间
    state["start_time"] = datetime.now()

    # 生成需求ID（如果未提供）
    if not state.get("requirement_id"):
        state["requirement_id"] = f"req_{int(datetime.now().timestamp())}"

    # 设置默认标题
    if not state.get("requirement_title"):
        state["requirement_title"] = "未命名需求"

    logger.info(f"评估初始化完成: requirement_id={state['requirement_id']}")
    return state


def extract_info_node(state: EvaluationState) -> EvaluationState:
    """提取部门/系统信息"""
    logger.info("=== 提取部门/系统信息 ===")

    # 提取部门信息
    department, system = extract_department(
        content=state.get("requirement_content", ""),
        title=state.get("requirement_title", ""),
        department=state.get("department"),
        system=state.get("system")
    )

    state["department"] = department
    state["system"] = system

    logger.info(f"部门/系统提取结果: department={department}, system={system}")
    return state


def prepare_dimensions_node(state: EvaluationState) -> EvaluationState:
    """准备评估维度列表"""
    logger.info("=== 准备评估维度 ===")

    # 获取用户指定的维度或所有可用维度
    specified_dims = state.get("dimensions", [])

    if specified_dims:
        # 使用用户指定的维度
        dimension_list = specified_dims
    else:
        # 使用所有可用维度
        dimension_list = list_available_dimensions()

    state["dimensions"] = dimension_list
    state["dimensions_evaluated"] = []

    logger.info(f"将评估 {len(dimension_list)} 个维度")
    return state


def select_next_dimension_node(state: EvaluationState) -> EvaluationState:
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


def load_rule_node(state: EvaluationState) -> EvaluationState:
    """加载评估规则"""
    dimension = state.get("current_dimension", "")
    source = state.get("current_source", "general")

    logger.info(f"加载规则: dimension={dimension}, source={source}")

    if source == "general":
        rule = get_dimension_rules(dimension)
    else:
        # 个性化规则
        from .rule_loader import get_personalized_department_rules
        dept = state.get("department")
        dept_rules = get_personalized_department_rules(dept) if dept else {}
        rule = dept_rules.get(dimension)

    state["rule"] = rule or ""
    return state


def run_evaluation_node(state: EvaluationState) -> EvaluationState:
    """运行评估（简化版，同步调用）"""
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
            state["dimension_scores"].append(score.model_dump())
            state["dimensions_evaluated"].append(dimension)
            logger.info(f"评估完成: {dimension}, score={score.score}")
        else:
            logger.warning(f"评估结果解析失败: {dimension}")

    except Exception as e:
        logger.error(f"评估失败: {dimension}, error={e}")
        state["error"] = str(e)

    return state


def aggregate_results_node(state: EvaluationState) -> EvaluationState:
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


def save_results_node(state: EvaluationState) -> EvaluationState:
    """保存评估结果"""
    from .database import Database

    logger.info("=== 保存评估结果 ===")

    try:
        db = Database(config.db_path)

        dimension_scores = []
        for score_dict in state.get("dimension_scores", []):
            dimension_scores.append(DimensionScore(**score_dict))

        from .models import EvaluationResult, EvaluationStatus
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


def generate_report_node(state: EvaluationState) -> EvaluationState:
    """生成评估报告"""
    from .report_generator import generate_evaluation_report

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


def build_evaluation_graph():
    """构建评估图（LangGraph）"""
    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph 不可用，返回简易版本")
        return None

    # 创建图
    workflow = StateGraph(EvaluationState)

    # 添加节点
    workflow.add_node("init", init_evaluation)
    workflow.add_node("extract_info", extract_info_node)
    workflow.add_node("prepare_dimensions", prepare_dimensions_node)
    workflow.add_node("select_dimension", select_next_dimension_node)
    workflow.add_node("load_rule", load_rule_node)
    workflow.add_node("evaluate", run_evaluation_node)
    workflow.add_node("aggregate", aggregate_results_node)
    workflow.add_node("save", save_results_node)
    workflow.add_node("report", generate_report_node)

    # 设置边
    workflow.set_entry_point("init")
    workflow.add_edge("init", "extract_info")
    workflow.add_edge("extract_info", "prepare_dimensions")
    workflow.add_edge("prepare_dimensions", "select_dimension")

    # 条件边：评估循环
    workflow.add_conditional_edges(
        "select_dimension",
        should_evaluate_dimension,
        {
            True: "load_rule",
            False: "aggregate"
        }
    )

    workflow.add_edge("load_rule", "evaluate")
    workflow.add_edge("evaluate", "select_dimension")

    workflow.add_edge("aggregate", "save")
    workflow.add_edge("save", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


def run_evaluation(
    requirement_content: str,
    requirement_id: str = None,
    requirement_title: str = None,
    department: str = None,
    system: str = None,
    dimensions: List[str] = None,
    enable_personalized: bool = True
) -> Dict[str, Any]:
    """运行评估（简化同步版本）

    Args:
        requirement_content: 需求文档内容
        requirement_id: 需求ID
        requirement_title: 需求标题
        department: 指定部门
        system: 指定系统
        dimensions: 指定评估维度
        enable_personalized: 是否启用个性化评估

    Returns:
        评估结果字典
    """
    # 构建初始状态
    state = EvaluationState({
        "requirement_content": requirement_content,
        "requirement_id": requirement_id or f"req_{int(datetime.now().timestamp())}",
        "requirement_title": requirement_title or "未命名需求",
        "department": department,
        "system": system,
        "dimensions": dimensions or [],
        "enable_personalized": enable_personalized,
    })

    # 执行评估流程
    state = init_evaluation(state)
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


# 导出主要接口
__all__ = [
    "run_evaluation",
    "build_evaluation_graph",
    "EvaluationState"
]