"""Word 题库解析器 - 支持笔试和面试答辩格式"""
import re
from typing import List, Tuple, Dict, Any
from docx import Document
from .question_model import (
    Question, QuestionType, SingleChoiceQuestion, 
    CaseAnalysisQuestion, CaseInterviewQuestion
)


def extract_keywords(text: str) -> List[str]:
    """从答案文本中提取关键词"""
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
        "闪回", "噩梦", "回避", "情绪麻木", "警觉性增高",
        "修通", "诊断", "领悟", "再教育", "咨询目标", "中立", "接纳"
    ]
    
    keywords = []
    text_lower = text.lower()
    for term in psychology_terms:
        if term.lower() in text_lower:
            keywords.append(term)
    
    return keywords


def parse_case_written_exam(lines: List[str], start_idx: int) -> Tuple[List, int]:
    """
    解析笔试技能题格式（案例 + 多道独立单选/多选）
    格式：
    题目：案例描述（一）、...案例内容...
    单选 1、题目内容（）
    选项：A. xxx B. xxx C. xxx D. xxx
    答案：xxx
    分析：xxx
    单选 2、题目内容（）
    选项：A. xxx B. xxx C. xxx D. xxx
    答案：xxx
    分析：xxx
    多选 4、题目内容（）
    选项：A. xxx B. xxx C. xxx D. xxx E. xxx
    答案：xxx
    分析：xxx
    
    返回：独立的单选/多选题列表，每道题都包含案例背景
    """
    questions = []
    case_background = ""
    
    i = start_idx
    current_question_type = None  # "单选" or "多选"
    current_question_num = ""
    current_question_content = ""
    current_options = []
    current_answer = ""
    current_analysis = ""
    current_field = "case"  # case, question, options, answer, analysis
    question_counter = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # 检测案例描述开始
        if line.startswith("题目：案例描述"):
            current_field = "case"
            # 提取案例内容（去掉"题目：案例描述（X）、"）
            case_content = re.sub(r'^题目：案例描述 [（(][^）)]*[)）][、,]?', '', line)
            if case_content:
                case_background = case_content
            i += 1
            continue
        
        # 累积案例内容（直到遇到单选/多选）
        if current_field == "case" and case_background:
            # 检查是否是单选/多选题目行
            if re.match(r'^[单多]选\s*\d+', line):
                # 保存之前的题目（如果有）
                if current_question_content and current_answer:
                    question_counter += 1
                    q_type = QuestionType.MULTIPLE_CHOICE if current_question_type == "多选" else QuestionType.SINGLE_CHOICE
                    q_id = f"case_{current_question_type}_{start_idx}_{question_counter}"
                    
                    all_keywords = extract_keywords(current_analysis)
                    
                    questions.append(SingleChoiceQuestion(
                        id=q_id,
                        type=q_type,
                        content=f"【案例】{case_background}\n\n{current_question_content}",
                        answer=current_answer,
                        analysis=current_analysis,
                        options=current_options,
                        correct_option=current_answer,
                        is_multiple=(current_question_type == "多选"),
                        keywords=all_keywords
                    ))
                
                # 解析新题目行：单选 1、xxx 或 多选 4、xxx
                match = re.match(r'^([单多]选)\s*(\d+)[,，、]?\s*(.*)$', line)
                if match:
                    current_question_type = match.group(1)
                    current_question_num = match.group(2)
                    current_question_content = match.group(3).strip()
                    current_options = []
                    current_answer = ""
                    current_analysis = ""
                    current_field = "question"
                i += 1
                continue
            else:
                # 继续累积案例内容
                case_background += " " + line
                i += 1
                continue
        
        # 检测单选/多选题目行
        if re.match(r'^[单多]选\s*\d+', line):
            # 保存之前的题目（如果有）
            if current_question_content and current_answer:
                question_counter += 1
                q_type = QuestionType.MULTIPLE_CHOICE if current_question_type == "多选" else QuestionType.SINGLE_CHOICE
                q_id = f"case_{current_question_type}_{start_idx}_{question_counter}"
                
                all_keywords = extract_keywords(current_analysis)
                
                questions.append(SingleChoiceQuestion(
                    id=q_id,
                    type=q_type,
                    content=f"【案例】{case_background}\n\n{current_question_content}",
                    answer=current_answer,
                    analysis=current_analysis,
                    options=current_options,
                    correct_option=current_answer,
                    is_multiple=(current_question_type == "多选"),
                    keywords=all_keywords
                ))
            
            # 解析新题目行
            match = re.match(r'^([单多]选)\s*(\d+)[,，、]?\s*(.*)$', line)
            if match:
                current_question_type = match.group(1)
                current_question_num = match.group(2)
                current_question_content = match.group(3).strip()
                current_options = []
                current_answer = ""
                current_analysis = ""
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
        
        # 累积分析内容
        if current_field == "analysis" and current_analysis:
            current_analysis += " " + line
        
        i += 1
    
    # 保存最后一个题目
    if current_question_content and current_answer:
        question_counter += 1
        q_type = QuestionType.MULTIPLE_CHOICE if current_question_type == "多选" else QuestionType.SINGLE_CHOICE
        q_id = f"case_{current_question_type}_{start_idx}_{question_counter}"
        
        all_keywords = extract_keywords(current_analysis)
        
        questions.append(SingleChoiceQuestion(
            id=q_id,
            type=q_type,
            content=f"【案例】{case_background}\n\n{current_question_content}",
            answer=current_answer,
            analysis=current_analysis,
            options=current_options,
            correct_option=current_answer,
            is_multiple=(current_question_type == "多选"),
            keywords=all_keywords
        ))
    
    return questions, i


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
    questions_list = []
    analysis_items = []
    
    i = start_idx
    current_section = "background"
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
            if "请依据" in line or "回答以下问题" in line:
                i += 1
                continue
            if re.match(r'^[\d]+[,.．]', line):
                q = re.sub(r'^[\d]+[,.．]\s*', '', line).strip()
                questions_list.append(q)
        
        elif current_section == "analysis":
            if re.match(r'^[\d]+[,.．]', line):
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
                if "：" in line:
                    parts = line.split("：", 1)
                    if "评分要点" in parts[0]:
                        current_scoring_points = parts[1].strip()
                    elif "参考答案" in parts[0]:
                        current_analysis_content += " " + parts[1].strip()
                else:
                    current_analysis_content += " " + line
            elif current_analysis_title:
                current_analysis_content += " " + line
        
        i += 1
    
    if current_analysis_title and current_analysis_content:
        analysis_items.append({
            "title": current_analysis_title,
            "content": current_analysis_content.strip(),
            "scoring_points": current_scoring_points.strip()
        })
    
    all_text = case_background + " " + " ".join([item.get("content", "") for item in analysis_items])
    all_keywords = extract_keywords(all_text)
    
    content = f"【案例】{case_background}"
    full_answer = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions_list)])
    
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
        questions=questions_list,
        analysis_items=analysis_items
    ), i


