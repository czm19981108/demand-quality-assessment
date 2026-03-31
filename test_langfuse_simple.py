"""简化的 Langfuse 验证测试 - 只评估 2 个维度，快速验证配置"""
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# 加载环境变量（Langfuse 配置）
load_dotenv()

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.workflow_langfuse import run_evaluation, get_langfuse, LANGFUSE_AVAILABLE


# 简单示例需求文档
SAMPLE_REQUIREMENT = """
# 用户登录功能需求

需要实现用户登录功能，支持用户名密码登录和短信验证码登录。

功能要点：
1. 用户可以输入用户名和密码进行登录
2. 用户可以选择使用手机号接收验证码登录
3. 登录成功后跳转至首页
4. 提供"记住我"选项

非功能需求：
- 登录响应时间不超过2秒
- 密码需要加密存储
"""


def main():
    """运行简化的 Langfuse 验证测试"""
    print("=" * 60)
    print("需求质量评估 - Langfuse 连通性验证测试")
    print("=" * 60)

    # 检查环境变量
    print("\n[1] 检查环境变量配置:")
    langfuse_host = os.getenv("LANGFUSE_HOST")
    langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")

    print(f"   LANGFUSE_HOST: {langfuse_host or '未设置'}")
    print(f"   LANGFUSE_SECRET_KEY: {'*' * 20 if langfuse_secret else '未设置'}")
    print(f"   LANGFUSE_PUBLIC_KEY: {'*' * 16 if langfuse_public else '未设置'}")

    print("\n[2] 检查 Langfuse SDK 状态:")
    print(f"   Langfuse SDK 已安装: {LANGFUSE_AVAILABLE}")

    if not LANGFUSE_AVAILABLE:
        print("   [FAILED] Langfuse SDK 未安装，请运行: pip install langfuse")
        sys.exit(1)

    client = get_langfuse()
    if client:
        print("   [OK] Langfuse 客户端初始化成功")
    else:
        print("   [FAILED] Langfuse 客户端初始化失败，请检查 API Key 和 Host 配置")
        print("      继续测试 LLM 调用，但追踪不会上报到 Langfuse")

    print("\n[3] 开始简化评估测试（只评估 2 个维度）:")
    print(f"   只测试: 功能完整性, 安全完整性")

    try:
        result = run_evaluation(
            requirement_content=SAMPLE_REQUIREMENT,
            requirement_id="LANGFUSE-VALIDATION-TEST",
            requirement_title="用户登录功能-简化测试",
            dimensions=["功能完整性", "安全完整性"],
            enable_personalized=False
        )

        print("\n[4] 评估完成!")
        print(f"   总体评分: {result.get('overall_score', 0):.2f}")
        print(f"   评估维度数: {len(result.get('dimensions_evaluated', []))}")
        print(f"   耗时: {result.get('evaluation_duration', 0):.2f} 秒")

        if result.get('error'):
            print(f"   [WARNING] 错误: {result['error']}")

        print("\n[5] 维度评分:")
        for score in result.get('dimension_scores', []):
            print(f"   - {score.get('dimension')}: {score.get('score')} 分")

        # 强制刷新 Langfuse
        if client:
            client.flush()
            print("\n[SUCCESS] 测试完成! 请打开 Langfuse UI 查看追踪数据。")
            print(f"   地址: {langfuse_host}")
            print("   在 Traces 页面可以看到完整的调用链：")
            print("   - demand_quality_evaluation (root trace)")
            print("   ├─ init_evaluation")
            print("   ├─ extract_department_info")
            print("   ├─ prepare_dimensions")
            print("   ├─ select_next_dimension ×2")
            print("   ├─ load_rule ×2")
            print("   ├─ evaluate_dimension ×2")
            print("   │  └─ LLM 调用（自动追踪 token/latency）")
            print("   ├─ aggregate_results")
            print("   ├─ save_results")
            print("   └─ generate_report")
        else:
            print("\n[WARNING] Langfuse 客户端未连接成功，但 LLM 评估已完成")

    except Exception as e:
        print("\n[FAILED] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
