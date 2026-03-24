"""测试脚本"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rule_loader import (
    list_available_dimensions,
    get_dimension_rules,
    get_personalized_department_rules,
    list_available_departments
)
from src.extract_department import extract_department
from src.config import config


def test_list_dimensions():
    """测试列出所有维度"""
    print("=" * 50)
    print("测试: 列出所有评估维度")
    print("=" * 50)

    dimensions = list_available_dimensions()
    print(f"共发现 {len(dimensions)} 个评估维度:")
    for i, dim in enumerate(dimensions, 1):
        print(f"  {i}. {dim}")

    print()
    return dimensions


def test_get_rules(dimensions):
    """测试获取规则"""
    print("=" * 50)
    print("测试: 获取指定维度的规则")
    print("=" * 50)

    # 测试获取功能完整性规则
    if "功能完整性" in dimensions:
        rule = get_dimension_rules("功能完整性")
        print(f"规则内容 (功能完整性, 前500字符):\n{rule[:500]}...")
    else:
        # 使用第一个维度
        dim = dimensions[0]
        rule = get_dimension_rules(dim)
        print(f"规则内容 ({dim}, 前500字符):\n{rule[:500]}...")

    print()
    return rule


def test_extract_department():
    """测试部门提取"""
    print("=" * 50)
    print("测试: 提取部门/系统信息")
    print("=" * 50)

    # 测试1: YAML frontmatter
    content1 = """---
department: 电商
system: 订单系统
---
# 订单管理需求

需求描述：...
"""
    dept, sys = extract_department(content1)
    print(f"YAML 方式提取: department={dept}, system={sys}")

    # 测试2: 关键词匹配
    content2 = """
# 用户登录功能需求

本系统需要支持用户通过手机号和验证码进行登录，
同时支持微信登录和第三方账号绑定...
"""
    dept, sys = extract_department(content2, title="用户登录功能需求")
    print(f"关键词匹配提取: department={dept}, system={sys}")

    # 测试3: 手动指定
    content3 = "这是一个普通的需求文档"
    dept, sys = extract_department(content3, department="金融")
    print(f"手动指定提取: department={dept}, system={sys}")

    print()
    return dept


def test_config():
    """测试配置"""
    print("=" * 50)
    print("测试: 配置信息")
    print("=" * 50)
    print(f"规则目录: {config.rules_dir}")
    print(f"通用规则目录: {config.general_rules_dir}")
    print(f"部门规则目录: {config.department_rules_dir}")
    print(f"数据库路径: {config.db_path}")
    print(f"LLM 模型: {config.llm_model}")
    print(f"LLM API: {config.llm_base_url}")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("需求文档质量评估系统 - 测试")
    print("=" * 50 + "\n")

    try:
        # 测试配置
        test_config()

        # 测试列出维度
        dimensions = test_list_dimensions()

        # 测试获取规则
        test_get_rules(dimensions)

        # 测试部门提取
        test_extract_department()

        print("=" * 50)
        print("所有测试完成!")
        print("=" * 50)

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()