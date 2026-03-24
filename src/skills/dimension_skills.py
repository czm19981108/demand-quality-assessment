"""
渐进式规则知识获取 Skills 实现

提供 3 个核心 Skill 函数，供 AI 智能体在评估过程中按需调用。
"""

from typing import Dict, List, Optional, Any
from loguru import logger

from ..rule_loader import (
    get_rule_provider,
    list_available_dimensions as _get_dimensions_from_loader,
    get_dimension_rules,
    get_personalized_department_rules as _get_dept_rules_from_loader,
    list_available_departments as _get_departments_from_loader
)
from .base import SkillResult, SkillMetadata


# ============== Skill 1: 获取指定质量维度的规则 ==============

def get_quality_dimension_rules(dimension: str, simplify: bool = True) -> SkillResult:
    """
    Skill 1: 获取指定质量维度的评估规则

    触发场景：智能体需要评估某个具体维度时

    参数:
        dimension: 质量维度名称（如"功能完整性"、"安全性"等）
        simplify: 是否精简规则内容（去除冗余，保留核心要点）

    返回:
        SkillResult: 包含规则内容
    """
    try:
        # 获取规则
        rule_content = get_dimension_rules(dimension)

        if rule_content is None:
            return SkillResult(
                success=False,
                error=f"维度 '{dimension}' 不存在或规则文件丢失",
                metadata={"dimension": dimension}
            )

        # 可选：精简规则内容
        if simplify:
            rule_content = _simplify_rule_content(rule_content, dimension)

        logger.info(f"Skill: 获取维度规则 - {dimension}")

        return SkillResult(
            success=True,
            data={
                "dimension": dimension,
                "rule": rule_content,
                "simplified": simplify
            },
            metadata={
                "dimension": dimension,
                "rule_length": len(rule_content)
            }
        )

    except Exception as e:
        logger.error(f"Skill 执行失败: get_quality_dimension_rules, error={e}")
        return SkillResult(
            success=False,
            error=str(e),
            metadata={"dimension": dimension}
        )


def _simplify_rule_content(content: str, dimension: str) -> str:
    """
    精简规则内容，保留核心要点

    策略：
    1. 保留评估标准/检查点
    2. 保留常见问题示例
    3. 精简冗长的说明
    4. 限制总长度
    """
    lines = content.split('\n')
    simplified_lines = []
    important_markers = ['####', '###', '**', '检查', '标准', '要求', '示例', '问题', '- ']
    max_lines = 80  # 限制最大行数

    # 优先保留标题和要点
    for line in lines:
        # 跳过太长的段落
        if len(line) > 200:
            stripped = line.strip()
            if stripped and not any(marker in stripped for marker in important_markers):
                continue

        simplified_lines.append(line)

        # 达到限制则截断
        if len(simplified_lines) >= max_lines:
            simplified_lines.append("\n... (规则已精简)")
            break

    return '\n'.join(simplified_lines)


# ============== Skill 2: 列出所有可用维度 ==============

def list_available_dimensions(include_descriptions: bool = False) -> SkillResult:
    """
    Skill 2: 列出所有可用的评估维度

    触发场景：智能体不确定需要评估哪些维度，或需要展示选项

    参数:
        include_descriptions: 是否包含每个维度的简短描述

    返回:
        SkillResult: 包含维度列表
    """
    try:
        dimensions = _get_dimensions_from_loader()

        data = {
            "dimensions": dimensions,
            "total_count": len(dimensions)
        }

        # 如果需要描述，提供每个维度的简短说明
        if include_descriptions:
            descriptions = _get_dimension_descriptions()
            data["descriptions"] = {
                dim: descriptions.get(dim, "暂无描述")
                for dim in dimensions
            }

        logger.info(f"Skill: 列出维度 - 共 {len(dimensions)} 个")

        return SkillResult(
            success=True,
            data=data,
            metadata={"count": len(dimensions)}
        )

    except Exception as e:
        logger.error(f"Skill 执行失败: list_available_dimensions, error={e}")
        return SkillResult(
            success=False,
            error=str(e)
        )


