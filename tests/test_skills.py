"""渐进式 Skills 测试"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.skills.dimension_skills import (
    get_quality_dimension_rules,
    list_available_dimensions,
    get_personalized_department_rules,
    list_available_departments,
    get_progressive_evaluation_workflow
)
from src.skills.agent_integration import (
    get_skills_agent,
    get_tool_schemas,
    call_skill
)


def test_list_available_dimensions():
    """测试 Skill 2: 列出所有可用维度"""
    print("=" * 60)
    print("测试: list_available_dimensions")
    print("=" * 60)

    # 不带描述
    result = list_available_dimensions()
    print(f"成功: {result.success}")
    print(f"维度数量: {result.data['total_count']}")
    print(f"维度列表: {result.data['dimensions'][:5]}...")  # 只显示前5个

    # 带描述
    result_with_desc = list_available_dimensions(include_descriptions=True)
    print(f"\n包含描述的维度示例:")
    dims = result_with_desc.data['descriptions']
    for dim in list(dims.keys())[:3]:
        print(f"  - {dim}: {dims[dim]}")

    print()
    return result


def test_get_quality_dimension_rules():
    """测试 Skill 1: 获取指定维度规则"""
    print("=" * 60)
    print("测试: get_quality_dimension_rules")
    print("=" * 60)

    # 测试存在的维度
    result = get_quality_dimension_rules("功能完整性")
    print(f"成功: {result.success}")
    print(f"维度: {result.data['dimension']}")
    print(f"规则长度: {result.data['rule_length']}")
    print(f"规则内容预览:\n{result.data['rule'][:300]}...")

    # 测试不存在的维度
    result_not_exist = get_quality_dimension_rules("不存在的维度")
    print(f"\n测试不存在的维度: 成功={result_not_exist.success}, 错误={result_not_exist.error}")

    print()
    return result


def test_get_personalized_department_rules():
    """测试 Skill 3: 获取部门个性化规则"""
    print("=" * 60)
    print("测试: get_personalized_department_rules")
    print("=" * 60)

    # 测试不存在的部门
    result = get_personalized_department_rules("电商")
    print(f"成功: {result.success}")
    print(f"部门: {result.data.get('department')}")
    print(f"消息: {result.data.get('message')}")
    print(f"规则数量: {result.data.get('rule_count', 0)}")

    print()
    return result


def test_skills_agent():
    """测试 SkillsAgent"""
    print("=" * 60)
    print("测试: SkillsAgent")
    print("=" * 60)

    agent = get_skills_agent()

    # 获取工具定义
    tools = agent.get_tool_definitions()
    print(f"工具数量: {len(tools)}")
    print(f"工具列表: {[t['function']['name'] for t in tools]}")

    # 调用工具
    result = agent.call_tool("list_available_dimensions")
    print(f"\n调用 list_available_dimensions: 成功={result.success}")

    # 直接调用 skill
    result2 = call_skill("get_quality_dimension_rules", dimension="易读性")
    print(f"调用 get_quality_dimension_rules: 成功={result2.success}")

    print()
    return agent


def test_progressive_workflow():
    """测试渐进式工作流"""
    print("=" * 60)
    print("测试: 渐进式评估工作流")
    print("=" * 60)

    workflow = get_progressive_evaluation_workflow()

    print("工作流步骤:")
    for step in workflow['workflow']:
        print(f"  {step['step']}. {step['action']}")
        print(f"     {step['description']}")

    print("\n原则:")
    for principle in workflow['principles']:
        print(f"  - {principle}")

    print()
    return workflow


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("渐进式规则知识获取 Skills - 测试")
    print("=" * 60 + "\n")

    try:
        # 测试各个 Skill
        test_list_available_dimensions()
        test_get_quality_dimension_rules()
        test_get_personalized_department_rules()

        # 测试 Agent 集成
        test_skills_agent()

        # 测试工作流
        test_progressive_workflow()

        print("=" * 60)
        print("所有测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()