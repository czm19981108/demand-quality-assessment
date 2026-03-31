"""报告生成模块"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from loguru import logger

from .models import DimensionScore, EvaluationResult, EvaluationSource, Report
from .config import config
from .rustfs_client import get_rustfs_client


def calculate_level(score: float) -> str:
    """根据评分计算等级"""
    if score >= 90:
        return "优秀"
    elif score >= 75:
        return "良好"
    elif score >= 60:
        return "一般"
    elif score >= 40:
        return "较差"
    else:
        return "差"


def calculate_overall_score(dimension_scores: List[DimensionScore]) -> float:
    """计算总体评分（各维度平均分）"""
    if not dimension_scores:
        return 0
    return sum(s.score for s in dimension_scores) / len(dimension_scores)


def format_dimension_result(score: DimensionScore) -> str:
    """格式化单个维度的评估结果"""
    issues_text = "\n".join([f"  - {issue}" for issue in score.issues]) if score.issues else "  无"
    suggestions_text = "\n".join([f"  - {s}" for s in score.suggestions]) if score.suggestions else "  无"

    return f"""### {score.dimension}

| 指标 | 值 |
|------|-----|
| 评分 | {score.score} 分 |
| 等级 | {score.level} |

**评估依据**: {score.evidence or "无"}

**发现的问题**:
{issues_text}

