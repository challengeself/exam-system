"""Word 题库解析器 - 支持笔试和面试答辩格式"""
import re
from typing import List, Tuple, Dict, Any
from docx import Document
from .question_model import (
    Question, QuestionType, SingleChoiceQuestion, 
    CaseAnalysisQuestion, CaseInterviewQuestion
)


def parse_single_choice(lines: List[str], start_idx: int) -> Tuple[SingleChoiceQuestion, int]:
    """解析单选题"""
    question_id = f"single_{start_idx}"
    content = ""
    options = []
    answer = ""
    analysis = ""
    
    i = start_idx
    current_field = "content"
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        # 检测新题目开始
        if line.startswith("题目：") or (line.startswith("题目") and "：" in line):
            if content:  # 已经有内容了，说明是下一题
                break
            content = line.replace("题目：", "").replace("题目:", "").strip()
            current_field = "content"
            i += 1
            continue
        
        if line.startswith("选项：") or (line.startswith("选项") and "：" in line):
            options_str = line.replace("选项：", "").replace("选项:", "").strip()
            # 解析选项 A.B.C.D.
            for opt in ['A', 'B', 'C', 'D']:
                opt_match = re.search(rf'{opt}\.([^A-D]+?)(?={chr(ord(opt)+1)}\.|$)', options_str)
                if opt_match:
                    options.append(f"{opt}. {opt_match.group(1).strip()}")
            current_field = "options"
            i += 1
            continue
        
        if line.startswith("答案：") or (line.startswith("答案") and "：" in line):
            answer = line.replace("答案：", "").replace("答案:", "").strip()
            current_field = "answer"
            i += 1
            continue
        
        if line.startswith("分析：") or (line.startswith("分析") and "：" in line):
            analysis = line.replace("分析：", "").replace("分析:", "").strip()
            current_field = "analysis"
            i += 1
            continue
        
        # 继续累积当前字段
        if current_field == "analysis" and analysis:
            analysis += " " + line
        elif current_field == "content" and content:
            content += " " + line
            
        i += 1
    
    return SingleChoiceQuestion(
        id=question_id,
        type=QuestionType.SINGLE_CHOICE,
        content=content,
        answer=answer,
        analysis=analysis,
        options=options,
        correct_option=answer,
        is_multiple=False
    ), i


def parse_multiple_choice(lines: List[str], start_idx: int) -> Tuple[SingleChoiceQuestion, int]:
    """解析多选题"""
    question_id = f"multiple_{start_idx}"
    content = ""
    options = []
    answer = ""
    analysis = ""
    
    i = start_idx
    current_field = "content"
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        # 检测新题目开始
        if line.startswith("题目：") or (line.startswith("题目") and "：" in line):
            if content:  # 已经有内容了，说明是下一题
                break
            content = line.replace("题目：", "").replace("题目:", "").strip()
            current_field = "content"
            i += 1
            continue
        
        if line.startswith("选项：") or (line.startswith("选项") and "：" in line):
            options_str = line.replace("选项：", "").replace("选项:", "").strip()
            for opt in ['A', 'B', 'C', 'D', 'E']:
                opt_match = re.search(rf'{opt}\.([^A-E]+?)(?={chr(ord(opt)+1)}\.|$)', options_str)
                if opt_match:
                    options.append(f"{opt}. {opt_match.group(1).strip()}")
            current_field = "options"
            i += 1
            continue
        
        if line.startswith("答案：") or (line.startswith("答案") and "：" in line):
            answer = line.replace("答案：", "").replace("答案:", "").strip()
            current_field = "answer"
            i += 1
            continue
        
        if line.startswith("分析：") or (line.startswith("分析") and "：" in line):
            analysis = line.replace("分析：", "").replace("分析:", "").strip()
            current_field = "analysis"
            i += 1
            continue
        
        # 继续累积当前字段
        if current_field == "analysis" and analysis:
            analysis += " " + line
        elif current_field == "content" and content:
            content += " " + line
            
        i += 1
    
    return SingleChoiceQuestion(
        id=question_id,
        type=QuestionType.MULTIPLE_CHOICE,
        content=content,
        answer=answer,
        analysis=analysis,
        options=options,
        correct_option=answer,
        is_multiple=True
    ), i


