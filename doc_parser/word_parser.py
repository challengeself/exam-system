"""Word 题库解析器"""
import re
from typing import List, Tuple, Dict, Any
from docx import Document
from .question_model import Question, QuestionType, SingleChoiceQuestion, CaseAnalysisQuestion


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
            option_pattern = r'([A-D])\.[^A-D]*'
            matches = re.findall(option_pattern, options_str)
            # 更精确的解析
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
        correct_option=answer
    ), i


def parse_case_analysis_new(lines: List[str], start_idx: int) -> Tuple[CaseAnalysisQuestion, int]:
    """
    解析新格式的案例分析题
    格式：
    案例一
    案例描述内容...
    单选/多选
    1. 题目内容（）
    选项：A. xxx B. xxx C. xxx D. xxx
    答案：xxx
    分析：xxx
    """
    question_id = f"case_{start_idx}"
    case_background = ""
    sub_questions = []
    sub_answers = []
    all_keywords = []
    
    i = start_idx
    current_field = "background"  # background, question_type, question, options, answer, analysis
    question_type = ""  # 单选/多选
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
        if line.startswith("案例") and i == start_idx:
            # 第一个案例标题行，下一行是描述
            case_background = ""
            current_field = "background"
            i += 1
            continue
        
        # 检测题型标记
        if line in ["单选", "多选"]:
            # 保存之前的子问题（如果有）
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
        if re.match(r'^[\d]+[.．]', line) and current_field in ["question", "background"]:
            # 保存之前的子问题（如果有）
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
            
            # 如果是背景描述阶段，切换到题目阶段
            if current_field == "background":
                current_field = "question"
            
            current_question = re.sub(r'^[\d]+[.．]\s*', '', line).strip()
            i += 1
            continue
        
        # 检测选项
        if line.startswith("选项：") or (line.startswith("选项") and "：" in line):
            options_str = line.replace("选项：", "").replace("选项:", "").strip()
            current_options = []
            # 解析选项 A. B. C. D.
            for opt in ['A', 'B', 'C', 'D']:
                opt_match = re.search(rf'{opt}\.([^A-D]+?)(?={chr(ord(opt)+1)}\.|$)', options_str)
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
            # 案例描述内容
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


def parse_case_analysis(lines: List[str], start_idx: int) -> Tuple[CaseAnalysisQuestion, int]:
    """解析案例分析题（兼容旧格式）"""
    question_id = f"case_{start_idx}"
    case_content = ""
    case_background = ""
    sub_questions = []
    answers = {}
    analysis = ""
    
    i = start_idx
    current_field = "case"
    current_question = ""
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # 检测新案例开始
        if line.startswith("案例") and ("案例：" in line or "案例:" in line):
            if case_content:
                break
            case_content = line.replace("案例：", "").replace("案例:", "").strip()
            current_field = "case"
            i += 1
            continue
        
        if line.startswith("问题"):
            current_field = "questions"
            i += 1
            continue
        
        if line.startswith("答案"):
            current_field = "answers"
            i += 1
            continue
        
        # 收集子问题（以数字或项目符号开头）
        if current_field == "questions":
            if re.match(r'^[\d一二三四五六七八九十]+[、.．]', line) or line.startswith("-"):
                q = re.sub(r'^[\d一二三四五六七八九十]+[、.．]\s*', '', line)
                sub_questions.append(q)
            elif line and not line.startswith("答案"):
                sub_questions.append(line)
        
        # 收集答案
        if current_field == "answers":
            if re.match(r'^[\d一二三四五六七八九十]+[、.．]', line):
                # 新答案项
                parts = line.split("：", 1)
                if len(parts) == 2:
                    key = parts[0]
                    value = parts[1]
                    answers[key] = value
                    analysis += f"{key}：{value}\n"
            elif line and not line.startswith("案例"):
                analysis += line + " "
        
        i += 1
    
    # 提取关键词（从答案中提取关键术语）
    keywords = extract_keywords(analysis)
    
    return CaseAnalysisQuestion(
        id=question_id,
        type=QuestionType.CASE_ANALYSIS,
        content=case_content,
        answer=analysis.strip(),
        analysis=analysis.strip(),
        keywords=keywords,
        case_background=case_content,
        sub_questions=sub_questions
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
        "器质性病变", "现实因素", "病程", "情绪低落", "兴趣缺失"
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
        
        # 检测单选题
        if line.startswith("题目：") or (line.startswith("题目") and "：" in line):
            try:
                q, next_i = parse_single_choice(lines, i)
                questions.append(q)
                i = next_i
                continue
            except Exception as e:
                print(f"解析单选题失败 {i}: {e}")
                i += 1
                continue
        
        # 检测案例分析题（新格式：案例 + 单选/多选）
        if line.startswith("案例") and not ("案例：" in line or "案例:" in line):
            try:
                q, next_i = parse_case_analysis_new(lines, i)
                questions.append(q)
                i = next_i
                continue
            except Exception as e:
                print(f"解析新格式案例题失败 {i}: {e}")
                i += 1
                continue
        
        # 检测案例分析题（旧格式）
        if line.startswith("案例") and ("案例：" in line or "案例:" in line):
            try:
                q, next_i = parse_case_analysis(lines, i)
                questions.append(q)
                i = next_i
                continue
            except Exception as e:
                print(f"解析旧格式案例题失败 {i}: {e}")
                i += 1
                continue
        
        i += 1
    
    return questions
