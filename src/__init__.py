"""需求文档质量评估系统"""
from .config import config, Config
from .models import (
    EvaluationResult,
    EvaluationRequest,
    DimensionScore,
    EvaluationStatus,
    EvaluationSource,
    Report
)
from .rule_loader import (
    get_rule_provider,
    set_rule_provider,
    list_available_dimensions,
    get_dimension_rules,
    get_personalized_department_rules,
    list_available_departments,
    RuleProvider,
    LocalFileRuleProvider
)
from .extract_department import extract_department
from .database import Database
from .workflow import run_evaluation, build_evaluation_graph
from .report_generator import generate_evaluation_report

__version__ = "1.0.0"

__all__ = [
    # 配置
    "config",
    "Config",
    # 模型
    "EvaluationResult",
    "EvaluationRequest",
    "DimensionScore",
    "EvaluationStatus",
    "EvaluationSource",
    "Report",
    # 规则加载
    "get_rule_provider",
    "set_rule_provider",
    "list_available_dimensions",
    "get_dimension_rules",
    "get_personalized_department_rules",
    "list_available_departments",
    "RuleProvider",
    "LocalFileRuleProvider",
    # 部门提取
    "extract_department",
    # 数据库
    "Database",
    # 工作流
    "run_evaluation",
    "build_evaluation_graph",
    # 报告
    "generate_evaluation_report",
]