def parse_case_analysis_written(lines: List[str], start_idx: int) -> Tuple[CaseAnalysisQuestion, int]:
    """
    解析笔试格式案例分析题（案例 + 单选/多选）
    格式：
    案例一
    案例描述
    内容...
    单选
    1. 题目内容（）
    选项：A. xxx B. xxx C. xxx D. xxx
    答案：xxx
    分析：xxx
    多选
    1. 题目内容（）
    ...
    """
    question_id = f"case_written_{start_idx}"
    case_background = ""
    sub_questions = []
    
    i = start_idx
    current_field = "background"
    question_type = ""
    current_question = ""
    current_options = []
    current_answer = ""
    current_analysis = ""
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # 检测新案例开始
        if line.startswith('案例') and line != '案例描述' and any(c in line for c in '0123456789 一二三四五六七八九十'):
            if case_background:
                break
            i += 1
            continue
        
        if line == "案例描述":
            current_field = "background"
            i += 1
            continue
        
        # 检测题型标记
        if line in ["单选", "多选"]:
            if current_question and current_answer:
                sub_questions.append({
                    "content": current_question,
                    "type": question_type,
                    "options": current_options,
                    "answer": current_answer,
                    "analysis": current_analysis
                })
            
            question_type = line
            current_field = "question"
            current_question = ""
            current_options = []
            current_answer = ""
            current_analysis = ""
            i += 1
            continue
        
        # 检测题目（数字开头）
        if re.match(r'^[\d]+[.．]', line):
            if current_question and current_answer:
                sub_questions.append({
                    "content": current_question,
                    "type": question_type,
                    "options": current_options,
                    "answer": current_answer,
                    "analysis": current_analysis
                })
                current_question = ""
                current_options = []
                current_answer = ""
                current_analysis = ""
            
            current_question = re.sub(r'^[\d]+[.．]\s*', '', line).strip()
            current_field = "question"
            i += 1
            continue
        
        # 检测选项
        if line.startswith("选项：") or (line.startswith("选项") and "：" in line):
            options_str = line.replace("选项：", "").replace("选项:", "").strip()
            current_options = []
            for opt in ['A', 'B', 'C', 'D', 'E']:
                opt_match = re.search(rf'{opt}\.([^A-E]+?)(?={chr(ord(opt)+1)}\.|$)', options_str)
                if opt_match:
                    current_options.append(f"{opt}. {opt_match.group(1).strip()}")
            current_field = "options"
            i += 1
            continue
        
        # 检测答案
        if line.startswith("答案：") or (line.startswith("答案") and "：" in line):
            current_answer = line.replace("答案：", "").replace("答案:", "").strip()
            current_field = "answer"
            i += 1
            continue
        
        # 检测分析
        if line.startswith("分析：") or (line.startswith("分析") and "：" in line):
            current_analysis = line.replace("分析：", "").replace("分析:", "").strip()
            current_field = "analysis"
            i += 1
            continue
        
        # 处理各字段内容
        if current_field == "background":
            if case_background:
                case_background += " " + line
            else:
                case_background = line
        elif current_field == "analysis" and current_analysis:
            current_analysis += " " + line
        
        i += 1
    
    # 保存最后一个子问题
    if current_question and current_answer:
        sub_questions.append({
            "content": current_question,
            "type": question_type,
            "options": current_options,
            "answer": current_answer,
            "analysis": current_analysis
        })
    
    # 提取关键词
    all_text = " ".join([sq.get("analysis", "") for sq in sub_questions])
    all_keywords = extract_keywords(all_text)
    
    # 构建案例题内容
    content = f"【案例】{case_background}"
    
    # 构建答案和解析
    full_answer = ""
    full_analysis = ""
    for sq in sub_questions:
        full_answer += f"[{sq['type']}] {sq['content']} 答案：{sq['answer']}\n"
        full_analysis += f"[{sq['type']}] {sq['content']}\n答案：{sq['answer']}\n分析：{sq['analysis']}\n\n"
    
    return CaseAnalysisQuestion(
        id=question_id,
        type=QuestionType.CASE_ANALYSIS,
        content=content,
        answer=full_answer.strip(),
        analysis=full_analysis.strip(),
        keywords=all_keywords,
        case_background=case_background,
        sub_questions=[sq["content"] for sq in sub_questions]
    ), i