**改进建议**:
{suggestions_text}
"""


def generate_markdown_report(
    requirement_id: str,
    requirement_title: str,
    department: Optional[str],
    system: Optional[str],
    dimension_scores: List[DimensionScore],
    overall_score: float,
    overall_level: str,
    evaluation_duration: Optional[float] = None
) -> str:
    """生成 Markdown 格式的评估报告"""

    # 分类结果
    general_results = [s for s in dimension_scores]  # 简化处理，所有结果都显示

    # 构建报告内容
    report_lines = [
        f"# 需求文档质量评估报告",
        "",
        f"**需求ID**: {requirement_id}",
        f"**需求标题**: {requirement_title}",
        f"**所属部门**: {department or '未识别'}",
        f"**所属系统**: {system or '未识别'}",
        f"**评估时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    if evaluation_duration:
        report_lines.append(f"**评估耗时**: {evaluation_duration:.2f} 秒")

    report_lines.extend([
        "",
        "---",
        "",
        "## 评估摘要",
        "",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| 总体评分 | **{overall_score:.1f}** 分 |",
        f"| 总体等级 | **{overall_level}** |",
        f"| 评估维度数 | {len(dimension_scores)} |",
        "",
    ])

    # 维度评分表格
    if dimension_scores:
        report_lines.extend([
            "## 维度评分概览",
            "",
            f"| 维度 | 评分 | 等级 |",
            f"|------|------|------|",
        ])
        for s in dimension_scores:
            report_lines.append(f"| {s.dimension} | {s.score} | {s.level} |")
        report_lines.append("")

    # 详细评估结果
    if general_results:
        report_lines.extend([
            "## 通用规则评估详情",
            ""
        ])
        for score in general_results:
            report_lines.append(format_dimension_result(score))
            report_lines.append("")

    # 总结
    report_lines.extend([
        "---",
        "",
        "## 总结",
        "",
        f"本次评估共对 **{len(dimension_scores)}** 个维度进行了评估，",
        f"总体评分为 **{overall_score:.1f}** 分，等级为 **{overall_level}**。",
        "",
    ])

    # 汇总问题和建议
    all_issues = []
    all_suggestions = []
    for s in dimension_scores:
        all_issues.extend(s.issues)
        all_suggestions.extend(s.suggestions)

    if all_issues:
        report_lines.append("### 主要问题")
        for issue in all_issues[:10]:  # 最多显示10个
            report_lines.append(f"- {issue}")
        report_lines.append("")

    if all_suggestions:
        report_lines.append("### 改进建议")
        for suggestion in all_suggestions[:10]:  # 最多显示10个
            report_lines.append(f"- {suggestion}")
        report_lines.append("")

    return "\n".join(report_lines)


def save_report(
    report_content: str,
    requirement_id: str,
    format: str = "markdown"
) -> str:
    """保存报告

    如果启用了 RustFS，则上传到 RustFS 对象存储；否则保存到本地文件。

    Args:
        report_content: 报告内容
        requirement_id: 需求ID
        format: 报告格式

    Returns:
        报告路径（本地路径或 RustFS 对象键）
    """
    # 如果启用了 RustFS，优先上传到 RustFS
    rustfs = get_rustfs_client()
    if rustfs.enabled:
        success, object_key = rustfs.upload_report(requirement_id, report_content)
        if success:
            logger.info(f"报告已上传到 RustFS: {object_key}")
            return f"rustfs://{object_key}"
        else:
            logger.warning("RustFS 上传失败，回退到本地存储")

    # 回退到本地文件存储
    output_dir = Path(config.report_config.get("output_dir", "data/reports"))
    output_dir.mkdir(parents=True, exist_ok=True)

    extension = "md" if format == "markdown" else format
    filename = f"{requirement_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
    file_path = output_dir / filename

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"报告已保存到本地: {file_path}")
    return str(file_path)


def generate_evaluation_report(
    requirement_id: str,
    requirement_title: str,
    department: Optional[str],
    system: Optional[str],
    dimension_scores: List[DimensionScore],
    evaluation_duration: Optional[float] = None,
    save: bool = True
) -> Tuple[Report, Optional[str]]:
    """生成评估报告

    Args:
        requirement_id: 需求ID
        requirement_title: 需求标题
        department: 部门
        system: 系统
        dimension_scores: 维度评分列表
        evaluation_duration: 评估耗时
        save: 是否保存到文件/RustFS

    Returns:
        (Report 对象, 报告路径)
    """
    # 计算总体评分和等级
    overall_score = calculate_overall_score(dimension_scores)
    overall_level = calculate_level(overall_score)
    dimensions_evaluated = [s.dimension for s in dimension_scores]

    # 生成 Markdown 报告
    report_content = generate_markdown_report(
        requirement_id=requirement_id,
        requirement_title=requirement_title,
        department=department,
        system=system,
        dimension_scores=dimension_scores,
        overall_score=overall_score,
        overall_level=overall_level,
        evaluation_duration=evaluation_duration
    )

    # 保存报告
    report_path = None
    if save:
        report_path = save_report(report_content, requirement_id)

    report_obj = Report(
        requirement_id=requirement_id,
        requirement_title=requirement_title,
        department=department,
        system=system,
        overall_score=overall_score,
        overall_level=overall_level,
        general_results=dimension_scores,
        dimensions_evaluated=dimensions_evaluated,
        generated_at=datetime.now(),
        evaluation_duration=evaluation_duration
    )

    return report_obj, report_path


def create_report_node():
    """创建报告生成节点（供 LangGraph 使用）"""
    def report_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
        requirement_id = state.get("requirement_id", "unknown")
        requirement_title = state.get("requirement_title", "")
        department = state.get("department")
        system = state.get("system")
        dimension_scores_data = state.get("dimension_scores", [])
        evaluation_duration = state.get("evaluation_duration")

        logger.info(f"开始生成评估报告: requirement_id={requirement_id}")

        # 转换 dimension_scores
        dimension_scores = []
        for score_data in dimension_scores_data:
            if isinstance(score_data, dict):
                dimension_scores.append(DimensionScore(**score_data))
            elif isinstance(score_data, DimensionScore):
                dimension_scores.append(score_data)

        # 生成报告
        report, report_path = generate_evaluation_report(
            requirement_id=requirement_id,
            requirement_title=requirement_title,
            department=department,
            system=system,
            dimension_scores=dimension_scores,
            evaluation_duration=evaluation_duration,
            save=True
        )

        return {
            "report": report.model_dump(),
            "report_path": report_path
        }

    return report_generator_node