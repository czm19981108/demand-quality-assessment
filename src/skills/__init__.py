"""
渐进式规则知识获取 Skills 模块

本模块提供 3 个核心 Skill，供 AI 智能体在评估过程中按需调用：

1. get_quality_dimension_rules: 获取指定质量维度的评估规则
2. list_available_dimensions: 列出所有可用的评估维度
3. get_personalized_department_rules: 获取特定部门/系统的个性化评估规则

渐进式披露的核心思想：
- 像师傅带徒弟，边做边教，按需给知识
- 智能体需要哪个维度的规则，再获取对应的规则
- 保持上下文精简，提高推理效率和准确性
"""

from .base import Skill, SkillResult, SkillMetadata
from .dimension_skills import (
    get_quality_dimension_rules,
    list_available_dimensions,
    get_personalized_department_rules,
    list_available_departments
)

# Skill 注册表
SKILL_REGISTRY = {
    "get_quality_dimension_rules": get_quality_dimension_rules,
    "list_available_dimensions": list_available_dimensions,
    "get_personalized_department_rules": get_personalized_department_rules,
    "list_available_departments": list_available_departments,
}


def get_skill(name: str) -> Skill:
    """根据名称获取 Skill"""
    skill = SKILL_REGISTRY.get(name)
    if skill is None:
        raise ValueError(f"Skill '{name}' 不存在")
    return skill


def list_available_skills() -> list[str]:
    """列出所有可用的 Skill"""
    return list(SKILL_REGISTRY.keys())


__all__ = [
    # 基础类
    "Skill",
    "SkillResult",
    "SkillMetadata",
    # Skill 函数
    "get_quality_dimension_rules",
    "list_available_dimensions",
    "get_personalized_department_rules",
    "list_available_departments",
    # 注册表
    "get_skill",
    "list_available_skills",
    "SKILL_REGISTRY",
]