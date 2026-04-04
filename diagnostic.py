"""完整诊断：从加载到显示"""
import sys
import json
import re
sys.path.insert(0, '.')

print("=" * 70)
print("诊断报告：多选题选项显示问题")
print("=" * 70)

# 1. 检查 libraries.json
print("\n【1】检查 libraries.json")
try:
    with open('storage/libraries.json', 'r', encoding='utf-8') as f:
        libraries = json.load(f)
    print(f"✅ 找到 libraries.json，{len(libraries)}个题库")
    
    for lib in libraries:
        print(f"\n  题库：{lib['name']}")
        questions = lib.get('questions', [])
        print(f"  题目数：{len(questions)}")
        
        # 检查多选题
        mc_questions = [q for q in questions if q.get('is_multiple')]
        print(f"  多选题：{len(mc_questions)}道")
        
        for i, q in enumerate(mc_questions, 1):
            opts = q.get('options', [])
            print(f"    多选题{i}: options={len(opts)}个")
            if opts:
                print(f"      选项：{opts}")
            else:
                print(f"      ⚠️ 选项为空！")
                print(f"      完整数据：{json.dumps(q, ensure_ascii=False)[:200]}")
except FileNotFoundError:
    print("❌ libraries.json 不存在")
except json.JSONDecodeError as e:
    print(f"❌ JSON 解析失败：{e}")

# 2. 测试分组函数
print("\n【2】测试分组函数")
def group_questions_by_case(questions):
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
        else:
            if current_group:
                groups.append(current_group)
                current_group = []
            groups.append([q])
    
    if current_group:
        groups.append(current_group)
    
    return groups

if 'questions' in locals():
    groups = group_questions_by_case(questions)
    print(f"✅ 分组成功：{len(groups)}个案例")
    
    for ci, group in enumerate(groups, 1):
        print(f"\n  案例{ci}: {len(group)}道题")
        for si, q in enumerate(group, 1):
            is_mc = q.get('is_multiple', False)
            opts = q.get('options', [])
            status = "✅" if (not is_mc or opts) else "❌"
            print(f"    {status} 小题{si}: type={q['type']}, is_multiple={is_mc}, options={len(opts)}个")

# 3. 模拟答题界面逻辑
print("\n【3】模拟答题界面逻辑")
if 'questions' in locals():
    for gi, group in enumerate(groups):
        for si, question in enumerate(group):
            if question.get('is_multiple'):
                print(f"\n  案例{gi+1} 小题{si+1} (多选题):")
                options = question.get("options", [])
                is_multiple = question.get("is_multiple", False)
                
                print(f"    question['type'] = {question['type']}")
                print(f"    is_multiple = {is_multiple}")
                print(f"    options = {options}")
                
                # 检查条件判断
                if question["type"] in ["single_choice", "multiple_choice"]:
                    print(f"    ✅ 通过类型检查")
                    
                    if is_multiple:
                        print(f"    ✅ 进入多选题逻辑")
                        
                        if options:
                            print(f"    ✅ 有{len(options)}个选项")
                            print(f"    ✅ 应该显示选项！")
                        else:
                            print(f"    ❌ options 为空！")
                    else:
                        print(f"    ❌ is_multiple=False")
                else:
                    print(f"    ❌ 类型检查失败")

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)
