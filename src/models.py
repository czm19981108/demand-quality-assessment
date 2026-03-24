"""数据模型定义"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EvaluationSource(str, Enum):
    """评估来源类型"""
    GENERAL = "general"       # 通用规则评估
    PERSONALIZED = "personalized"  # 个性化规则评估


class EvaluationStatus(str, Enum):
    """评估状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DimensionScore(BaseModel):
    """维度评分"""
    dimension: str = Field(..., description="维度名称")
    score: float = Field(..., ge=0, le=100, description="评分 0-100")
    level: str = Field(..., description="等级: 优秀/良好/一般/较差/差")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    evidence: str = Field("", description="评估依据")


class EvaluationResult(BaseModel):
    """评估结果"""
    requirement_id: str = Field(..., description="需求文档ID")
    requirement_title: str = Field(..., description="需求标题")
    department: Optional[str] = Field(None, description="所属部门")
    system: Optional[str] = Field(None, description="所属系统")
    source: EvaluationSource = Field(EvaluationSource.GENERAL, description="评估来源")

    # 评估结果
    dimension_scores: List[DimensionScore] = Field(default_factory=list)
    overall_score: float = Field(0, ge=0, le=100, description="总体评分")
    overall_level: str = Field("未评估", description="总体等级")

    # 元数据
    dimensions_evaluated: List[str] = Field(default_factory=list, description="已评估的维度")
    evaluation_time: Optional[datetime] = None
    evaluation_duration: Optional[float] = None  # 秒

    # 原始输出
    raw_llm_output: Optional[str] = None

    # 状态
    status: EvaluationStatus = Field(EvaluationStatus.PENDING, description="评估状态")
    error_message: Optional[str] = None


class EvaluationRequest(BaseModel):
    """评估请求"""
    requirement_content: str = Field(..., description="需求文档内容")
    requirement_id: Optional[str] = Field(None, description="需求文档ID")
    requirement_title: Optional[str] = Field(None, description="需求标题")

    # 部门/系统信息
    department: Optional[str] = Field(None, description="指定部门")
    system: Optional[str] = Field(None, description="指定系统")

    # 评估选项
    dimensions: Optional[List[str]] = Field(None, description="指定评估维度，为空则评估所有")
    enable_personalized: bool = Field(True, description="是否启用个性化评估")


class Report(BaseModel):
    """评估报告"""
    requirement_id: str
    requirement_title: str
    department: Optional[str] = None
    system: Optional[str] = None

    # 评估摘要
    overall_score: float
    overall_level: str
    dimensions_evaluated: List[str]

    # 详细结果
    general_results: List[DimensionScore] = Field(default_factory=list)
    personalized_results: List[DimensionScore] = Field(default_factory=list)

    # 元数据
    generated_at: datetime
    evaluation_duration: Optional[float] = None