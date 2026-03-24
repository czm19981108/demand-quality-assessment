"""LLM 客户端封装"""
from typing import Optional, Dict, Any
from loguru import logger

from .config import config

# 延迟导入 langchain，避免未安装时报错
_langchain_available = False
_llm_client = None


def _check_langchain():
    """检查 langchain 是否可用"""
    global _langchain_available
    if _langchain_available:
        return True

    try:
        from langchain_openai import ChatOpenAI
        _langchain_available = True
        return True
    except ImportError:
        logger.warning("langchain-openai 未安装，请运行: pip install langchain-openai")
        return False


def get_llm_client():
    """获取 LLM 客户端实例"""
    global _llm_client

    if _llm_client is not None:
        return _llm_client

    if not _check_langchain():
        raise RuntimeError("langchain-openai 未安装")

    from langchain_openai import ChatOpenAI

    llm_config = config.llm_config

    _llm_client = ChatOpenAI(
        model=llm_config.get("model", "gpt-4"),
        base_url=llm_config.get("base_url", "http://localhost:8000/v1"),
        api_key=llm_config.get("api_key", "dummy-key"),
        temperature=llm_config.get("temperature", 0.1),
        max_tokens=llm_config.get("max_tokens", 4096),
        timeout=llm_config.get("timeout", 120),
    )

    logger.info(f"LLM 客户端初始化完成: model={llm_config.get('model')}")
    return _llm_client


def call_llm(prompt: str, **kwargs) -> str:
    """调用 LLM 生成响应

    Args:
        prompt: 提示词
        **kwargs: 额外参数

    Returns:
        LLM 生成的文本响应
    """
    llm = get_llm_client()

    # 合并参数
    llm_params = {
        "temperature": kwargs.get("temperature", config.llm_temperature),
        "max_tokens": kwargs.get("max_tokens", config.llm_max_tokens),
    }

    try:
        response = llm.invoke(prompt, **llm_params)
        content = response.content if hasattr(response, 'content') else str(response)
        logger.debug(f"LLM 响应长度: {len(content)}")
        return content
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        raise


def reset_llm_client():
    """重置 LLM 客户端（用于测试或切换配置）"""
    global _llm_client
    _llm_client = None