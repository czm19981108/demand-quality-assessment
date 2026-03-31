# Laminar 可观测性集成

本项目集成了 Laminar，用于追踪需求文档质量评估的完整工作流程。

## 功能

- **完整调用链追踪**：查看每个节点的执行顺序和耗时
- **性能指标**：每个节点的延迟、Token 消耗等
- **可视化界面**：图形化展示工作流程
- **自托管**：支持本地部署，无需云服务

## 快速开始

### 1. 启动本地 Laminar

```bash
# 进入 Laminar 项目目录
cd ../lmnr-project

# 启动 Laminar 服务
docker compose up -d
```

访问 http://localhost:5667 打开 Laminar UI。

### 2. 配置环境变量

```bash
# 复制配置
cp .env.example .env

# 编辑 .env，确保包含:
LMNR_PROJECT_API_KEY=local-dev
```

### 3. 运行评估

```python
from src.workflow_observed import run_evaluation

result = run_evaluation(
    requirement_content="""
# 用户登录功能需求

## 功能需求
1. 用户名密码登录
2. 手机验证码登录
3. 微信一键登录
""",
    requirement_id="REQ001",
    requirement_title="用户登录功能"
)

print(f"总体评分: {result['overall_score']}")
print(f"评估耗时: {result['evaluation_duration']}s")
```

### 4. 查看追踪

1. 打开 http://localhost:5667
2. 在 Traces 面板查看完整调用链
3. 点击每个节点查看详细信息和耗时

## 追踪的节点

| 节点名称 | 说明 |
|----------|------|
| run_evaluation | 根节点，整个评估流程 |
| init_evaluation | 初始化 |
| extract_department_info | 提取部门/系统信息 |
| prepare_dimensions | 准备评估维度 |
| select_next_dimension | 选择下一个维度 |
| load_rule | 加载规则文件 |
| evaluate_dimension | LLM 评估 |
| aggregate_results | 汇总结果 |
| save_results | 保存到数据库 |
| generate_report | 生成报告 |

## 性能指标

在 Laminar UI 中可以看到：
- 每个节点的执行时间
- 节点之间的依赖关系
- 总体耗时统计
- 错误和异常信息