def _get_dimension_descriptions() -> Dict[str, str]:
    """获取各维度的简短描述"""
    return {
        "功能完整性": "需求是否包含所有必要的功能",
        "细节完整性": "需求描述是否足够详细",
        "场景完整性": "是否覆盖正常场景和边界场景",
        "流程完整性": "业务流程是否完整",
        "逆向流程完整性": "是否考虑了异常流程和反向流程",
        "依赖系统完整性": "是否明确了与其他系统的依赖关系",
        "业务风险完整性": "是否识别并处理了业务风险",
        "性能压力完整性": "是否明确了性能要求",
        "可审计需求完整性": "是否满足审计追踪要求",
        "安全完整性": "是否满足安全要求",
        "监管要求完整性": "是否满足监管合规要求",
        "法律要求完整性": "是否满足法律法规要求",
        "兼容完整性": "是否考虑了兼容性",
        "搜索引擎（SEO）优化完整性": "是否满足SEO要求",
        "多样性完整性": "是否考虑用户多样性",
        "出错处理完整性": "是否包含错误处理机制",
        "需求理解正确性": "需求理解是否准确",
        "需求逻辑表达正确性": "逻辑表达是否清晰正确",
        "原始资料正确性": "原始资料是否准确",
        "数据模型正确性": "数据模型设计是否正确",
        "用户体验完整性": "用户体验设计是否完善",
        "易读性": "文档是否易于阅读理解",
        "一致性": "文档内容是否一致",
        "可实现性": "需求是否可以实现",
        "可测性": "需求是否可以测试验证",
        "精确性": "需求描述是否精确无歧义",
        "复用性": "设计是否具有复用性",
        "完整性": "整体完整性评估",
        "精确性": "需求描述精确性",
    }


# ============== Skill 3: 获取部门个性化规则 ==============

def get_personalized_department_rules(
    department: str,
    dimensions: Optional[List[str]] = None
) -> SkillResult:
    """
    Skill 3: 获取特定部门/系统的个性化评估规则

    触发场景：智能体识别到需求文档属于某个部门，需要该部门的特殊规则进行补充评估

    参数:
        department: 部门名称（如"电商"、"金融"等）
        dimensions: 可选，指定要获取的维度列表，默认获取全部

    返回:
        SkillResult: 包含部门个性化规则
    """
    try:
        # 获取部门的个性化规则
        dept_rules = _get_dept_rules_from_loader(department)

        if not dept_rules:
            return SkillResult(
                success=True,
                data={
                    "department": department,
                    "rules": {},
                    "message": f"部门 '{department}' 暂无个性化规则"
                },
                metadata={"department": department, "rule_count": 0}
            )

        # 如果指定了维度，过滤结果
        if dimensions:
            dept_rules = {k: v for k, v in dept_rules.items() if k in dimensions}

        logger.info(f"Skill: 获取部门个性化规则 - {department}, 共 {len(dept_rules)} 个维度")

        return SkillResult(
            success=True,
            data={
                "department": department,
                "rules": dept_rules,
                "dimensions": list(dept_rules.keys()),
                "rule_count": len(dept_rules)
            },
            metadata={
                "department": department,
                "rule_count": len(dept_rules)
            }
        )

    except Exception as e:
        logger.error(f"Skill 执行失败: get_personalized_department_rules, error={e}")
        return SkillResult(
            success=False,
            error=str(e),
            metadata={"department": department}
        )


def list_available_departments() -> SkillResult:
    """
    列出所有有个性化规则的部门

    返回:
        SkillResult: 包含部门列表
    """
    try:
        departments = _get_departments_from_loader()

        logger.info(f"Skill: 列出部门 - 共 {len(departments)} 个")

        return SkillResult(
            success=True,
            data={
                "departments": departments,
                "total_count": len(departments)
            },
            metadata={"count": len(departments)}
        )

    except Exception as e:
        logger.error(f"Skill 执行失败: list_available_departments, error={e}")
        return SkillResult(
            success=False,
            error=str(e)
        )


# ============== 渐进式披露工作流辅助函数 ==============

def get_progressive_evaluation_workflow() -> Dict[str, Any]:
    """
    获取渐进式评估工作流指引

    供 AI 智能体参考的标准工作流程
    """
    return {
        "workflow": [
            {
                "step": 1,
                "action": "list_available_dimensions",
                "description": "先调用 list_available_dimensions() 了解有哪些维度"
            },
            {
                "step": 2,
                "action": "analyze_requirement",
                "description": "根据需求文档内容，决定要评估哪些维度"
            },
            {
                "step": 3,
                "action": "get_quality_dimension_rules",
                "description": "对每个选定维度，调用 get_quality_dimension_rules() 获取规则"
            },
            {
                "step": 4,
                "action": "evaluate",
                "description": "基于规则进行评估，输出结果"
            },
            {
                "step": 5,
                "action": "extract_department",
                "description": "尝试从需求文档中识别所属部门"
            },
            {
                "step": 6,
                "action": "get_personalized_department_rules",
                "description": "如果识别到部门，调用 get_personalized_department_rules() 获取个性化规则"
            },
            {
                "step": 7,
                "action": "supplementary_evaluate",
                "description": "基于个性化规则做补充评估"
            },
            {
                "step": 8,
                "action": "merge_results",
                "description": "合并两阶段结果，生成最终报告"
            }
        ],
        "principles": [
            "按需获取：用到什么给什么，不过早暴露全部信息",
            "保持精简：每次只获取一个维度的规则",
            "渐进增强：第一阶段通用评估，第二阶段个性化补充"
        ]
    }