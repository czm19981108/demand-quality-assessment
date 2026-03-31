#!/usr/bin/env python
"""查看 evaluations.db 数据"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/evaluations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== 数据库表列表 ===\n")
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
for row in cursor:
    print(f"  - {row['name']}")

# 查看表结构
print("\n=== 表结构: evaluations ===\n")
cursor.execute('PRAGMA table_info(evaluations)')
for col in cursor.fetchall():
    print(f"  {col['name']}: {col['type']}")

print("\n=== 评估记录总数 ===\n")
cursor.execute('SELECT COUNT(*) FROM evaluations')
total = cursor.fetchone()[0]
print(f"  总计: {total} 条评估记录")

if total > 0:
    print("\n=== 最近 5 条评估记录 ===\n")
    cursor.execute('''
        SELECT * FROM evaluations ORDER BY created_at DESC LIMIT 5
    ''')
    for i, row in enumerate(cursor.fetchall(), 1):
        data = dict(row)
        print(f"[{i}] ")
        for k, v in data.items():
            print(f"    {k}: {v}")
        print()

print("\n=== 表结构: dimension_scores ===\n")
cursor.execute('PRAGMA table_info(dimension_scores)')
for col in cursor.fetchall():
    print(f"  {col['name']}: {col['type']}")

cursor.execute('SELECT COUNT(*) FROM dimension_scores')
ds_total = cursor.fetchone()[0]
print(f"\n维度评分记录总数: {ds_total} 条")

if ds_total > 0:
    print("\n最近 5 条维度评分:\n")
    cursor.execute('''
        SELECT * FROM dimension_scores ORDER BY created_at DESC LIMIT 5
    ''')
    for row in cursor.fetchall():
        data = dict(row)
        print(f"  evaluation_id={data['evaluation_id']}, dimension={data['dimension']}, score={data['score']}")

conn.close()
