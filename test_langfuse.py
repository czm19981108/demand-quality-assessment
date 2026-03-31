"""测试 Langfuse 追踪 + 修复后的 LLM API 配置"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.workflow_langfuse import run_evaluation, get_langfuse, LANGFUSE_AVAILABLE


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
    """运行带 Langfuse 追踪的评估测试"""
    print("=" * 70)
    print("需求文档质量评估系统 - Langfuse 可观测性测试")
    print("=" * 70)

    print(f"\n[1/4] Langfuse 状态检查...")
    print(f"   Langfuse SDK 可用: {LANGFUSE_AVAILABLE}")
    if LANGFUSE_AVAILABLE:
        client = get_langfuse()
        if client:
            print(f"   Langfuse 客户端已初始化")
        else:
            print(f"   ⚠️  Langfuse 客户端初始化失败，检查环境变量配置")

    print(f"\n[2/4] 开始运行评估（前 3 个维度测试）...")
    print(f"   需求标题: 电商平台用户登录功能")
    print(f"   需求长度: {len(SAMPLE_REQUIREMENT)} 字符")

    # 只评估几个维度来测试，避免耗时过长
    test_dimensions = ["完整性", "一致性", "准确性"]

    try:
        result = run_evaluation(
            requirement_content=SAMPLE_REQUIREMENT,
            requirement_id="REQ-LANGFUSE-TEST-001",
            requirement_title="电商平台用户登录功能",
            department="电商",
            system="用户中心",
            dimensions=test_dimensions,
            enable_personalized=True
        )

        print(f"\n[3/4] 评估完成!")
        print(f"   总体评分: {result.get('overall_score', 0):.2f}")
        print(f"   总体等级: {result.get('overall_level', '未知')}")
        print(f"   评估维度数: {len(result.get('dimensions_evaluated', []))}")
        print(f"   耗时: {result.get('evaluation_duration', 0):.2f} 秒")

        if result.get('error'):
            print(f"   ⚠️  评估过程出现错误: {result['error']}")

        print(f"\n[4/4] 维度详情:")
        for i, score in enumerate(result.get('dimension_scores', []), 1):
            print(f"   {i}. {score.get('dimension')}: {score.get('score')} 分")
            if score.get('feedback'):
                print(f"      反馈: {score.get('feedback')[:100]}...")

        print(f"\n✅ 测试完成! 请打开 Langfuse UI (http://localhost:3001) 查看追踪数据。")

        # 确保 Langfuse 刷新发送
        if LANGFUSE_AVAILABLE:
            client = get_langfuse()
            if client:
                client.flush_async()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
