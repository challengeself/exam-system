"""题目数据模型"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class QuestionType(Enum):
    SINGLE_CHOICE = "single_choice"  # 单选题
    MULTIPLE_CHOICE = "multiple_choice"  # 多选题
    CASE_ANALYSIS = "case_analysis"  # 案例分析（问答题）
    CASE_INTERVIEW = "case_interview"  # 面试答辩题（案例 + 问题 + 分析）


@dataclass
class Question:
    """题目基类"""
    id: str
    type: QuestionType
    content: str  # 题干/案例内容
    answer: str  # 参考答案
    analysis: str  # 解析
    keywords: List[str] = field(default_factory=list)  # 问答题关键词
    user_answer: Optional[str] = None  # 用户答案
    is_correct: Optional[bool] = None  # 是否正确
    score: float = 0.0  # 得分（问答题用）


@dataclass
class SingleChoiceQuestion(Question):
    """单选题/多选题"""
    options: List[str] = field(default_factory=list)  # 选项列表
    correct_option: str = ""  # 正确选项（A/B/C/D）
    is_multiple: bool = False  # 是否多选题


@dataclass
class CaseAnalysisQuestion(Question):
    """案例分析题（问答题）"""
    case_content: str = ""  # 案例描述
    sub_questions: List[str] = field(default_factory=list)  # 子问题列表
    case_background: str = ""  # 案例背景


@dataclass
class CaseInterviewQuestion(Question):
    """面试答辩题"""
    case_background: str = ""  # 案例背景
    questions: List[str] = field(default_factory=list)  # 问题列表
    analysis_items: List[dict] = field(default_factory=list)  # 试题分析项 [{title, content, scoring_points}]


def calculate_keyword_match(user_answer: str, keywords: List[str]) -> tuple[bool, float, List[str]]:
    """
    计算关键词匹配度
    返回：(是否及格，匹配度 0-1, 命中的关键词)
    """
    if not keywords or not user_answer.strip():
        return False, 0.0, []
    
    user_answer_lower = user_answer.lower()
    matched = [kw for kw in keywords if kw.lower() in user_answer_lower]
    
    match_rate = len(matched) / len(keywords) if keywords else 0.0
    # 匹配 60% 以上算正确
    is_correct = match_rate >= 0.6
    
    return is_correct, match_rate, matched
