"""数据库模块"""
import sqlite3
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from loguru import logger

from .models import EvaluationResult, DimensionScore, EvaluationStatus, EvaluationSource


class Database:
    """SQLite数据库管理"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 评估结果表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id TEXT NOT NULL,
                requirement_title TEXT,
                department TEXT,
                system TEXT,
                source TEXT NOT NULL,
                dimension TEXT,
                score REAL,
                level TEXT,
                issues TEXT,
                suggestions TEXT,
                evidence TEXT,
                overall_score REAL,
                overall_level TEXT,
                dimensions_evaluated TEXT,
                evaluation_time TEXT,
                evaluation_duration REAL,
                raw_llm_output TEXT,
                status TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_requirement_id ON evaluations(requirement_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_department ON evaluations(department)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source ON evaluations(source)
        """)

        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成: {self.db_path}")

    def save_evaluation(self, result: EvaluationResult) -> int:
        """保存评估结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for dim_score in result.dimension_scores:
            cursor.execute("""
                INSERT INTO evaluations (
                    requirement_id, requirement_title, department, system,
                    source, dimension, score, level, issues, suggestions,
                    evidence, overall_score, overall_level, dimensions_evaluated,
                    evaluation_time, evaluation_duration, raw_llm_output,
                    status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.requirement_id,
                result.requirement_title,
                result.department,
                result.system,
                result.source.value,
                dim_score.dimension,
                dim_score.score,
                dim_score.level,
                json.dumps(dim_score.issues, ensure_ascii=False),
                json.dumps(dim_score.suggestions, ensure_ascii=False),
                dim_score.evidence,
                result.overall_score,
                result.overall_level,
                json.dumps(result.dimensions_evaluated, ensure_ascii=False),
                result.evaluation_time.isoformat() if result.evaluation_time else None,
                result.evaluation_duration,
                result.raw_llm_output,
                result.status.value,
                result.error_message
            ))

        conn.commit()
        conn.close()
        logger.info(f"评估结果已保存: requirement_id={result.requirement_id}, dimension_count={len(result.dimension_scores)}")
        return len(result.dimension_scores)

    def get_evaluation(self, requirement_id: str, source: Optional[EvaluationSource] = None) -> Optional[EvaluationResult]:
        """获取评估结果"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if source:
            cursor.execute("""
                SELECT * FROM evaluations
                WHERE requirement_id = ? AND source = ?
                ORDER BY id
            """, (requirement_id, source.value))
        else:
            cursor.execute("""
                SELECT * FROM evaluations
                WHERE requirement_id = ?
                ORDER BY id
            """, (requirement_id,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        # 构建结果
        first_row = dict(rows[0])
        dimension_scores = []

        for row in rows:
            row_dict = dict(row)
            dimension_scores.append(DimensionScore(
                dimension=row_dict['dimension'],
                score=row_dict['score'],
                level=row_dict['level'],
                issues=json.loads(row_dict['issues']) if row_dict['issues'] else [],
                suggestions=json.loads(row_dict['suggestions']) if row_dict['suggestions'] else [],
                evidence=row_dict['evidence'] or ""
            ))

        result = EvaluationResult(
            requirement_id=first_row['requirement_id'],
            requirement_title=first_row['requirement_title'],
            department=first_row['department'],
            system=first_row['system'],
            source=EvaluationSource(first_row['source']),
            dimension_scores=dimension_scores,
            overall_score=first_row['overall_score'],
            overall_level=first_row['overall_level'],
            dimensions_evaluated=json.loads(first_row['dimensions_evaluated']) if first_row['dimensions_evaluated'] else [],
            evaluation_time=datetime.fromisoformat(first_row['evaluation_time']) if first_row['evaluation_time'] else None,
            evaluation_duration=first_row['evaluation_duration'],
            raw_llm_output=first_row['raw_llm_output'],
            status=EvaluationStatus(first_row['status']),
            error_message=first_row['error_message']
        )

        return result

    def list_evaluations(self, limit: int = 100) -> List[str]:
        """列出所有评估过的需求ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT requirement_id FROM evaluations
            ORDER BY created_at DESC LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]

    def delete_evaluation(self, requirement_id: str) -> int:
        """删除评估结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM evaluations WHERE requirement_id = ?", (requirement_id,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"删除评估结果: requirement_id={requirement_id}, deleted_count={deleted}")
        return deleted