def parse_simple_questions(lines: List[str], start_idx: int) -> Tuple[List, int]:
    """
    解析简单题目格式（无案例，直接题目）
    格式：
    题目：1、xxx 或 题目：单选 1、xxx
    选项：A. xxx B. xxx C. xxx D. xxx
    答案：xxx
    分析：xxx
    """
    questions = []
    current_q = None
    
    i = start_idx
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # 检测题目行
        match = re.match(r'^题目：(?:([单多] 选)\s*)?(\d+)[,，、]\s*(.+)$', line)
        if match:
            if current_q:
                questions.append(current_q)
            
            q_type_str = match.group(1)
            q_type = QuestionType.MULTIPLE_CHOICE if q_type_str == "多选" else QuestionType.SINGLE_CHOICE
            is_multiple = q_type_str == "多选"
            
            current_q = SingleChoiceQuestion(
                id=f"q_{match.group(2)}",
                type=q_type,
                is_multiple=is_multiple,
                content=match.group(3),
                options=[],
                answer="",
                analysis="",
                correct_option="",
                keywords=[]
            )
            i += 1
            continue
        
        if current_q:
            if line.startswith("选项："):
                opts_text = line.replace("选项：", "").strip()
                opts = re.split(r'\s+(?=[A-D]\.)', opts_text)
                current_q.options = [o.strip() for o in opts if o.strip()]
            elif line.startswith("答案："):
                ans = line.replace("答案：", "").strip()
                current_q.answer = ans
                current_q.correct_option = ans
            elif line.startswith("分析："):
                current_q.analysis = line.replace("分析：", "").strip()
                current_q.keywords = extract_keywords(current_q.analysis)
        
        i += 1
    
    if current_q:
        questions.append(current_q)
    
    return questions, i


def parse_word_document(file_path: str) -> List[Question]:
    """解析 Word 文档，返回题目列表"""
    doc = Document(file_path)
    
    lines = []
    for para in doc.paragraphs:
        if para.text.strip():
            lines.append(para.text.strip())
    
    questions = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 检测笔试技能题格式（题目：案例描述）
        if line.startswith("题目：案例描述"):
            try:
                q_list, next_i = parse_case_written_exam(lines, i)
                questions.extend(q_list)
                i = next_i
                continue
            except Exception as e:
                print(f"解析笔试技能题失败 {i}: {e}")
            i += 1
            continue
        
        # 检测面试答辩格式（案例 + 问题 + 试题分析）
        if line.startswith("案例") and not ("案例：" in line or "案例:" in line):
            remaining_text = " ".join(lines[i:min(i+50, len(lines))])
            if "试题分析" in remaining_text:
                try:
                    q, next_i = parse_case_interview(lines, i)
                    questions.append(q)
                    i = next_i
                    continue
                except Exception as e:
                    print(f"解析面试答辩题失败 {i}: {e}")
            i += 1
            continue
        
        # 检测简单题目格式（题目：1、xxx）
        if line.startswith("题目：") and re.match(r'^题目：(?:[单多] 选\s*)?\d+', line):
            try:
                q_list, next_i = parse_simple_questions(lines, i)
                questions.extend(q_list)
                i = next_i
                continue
            except Exception as e:
                print(f"解析简单题目失败 {i}: {e}")
            i += 1
            continue
            i += 1
            continue
        
        i += 1
    
    return questions