def parse_case_interview(lines: List[str], start_idx: int) -> Tuple[CaseInterviewQuestion, int]:
    """
    解析面试答辩格式
    格式：
    案例一
    案例描述
    内容...
    问题
    请依据以上案例，回答以下问题：
    1、……
    2、……
    试题分析
    1、……
    评分要点：……
    2、……
    评分要点：……
    """
    question_id = f"case_interview_{start_idx}"
    case_background = ""
    questions = []
    analysis_items = []
    
    i = start_idx
    current_section = "background"  # background, questions, analysis
    current_analysis_title = ""
    current_analysis_content = ""
    current_scoring_points = ""
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # 检测新案例开始
        if line.startswith('案例') and line != '案例描述' and any(c in line for c in '0123456789 一二三四五六七八九十'):
            if case_background:
                break
            i += 1
            continue
        
        if line == "案例描述":
            current_section = "background"
            i += 1
            continue
        
        # 检测"问题"部分
        if line == "问题" or line.startswith("问题"):
            # 保存之前的分析项
            if current_analysis_title and current_analysis_content:
                analysis_items.append({
                    "title": current_analysis_title,
                    "content": current_analysis_content.strip(),
                    "scoring_points": current_scoring_points.strip()
                })
                current_analysis_title = ""
                current_analysis_content = ""
                current_scoring_points = ""
            
            current_section = "questions"
            i += 1
            continue
        
        # 检测"试题分析"部分
        if line == "试题分析" or line.startswith("试题分析"):
            # 保存之前的分析项
            if current_analysis_title and current_analysis_content:
                analysis_items.append({
                    "title": current_analysis_title,
                    "content": current_analysis_content.strip(),
                    "scoring_points": current_scoring_points.strip()
                })
                current_analysis_title = ""
                current_analysis_content = ""
                current_scoring_points = ""
            
            current_section = "analysis"
            i += 1
            continue
        
        # 处理各部分内容
        if current_section == "background":
            if case_background:
                case_background += " " + line
            else:
                case_background = line
        
        elif current_section == "questions":
            # 跳过"请依据以上案例，回答以下问题："这类提示语
            if "请依据" in line or "回答以下问题" in line:
                i += 1
                continue
            # 检测问题（数字开头）
            if re.match(r'^[\d]+[,.．]', line):
                q = re.sub(r'^[\d]+[,.．]\s*', '', line).strip()
                questions.append(q)
        
        elif current_section == "analysis":
            # 检测分析项标题（数字开头）
            if re.match(r'^[\d]+[,.．]', line):
                # 保存之前的分析项
                if current_analysis_title and current_analysis_content:
                    analysis_items.append({
                        "title": current_analysis_title,
                        "content": current_analysis_content.strip(),
                        "scoring_points": current_scoring_points.strip()
                    })
                
                parts = line.split("：", 1)
                if len(parts) >= 2:
                    current_analysis_title = re.sub(r'^[\d]+[,.．]\s*', '', parts[0]).strip()
                    current_analysis_content = parts[1].strip() if len(parts) > 1 else ""
                else:
                    current_analysis_title = re.sub(r'^[\d]+[,.．]\s*', '', line).strip()
                    current_analysis_content = ""
                current_scoring_points = ""
            elif "评分要点" in line or "参考答案" in line:
                # 这是评分要点或参考答案
                if "：" in line:
                    parts = line.split("：", 1)
                    if "评分要点" in parts[0]:
                        current_scoring_points = parts[1].strip()
                    elif "参考答案" in parts[0]:
                        current_analysis_content += " " + parts[1].strip()
                else:
                    current_analysis_content += " " + line
            elif current_analysis_title:
                # 继续累积分析内容
                current_analysis_content += " " + line
        
        i += 1
    
    # 保存最后一个分析项
    if current_analysis_title and current_analysis_content:
        analysis_items.append({
            "title": current_analysis_title,
            "content": current_analysis_content.strip(),
            "scoring_points": current_scoring_points.strip()
        })
    
    # 提取关键词
    all_text = case_background + " " + " ".join([item.get("content", "") for item in analysis_items])
    all_keywords = extract_keywords(all_text)
    
    # 构建内容
    content = f"【案例】{case_background}"
    
    # 构建答案（问题列表）
    full_answer = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    
    # 构建解析（分析项）
    full_analysis = ""
    for item in analysis_items:
        full_analysis += f"{item['title']}:\n"
        if item.get('content'):
            full_analysis += f"参考答案：{item['content']}\n"
        if item.get('scoring_points'):
            full_analysis += f"评分要点：{item['scoring_points']}\n"
        full_analysis += "\n"
    
    return CaseInterviewQuestion(
        id=question_id,
        type=QuestionType.CASE_INTERVIEW,
        content=content,
        answer=full_answer.strip(),
        analysis=full_analysis.strip(),
        keywords=all_keywords,
        case_background=case_background,
        questions=questions,
        analysis_items=analysis_items
    ), i


