"""存储节点"""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from ..database import Database
from ..models import EvaluationResult, DimensionScore, EvaluationSource, EvaluationStatus
from ..config import config


# 全局数据库实例
_db = None


def get_database() -> Database:
    """获取数据库实例"""
    global _db
    if _db is None:
        _db = Database(config.db_path)
    return _db


def storage_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """存储节点

    该节点负责将评估结果存储到数据库。

    输入状态:
        - requirement_id: 需求ID
        - requirement_title: 需求标题
        - department: 部门
        - system: 系统
        - source: 评估来源 (general/personalized)
        - dimension_scores: 评估结果列表
        - overall_score: 总体评分
        - overall_level: 总体等级
        - dimensions_evaluated: 已评估的维度列表
        - evaluation_duration: 评估耗时

    输出状态:
        - stored: 是否存储成功
        - error: 错误信息（如有）
    """
    requirement_id = state.get("requirement_id", "unknown")
    requirement_title = state.get("requirement_title", "")
    department = state.get("department")
    system = state.get("system")
    source = state.get("source", "general")
    dimension_scores_data = state.get("dimension_scores", [])
    overall_score = state.get("overall_score", 0)
    overall_level = state.get("overall_level", "未评估")
    dimensions_evaluated = state.get("dimensions_evaluated", [])
    evaluation_duration = state.get("evaluation_duration")
    raw_llm_output = state.get("llm_output")

    logger.info(f"开始存储评估结果: requirement_id={requirement_id}, source={source}")

    try:
        # 转换 dimension_scores
        dimension_scores = []
        for score_data in dimension_scores_data:
            if isinstance(score_data, dict):
                dimension_scores.append(DimensionScore(**score_data))
            elif isinstance(score_data, DimensionScore):
                dimension_scores.append(score_data)

        # 构建评估结果
        result = EvaluationResult(
            requirement_id=requirement_id,
            requirement_title=requirement_title,
            department=department,
            system=system,
            source=EvaluationSource(source) if isinstance(source, str) else source,
            dimension_scores=dimension_scores,
            overall_score=overall_score,
            overall_level=overall_level,
            dimensions_evaluated=dimensions_evaluated,
            evaluation_time=datetime.now(),
            evaluation_duration=evaluation_duration,
            raw_llm_output=raw_llm_output,
            status=EvaluationStatus.COMPLETED
        )

        # 存储到数据库
        db = get_database()
        db.save_evaluation(result)

        logger.info(f"评估结果存储成功: requirement_id={requirement_id}, dimension_count={len(dimension_scores)}")

        return {
            "stored": True,
            "error": None
        }

    except Exception as e:
        logger.error(f"存储评估结果失败: {e}")
        return {
            "stored": False,
            "error": str(e)
        }


def create_storage_node():
    """创建存储节点（供 LangGraph 使用）"""
    return storage_node


def get_stored_evaluation(requirement_id: str, source: str = None) -> EvaluationResult:
    """获取已存储的评估结果"""
    db = get_database()
    return db.get_evaluation(requirement_id, source)


def list_evaluations(limit: int = 100) -> List[str]:
    """列出所有评估过的需求ID"""
    db = get_database()
    return db.list_evaluations(limit)


def delete_evaluation(requirement_id: str) -> int:
    """删除评估结果"""
    db = get_database()
    return db.delete_evaluation(requirement_id)