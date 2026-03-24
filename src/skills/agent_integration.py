"""
AI Agent 集成模块

将 Skills 封装成 Agent 可用的工具，支持多种 Agent 框架：
- LangChain Agents
- Claude Agent SDK
- 通用函数调用
"""

from typing import Dict, List, Any, Optional, Callable
from loguru import logger
from dataclasses import dataclass

from .base import SkillResult
from .dimension_skills import (
    get_quality_dimension_rules,
    list_available_dimensions,
    get_personalized_department_rules,
    list_available_departments,
    get_progressive_evaluation_workflow
)
from ..rule_loader import list_available_dimensions as get_all_dimensions


# ============== 工具定义 ==============

@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable


# ============== 工具注册表 ==============

def create_tools() -> List[ToolDefinition]:
    """创建所有可用的工具定义"""
    return [
        ToolDefinition(
            name="get_quality_dimension_rules",
            description="获取指定质量维度的评估规则。每次只返回一个维度，避免信息过载。支持28个通用维度的按需查询。",
            parameters={
                "type": "object",
                "properties": {
                    "dimension": {
                        "type": "string",
                        "description": "质量维度名称，如'功能完整性'、'安全性'、'易读性'等"
                    },
                    "simplify": {
                        "type": "boolean",
                        "description": "是否精简规则内容（默认true）",
                        "default": True
                    }
                },
                "required": ["dimension"]
            },
            function=get_quality_dimension_rules
        ),
        ToolDefinition(
            name="list_available_dimensions",
            description="列出所有可用的评估维度。触发场景：智能体不确定需要评估哪些维度，或需要展示选项。",
            parameters={
                "type": "object",
                "properties": {
                    "include_descriptions": {
                        "type": "boolean",
                        "description": "是否包含每个维度的简短描述",
                        "default": False
                    }
                }
            },
            function=list_available_dimensions
        ),
        ToolDefinition(
            name="get_personalized_department_rules",
            description="获取特定部门/系统的个性化评估规则。触发场景：智能体识别到需求文档属于某个部门，需要该部门的特殊规则进行补充评估。",
            parameters={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "部门名称，如'电商'、'金融'、'物流'等"
                    },
                    "dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "可选，指定要获取的维度列表"
                    }
                },
                "required": ["department"]
            },
            function=get_personalized_department_rules
        ),
        ToolDefinition(
            name="list_available_departments",
            description="列出所有有个性化规则的部门。",
            parameters={"type": "object", "properties": {}},
            function=list_available_departments
        ),
    ]


# ============== Agent 调用接口 ==============

class SkillsAgent:
    """渐进式评估 Skills Agent

    封装渐进式规则获取能力，供 AI 智能体调用
    """

    def __init__(self):
        self.tools = create_tools()
        self.tool_map = {t.name: t for t in self.tools}
        logger.info(f"SkillsAgent 初始化，共 {len(self.tools)} 个工具")

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取工具定义（用于 Agent 系统提示）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self.tools
        ]

    def call_tool(self, tool_name: str, **kwargs) -> SkillResult:
        """调用指定工具"""
        tool = self.tool_map.get(tool_name)
        if tool is None:
            return SkillResult(
                success=False,
                error=f"工具 '{tool_name}' 不存在"
            )

        try:
            result = tool.function(**kwargs)
            logger.info(f"工具调用成功: {tool_name}")
            return result
        except Exception as e:
            logger.error(f"工具调用失败: {tool_name}, error={e}")
            return SkillResult(
                success=False,
                error=str(e)
            )

    def execute_progressive_evaluation(self, requirement_content: str) -> Dict[str, Any]:
        """
        执行渐进式评估的标准工作流

        供 AI Agent 参考的执行流程
        """
        result = {
            "workflow": get_progressive_evaluation_workflow(),
            "available_dimensions": get_all_dimensions(),
            "message": "请按工作流逐步执行评估"
        }
        return result


# 全局实例
_skills_agent: Optional[SkillsAgent] = None


def get_skills_agent() -> SkillsAgent:
    """获取 SkillsAgent 实例"""
    global _skills_agent
    if _skills_agent is None:
        _skills_agent = SkillsAgent()
    return _skills_agent


# ============== 便捷函数 ==============

def get_tool_schemas() -> List[Dict[str, Any]]:
    """获取工具 schemas（兼容 OpenAI function calling 格式）"""
    return get_skills_agent().get_tool_definitions()


def call_skill(skill_name: str, **kwargs) -> SkillResult:
    """直接调用 Skill 的便捷函数"""
    return get_skills_agent().call_tool(skill_name, **kwargs)


__all__ = [
    "SkillsAgent",
    "ToolDefinition",
    "get_skills_agent",
    "get_tool_schemas",
    "call_skill",
    "create_tools",
    "get_progressive_evaluation_workflow",
    # 导出所有 Skill 函数
    "get_quality_dimension_rules",
    "list_available_dimensions",
    "get_personalized_department_rules",
    "list_available_departments",
]