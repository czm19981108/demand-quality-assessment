"""配置管理模块"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger


class Config:
    """配置管理类"""

    _instance = None

    def __new__(cls, config_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if self._initialized:
            return

        if config_path is None:
            # 默认查找当前目录和父目录的配置文件
            current_dir = Path.cwd()
            possible_paths = [
                current_dir / ".req-check.json",
                current_dir.parent / ".req-check.json",
                Path(__file__).parent.parent / ".req-check.json",
            ]
            for p in possible_paths:
                if p.exists():
                    config_path = str(p)
                    break

        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"配置加载成功: {config_path}")
        else:
            logger.warning("未找到配置文件，使用默认配置")
            self._config = self._get_default_config()

        self._initialized = True

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0.0",
            "rules_dir": "rules",
            "general_rules_dir": "rules/general",
            "department_rules_dir": "rules/departments",
            "data_dir": "data",
            "db_path": "data/evaluations.db",
            "llm": {
                "provider": "openai",
                "model": "MiniMax-M2.1",
                "base_url": os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
                "api_key": os.getenv("LLM_API_KEY", "dummy-key"),
                "temperature": 0.1,
                "max_tokens": 4096
            },
            "embedding": {
                "provider": "openai",
                "model": "text-embedding-3-small",
                "base_url": os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
                "api_key": os.getenv("LLM_API_KEY", "dummy-key")
            },
            "department_keywords": {},
            "evaluation": {
                "default_dimension": "功能完整性",
                "max_retries": 3,
                "retry_delay": 2,
                "enable_personalized": True
            },
            "report": {
                "output_dir": "data/reports",
                "format": "markdown"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    @property
    def rules_dir(self) -> str:
        return self.get("rules_dir", "rules")

    @property
    def general_rules_dir(self) -> str:
        return self.get("general_rules_dir", "rules/general")

    @property
    def department_rules_dir(self) -> str:
        return self.get("department_rules_dir", "rules/departments")

    @property
    def db_path(self) -> str:
        return self.get("db_path", "data/evaluations.db")

    @property
    def llm_config(self) -> Dict:
        return self.get("llm", {})

    @property
    def embedding_config(self) -> Dict:
        return self.get("embedding", {})

    @property
    def department_keywords(self) -> Dict[str, List[str]]:
        return self.get("department_keywords", {})

    @property
    def evaluation_config(self) -> Dict:
        return self.get("evaluation", {})

    @property
    def report_config(self) -> Dict:
        return self.get("report", {})

    @property
    def llm_model(self) -> str:
        return self.get("llm.model", "gpt-4")

    @property
    def llm_base_url(self) -> str:
        return self.get("llm.base_url", "http://localhost:8000/v1")

    @property
    def llm_api_key(self) -> str:
        return self.get("llm.api_key", "dummy-key")

    @property
    def llm_temperature(self) -> float:
        return self.get("llm.temperature", 0.1)

    @property
    def llm_max_tokens(self) -> int:
        return self.get("llm.max_tokens", 4096)


# 全局配置实例
config = Config()