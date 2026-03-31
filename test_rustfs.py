#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 RustFS 连接"""

import sys
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from src.rustfs_client import get_rustfs_client
from src.config import config

def test_rustfs_connection():
    """测试 RustFS 连接和基本操作"""
    print("=== RustFS 连接测试 ===\n")

    if not config.rustfs_enabled:
        print("[X] RustFS 未启用，请在配置中开启 rustfs.enabled")
        print("\n配置示例 (.req-check.json):")
        print('  "rustfs": {')
        print('    "enabled": true,')
        print(f'    "endpoint": "{config.rustfs_endpoint}",')
        print('    "access_key": "your_access_key",')
        print('    "secret_key": "your_secret_key",')
        print('    "bucket": "demand-reports"')
        print('  }')
        return False

    print(f"端点: {config.rustfs_endpoint}")
    print(f"Bucket: {config.rustfs_bucket}")
    print(f"AccessKey: {config.rustfs_access_key[:5]}...\n")

    client = get_rustfs_client()

    if not client.enabled:
        print("[X] RustFS 客户端初始化失败")
        return False

    print("[OK] 客户端初始化成功\n")

    # 测试确保 Bucket 存在
    print("[1] 测试 Bucket 检查...")
    if not client.ensure_bucket_exists():
        print("[X] Bucket 不存在且创建失败")
        return False
    print("[OK] Bucket 检查/创建成功\n")

    # 测试上传
    print("[2] 测试上传报告...")
    test_content = """# 测试报告

这是一个测试报告，用于验证 RustFS 连接是否正常。

- 生成时间: 测试
- 功能: OK
"""
    success, object_key = client.upload_report("test_connection", test_content)
    if not success:
        print("[X] 上传失败")
        return False
    print(f"[OK] 上传成功: {object_key}\n")

    # 测试下载
    print("[3] 测试下载报告...")
    success, downloaded = client.download_report(object_key)
    if not success or downloaded is None:
        print("[X] 下载失败")
        return False
    print("[OK] 下载成功\n")

    # 测试列表
    print("[4] 测试列出报告...")
    objects = client.list_reports()
    print(f"[OK] 获取到 {len(objects)} 个对象\n")

    # 获取访问 URL
    print("[5] 获取访问 URL...")
    url = client.get_report_url(object_key)
    print(f"[OK] 报告 URL: {url}\n")

    # 清理测试文件
    print("[6] 清理测试文件...")
    if client.delete_report(object_key):
        print("[OK] 测试文件已删除\n")
    else:
        print("[!]  删除失败，但不影响测试结果\n")

    print("=== 所有测试通过! ===")
    print(f"- RustFS 运行正常")
    print(f"- 可以存储评估报告")
    return True


if __name__ == "__main__":
    success = test_rustfs_connection()
    sys.exit(0 if success else 1)
