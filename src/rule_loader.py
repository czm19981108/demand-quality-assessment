"""规则加载器模块"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger

from .config import config


class RuleProvider(ABC):
    """规则提供者抽象基类"""

    @abstractmethod
    def list_dimensions(self) -> List[str]:
        """列出所有可用的评估维度"""
        pass

    @abstractmethod
    def get_rule(self, dimension: str) -> Optional[str]:
        """获取指定维度的规则内容"""
        pass

    @abstractmethod
    def get_department_rules(self, department: str) -> Dict[str, str]:
        """获取指定部门的个性化规则"""
        pass

    @abstractmethod
    def list_departments(self) -> List[str]:
        """列出所有可用的部门"""
        pass


class LocalFileRuleProvider(RuleProvider):
    """本地文件系统规则提供者"""

    def __init__(self, general_rules_dir: Optional[str] = None, department_rules_dir: Optional[str] = None):
        self.general_rules_dir = Path(general_rules_dir or config.general_rules_dir)
        self.department_rules_dir = Path(department_rules_dir or config.department_rules_dir)
        self._dimensions_cache: Optional[List[str]] = None
        self._department_cache: Optional[List[str]] = None
        logger.info(f"规则加载器初始化: general={self.general_rules_dir}, department={self.department_rules_dir}")

    def list_dimensions(self) -> List[str]:
        """列出所有可用的评估维度"""
        if self._dimensions_cache is not None:
            return self._dimensions_cache

        dimensions = []
        if self.general_rules_dir.exists():
            for f in self.general_rules_dir.glob("*.md"):
                dimensions.append(f.stem)  # 文件名（不含扩展名）即为维度名

        self._dimensions_cache = sorted(dimensions)
        logger.info(f"发现 {len(self._dimensions_cache)} 个通用评估维度")
        return self._dimensions_cache

    def get_rule(self, dimension: str) -> Optional[str]:
        """获取指定维度的规则内容"""
        rule_file = self.general_rules_dir / f"{dimension}.md"
        if not rule_file.exists():
            logger.warning(f"规则文件不存在: {rule_file}")
            return None

        try:
            with open(rule_file, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"加载规则: {dimension}, 长度={len(content)}")
            return content
        except Exception as e:
            logger.error(f"读取规则文件失败: {rule_file}, error={e}")
            return None

    def get_department_rules(self, department: str) -> Dict[str, str]:
        """获取指定部门的个性化规则"""
        dept_dir = self.department_rules_dir / department
        rules = {}

        if not dept_dir.exists():
            logger.warning(f"部门规则目录不存在: {dept_dir}")
            return rules

        for f in dept_dir.glob("*.md"):
            dimension = f.stem
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    rules[dimension] = fp.read()
            except Exception as e:
                logger.error(f"读取部门规则文件失败: {f}, error={e}")

        logger.info(f"加载部门 {department} 的 {len(rules)} 个个性化规则")
        return rules

    def list_departments(self) -> List[str]:
        """列出所有可用的部门"""
        if self._department_cache is not None:
            return self._department_cache

        departments = []
        if self.department_rules_dir.exists():
            for d in self.department_rules_dir.iterdir():
                if d.is_dir():
                    departments.append(d.name)

        self._department_cache = sorted(departments)
        logger.info(f"发现 {len(self._department_cache)} 个部门个性化规则")
        return self._department_cache


# 全局规则提供者实例
_rule_provider: Optional[RuleProvider] = None


def get_rule_provider() -> RuleProvider:
    """获取规则提供者实例"""
    global _rule_provider
    if _rule_provider is None:
        _rule_provider = LocalFileRuleProvider()
    return _rule_provider


def set_rule_provider(provider: RuleProvider):
    """设置规则提供者（用于测试或扩展）"""
    global _rule_provider
    _rule_provider = provider


# 便捷函数
def list_available_dimensions() -> List[str]:
    """列出所有可用的评估维度"""
    return get_rule_provider().list_dimensions()


def get_dimension_rules(dimension: str) -> Optional[str]:
    """获取指定维度的规则"""
    return get_rule_provider().get_rule(dimension)


def get_personalized_department_rules(department: str) -> Dict[str, str]:
    """获取指定部门的个性化规则"""
    return get_rule_provider().get_department_rules(department)


def list_available_departments() -> List[str]:
    """列出所有可用的部门"""
    return get_rule_provider().list_departments()