"""Skill 基础类定义"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from datetime import datetime


@dataclass
class SkillMetadata:
    """Skill 元数据"""
    name: str  # Skill 名称
    description: str  # Skill 描述
    parameters: Dict[str, Any] = field(default_factory=dict)  # 参数定义
    returns: Dict[str, Any] = field(default_factory=dict)  # 返回值定义
    triggers: List[str] = field(default_factory=list)  # 触发场景


@dataclass
class SkillResult:
    """Skill 执行结果"""
    success: bool  # 是否成功
    data: Any = None  # 返回数据
    error: Optional[str] = None  # 错误信息
    metadata: Dict[str, Any] = field(default_factory=dict)  # 附加元数据
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class Skill(ABC):
    """Skill 抽象基类"""

    def __init__(self):
        self._metadata = self.get_metadata()

    @abstractmethod
    def get_metadata(self) -> SkillMetadata:
        """获取 Skill 元数据"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> SkillResult:
        """执行 Skill"""
        pass

    @property
    def name(self) -> str:
        """Skill 名称"""
        return self._metadata.name

    @property
    def description(self) -> str:
        """Skill 描述"""
        return self._metadata.description


def create_skill_result(
    success: bool,
    data: Any = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> SkillResult:
    """创建 SkillResult 的便捷函数"""
    return SkillResult(
        success=success,
        data=data,
        error=error,
        metadata=metadata or {}
    )