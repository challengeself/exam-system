#!/usr/bin/env python3
"""测试多选题选项显示"""
import json

# 加载题库
data = json.load(open('storage/debug_save.json'))
questions = data if isinstance(data, list) else data.get('questions', [])

# 按案例分组
import re
groups = []
current_group = []
current_case_prefix = None

for q in questions:
    q_id = q.get("id", "")
    match = re.search(r'case_.*?_(\d+)_(\d+)', q_id)
    if match:
        case_idx = match.group(1)
        if current_case_prefix is None:
            current_case_prefix = case_idx
            current_group = [q]
        elif case_idx == current_case_prefix:
            current_group.append(q)
        else:
            if current_group:
                groups.append(current_group)
            current_group = [q]
            current_case_prefix = case_idx

if current_group:
    groups.append(current_group)

print(f"分组数：{len(groups)}")
for i, group in enumerate(groups, 1):
    print(f"\n案例{i}: {len(group)}道题")
    for j, q in enumerate(group, 1):
        q_type = q.get('type')
        is_mc = q.get('is_multiple', False)
        opts = q.get('options', [])
        print(f"  {j}. type={q_type}, is_multiple={is_mc}, options={len(opts)}")
        if is_mc:
            print(f"     选项：{opts}")

# 模拟第 4、5 题的显示
print("\n\n=== 模拟第 4 题显示 ===")
q4 = groups[0][3]  # 第 1 组第 4 题
print(f"type: {q4['type']}")
print(f"is_multiple: {q4.get('is_multiple', False)}")
print(f"options: {q4.get('options', [])}")
options = q4.get('options', [])
is_multiple = q4.get('is_multiple', False)

if is_multiple:
    print("\nCheckbox 循环:")
    for opt in options:
        opt_letter = opt.split(".")[0].strip()
        opt_text = opt.split(".", 1)[1].strip() if "." in opt else opt
        print(f"  ☐ {opt_letter}. {opt_text}")