def extract_keywords(text: str) -> List[str]:
    """从答案文本中提取关键词"""
    # 心理学常见关键词
    psychology_terms = [
        "焦虑", "抑郁", "恐惧", "强迫", "一般心理问题", "严重心理问题",
        "神经症", "精神病", "自知力", "幻听", "妄想", "ABC 理论",
        "合理情绪疗法", "认知行为", "精神分析", "人本主义", "行为主义",
        "条件反射", "无条件反射", "社会化", "自我实现", "马斯洛",
        "埃里克森", "人格发展", "勤奋对自卑", "信任对怀疑",
        "被动求医", "主动求医", "转诊", "面质", "倾听", "共情",
        "无条件积极关注", "真诚", "设身处地", "咨询关系", "保密",
        "危机干预", "自杀", "自伤", "依赖", "依赖型", "恐惧型",
        "依恋类型", "强迫性", "恐怖症", "泛化", "社会功能",
        "器质性病变", "现实因素", "病程", "情绪低落", "兴趣缺失",
        "PTSD", "创伤后应激障碍", "惊恐障碍", "强迫症", "抑郁症",
        "暴露疗法", "ERP", "认知重构", "放松训练", "正念",
        "家庭系统", "代际传递", "原生家庭", "夫妻咨询", "沟通技巧",
        "闪回", "噩梦", "回避", "情绪麻木", "警觉性增高"
    ]
    
    keywords = []
    text_lower = text.lower()
    for term in psychology_terms:
        if term.lower() in text_lower:
            keywords.append(term)
    
    return keywords


def parse_word_document(file_path: str) -> List[Question]:
    """解析 Word 文档，返回题目列表"""
    doc = Document(file_path)
    
    # 提取所有段落文本
    lines = []
    for para in doc.paragraphs:
        if para.text.strip():
            lines.append(para.text.strip())
    
    questions = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 检测单选题（独立题目格式）
        if line.startswith("题目：") and "单选" not in line:
            # 检查后面是否有"选项："来判断是否是单选题
            # 先尝试解析
            try:
                q, next_i = parse_single_choice(lines, i)
                if q.options:  # 有选项才是单选题
                    questions.append(q)
                    i = next_i
                    continue
            except Exception as e:
                print(f"解析单选题失败 {i}: {e}")
            i += 1
            continue
        
        # 检测多选题（独立题目格式）
        if line.startswith("题目：") and "多选" in line:
            try:
                q, next_i = parse_multiple_choice(lines, i)
                questions.append(q)
                i = next_i
                continue
            except Exception as e:
                print(f"解析多选题失败 {i}: {e}")
            i += 1
            continue
        
        # 检测面试答辩格式（案例 + 问题 + 试题分析）
        if line.startswith("案例") and not ("案例：" in line or "案例:" in line):
            # 检查是否包含"试题分析"来判断是面试格式
            remaining_text = " ".join(lines[i:min(i+50, len(lines))])
            if "试题分析" in remaining_text:
                try:
                    q, next_i = parse_case_interview(lines, i)
                    questions.append(q)
                    i = next_i
                    continue
                except Exception as e:
                    print(f"解析面试答辩题失败 {i}: {e}")
            else:
                # 否则是笔试格式（案例 + 单选/多选）
                try:
                    q, next_i = parse_case_analysis_written(lines, i)
                    questions.append(q)
                    i = next_i
                    continue
                except Exception as e:
                    print(f"解析笔试案例题失败 {i}: {e}")
            i += 1
            continue
        
        i += 1
    
    return questions
