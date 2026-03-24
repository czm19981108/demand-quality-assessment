"""使用示例"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.workflow import run_evaluation
from src.rule_loader import list_available_dimensions


# 示例需求文档
SAMPLE_REQUIREMENT = """
# 电商平台用户登录功能需求

## 背景
随着电商平台用户量不断增长，需要优化用户体验，提升登录转化率。

## 功能需求
1. 用户名密码登录
2. 手机验证码登录
3. 微信一键登录
4. 第三方账号绑定（支付宝、Google、Facebook）
5. 记住密码功能
6. 自动登录功能

## 业务流程
1. 用户打开登录页面
2. 选择登录方式
3. 输入账号信息
4. 系统验证
5. 登录成功跳转首页

## 非功能性需求
1. 登录响应时间 < 2秒
2. 支持高并发
3. 密码加密存储
4. 防止暴力破解

## 风险点
1. 第三方登录回调失败处理
2. 验证码短信延迟
3. 并发登录冲突
"""


def main():
    """运行评估示例"""
    print("=" * 60)
    print("需求文档质量评估系统 - 使用示例")
    print("=" * 60)

    # 查看可用维度
    print("\n1. 查看可用评估维度...")
    dimensions = list_available_dimensions()
    print(f"   共 {len(dimensions)} 个维度")

    # 方式1: 评估所有维度
    print("\n2. 运行完整评估（所有维度）...")
    print("   (由于需要调用 LLM API，这里仅展示调用方式)")
    print()
    print("   # 完整调用方式:")
    print("""
from src.workflow import run_evaluation

result = run_evaluation(
    requirement_content=requirement_content,
    requirement_id="REQ001",
    requirement_title="用户登录功能",
    department="电商",  # 可选，自动提取
    system="用户中心",   # 可选
    # dimensions=["功能完整性", "安全性"],  # 可选，评估指定维度
    # enable_personalized=True  # 是否启用个性化评估
)

print(f"总体评分: {result['overall_score']}")
print(f"总体等级: {result['overall_level']}")
print(f"评估维度数: {len(result['dimension_scores'])}")
""")

    # 方式2: 评估指定维度
    print("\n3. 评估指定维度...")
    print("   # 评估特定维度:")
    print("""
result = run_evaluation(
    requirement_content=requirement_content,
    dimensions=["功能完整性", "安全性", "性能压力完整性"]
)
""")

    # 显示示例内容
    print("\n4. 示例需求文档内容预览:")
    print("-" * 60)
    print(SAMPLE_REQUIREMENT[:500] + "...")
    print("-" * 60)

    print("\n注意: 实际运行需要:")
    print("   1. 安装依赖: pip install -r requirements.txt")
    print("   2. 配置 .req-check.json 中的 LLM API")
    print("   3. 确保内网环境可以访问 API")


if __name__ == "__main__":
    main()