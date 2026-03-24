"""评估提示词模板"""

# 维度评估提示词
DIMENSION_EVALUATION_PROMPT = """你是一个专业的需求文档评审专家。请根据以下规则对需求文档进行质量评估。

## 评估维度
{dimension_name}

## 评估规则
{rule_content}

## 需求文档
{requirement_content}

## 评估要求
1. 仔细阅读需求文档内容
2. 根据评估规则，评估需求文档在该维度的表现
3. 输出评估结果，包括：
   - 评分 (0-100分)
   - 等级 (优秀/良好/一般/较差/差)
   - 发现的问题 (如有)
   - 改进建议 (如有)
   - 评估依据

## 输出格式 (JSON)
请严格按照以下JSON格式输出，不要添加任何额外内容：
{{
    "score": <评分0-100>,
    "level": "<等级>",
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "evidence": "评估依据描述"
}}

注意：
- score 必须是一个数字 (0-100)
- level 必须是以下之一：优秀、良好、一般、较差、差
- issues 和 suggestions 是字符串数组，可以为空数组 []
- evidence 是评估依据的简要描述"""

# 多维度评估提示词
MULTI_DIMENSION_EVALUATION_PROMPT = """你是一个专业的需求文档评审专家。请根据以下规则对需求文档进行多维度质量评估。

## 评估维度列表
{dimensions_list}

## 评估规则
{rule_contents}

## 需求文档
{requirement_content}

## 评估要求
1. 仔细阅读需求文档内容
2. 对每个评估维度分别进行评估
3. 输出每个维度的评估结果

## 输出格式 (JSON数组)
请严格按照以下JSON格式输出：
[
    {{
        "dimension": "维度名称",
        "score": <评分0-100>,
        "level": "<等级>",
        "issues": ["问题1"],
        "suggestions": ["建议1"],
        "evidence": "评估依据"
    }},
    ...
]

注意：
- 每个维度都需要有完整的评估结果
- score 必须是一个数字 (0-100)
- level 必须是以下之一：优秀、良好、一般、较差、差"""

# 通用信息提取提示词
EXTRACT_DEPARTMENT_PROMPT = """请从以下需求文档中识别出所属的部门或系统。

## 需求文档
{requirement_content}

## 可选部门
{departments_list}

## 输出格式 (JSON)
{{
    "department": "<识别的部门，如果没有匹配的返回null>",
    "confidence": "<置信度 0-1>",
    "reason": "识别理由"
}}"""

# 综合报告生成提示词
REPORT_GENERATION_PROMPT = """请根据以下评估结果生成一份需求文档质量评估报告。

## 需求文档信息
- 需求ID: {requirement_id}
- 需求标题: {requirement_title}
- 所属部门: {department}
- 所属系统: {system}

## 评估结果
{evaluation_results}

## 评估摘要
- 总体评分: {overall_score}
- 总体等级: {overall_level}
- 已评估维度数: {dimension_count}

## 输出要求
请生成一份结构清晰、内容完整的评估报告，包括：
1. 评估概述
2. 各维度详细评估结果
3. 发现的主要问题
4. 改进建议
5. 总结

请使用 Markdown 格式输出报告。"""


def get_dimension_prompt(dimension: str, rule: str, requirement: str) -> str:
    """获取单维度评估提示词"""
    return DIMENSION_EVALUATION_PROMPT.format(
        dimension_name=dimension,
        rule_content=rule,
        requirement_content=requirement
    )


def get_multi_dimension_prompt(dimensions: list, rules: dict, requirement: str) -> str:
    """获取多维度评估提示词"""
    dimensions_list = "\n".join([f"- {d}" for d in dimensions])

    rule_contents = "\n\n".join([
        f"## {dim}\n{rules.get(dim, '无规则')}"
        for dim in dimensions
    ])

    return MULTI_DIMENSION_EVALUATION_PROMPT.format(
        dimensions_list=dimensions_list,
        rule_contents=rule_contents,
        requirement_content=requirement
    )


def get_extract_department_prompt(requirement: str, departments: list) -> str:
    """获取部门提取提示词"""
    departments_list = ", ".join(departments) if departments else "无特定部门"

    return EXTRACT_DEPARTMENT_PROMPT.format(
        requirement_content=requirement,
        departments_list=departments_list
    )


def get_report_prompt(
    requirement_id: str,
    requirement_title: str,
    department: str,
    system: str,
    evaluation_results: str,
    overall_score: float,
    overall_level: str,
    dimension_count: int
) -> str:
    """获取报告生成提示词"""
    return REPORT_GENERATION_PROMPT.format(
        requirement_id=requirement_id,
        requirement_title=requirement_title,
        department=department or "未识别",
        system=system or "未识别",
        evaluation_results=evaluation_results,
        overall_score=overall_score,
        overall_level=overall_level,
        dimension_count=dimension_count
    )