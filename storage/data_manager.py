"""数据存储管理"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


class DataManager:
    """数据管理器"""
    
    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.questions_file = self.storage_dir / "questions.json"
        self.wrong_notes_file = self.storage_dir / "wrong_notes.json"
        self.history_file = self.storage_dir / "history.json"
    
    def save_questions(self, questions: List[Dict[str, Any]]) -> None:
        """保存题库"""
        data = {
            "updated_at": datetime.now().isoformat(),
            "count": len(questions),
            "questions": questions
        }
        with open(self.questions_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_questions(self) -> List[Dict[str, Any]]:
        """加载题库"""
        if not self.questions_file.exists():
            return []
        
        with open(self.questions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return data.get("questions", [])
    
    def save_wrong_answer(self, question: Dict[str, Any]) -> None:
        """保存错题"""
        wrong_notes = self.load_wrong_notes()
        
        # 检查是否已存在
        for note in wrong_notes:
            if note.get("id") == question.get("id"):
                # 更新错题记录
                note["wrong_count"] = note.get("wrong_count", 0) + 1
                note["last_wrong_at"] = datetime.now().isoformat()
                note["user_answer"] = question.get("user_answer", "")
                break
        else:
            # 新增错题
            wrong_notes.append({
                "id": question.get("id"),
                "type": question.get("type"),
                "content": question.get("content"),
                "answer": question.get("answer"),
                "analysis": question.get("analysis"),
                "user_answer": question.get("user_answer", ""),
                "wrong_count": 1,
                "created_at": datetime.now().isoformat(),
                "last_wrong_at": datetime.now().isoformat()
            })
        
        with open(self.wrong_notes_file, "w", encoding="utf-8") as f:
            json.dump(wrong_notes, f, ensure_ascii=False, indent=2)
    
    def load_wrong_notes(self) -> List[Dict[str, Any]]:
        """加载错题集"""
        if not self.wrong_notes_file.exists():
            return []
        
        with open(self.wrong_notes_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def remove_wrong_answer(self, question_id: str) -> None:
        """移除单道错题"""
        wrong_notes = self.load_wrong_notes()
        wrong_notes = [note for note in wrong_notes if note.get("id") != question_id]
        
        with open(self.wrong_notes_file, "w", encoding="utf-8") as f:
            json.dump(wrong_notes, f, ensure_ascii=False, indent=2)
    
    def clear_wrong_notes(self) -> None:
        """清空错题集"""
        if self.wrong_notes_file.exists():
            self.wrong_notes_file.unlink()
    
    def save_history(self, history: Dict[str, Any]) -> None:
        """保存答题历史"""
        histories = self.load_history()
        histories.append({
            **history,
            "timestamp": datetime.now().isoformat()
        })
        
        # 只保留最近 100 条
        histories = histories[-100:]
        
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(histories, f, ensure_ascii=False, indent=2)
    
    def load_history(self) -> List[Dict[str, Any]]:
        """加载答题历史"""
        if not self.history_file.exists():
            return []
        
        with open(self.history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        wrong_notes = self.load_wrong_notes()
        history = self.load_history()
        
        total_answered = len(history)
        correct_count = sum(1 for h in history if h.get("is_correct", False))
        correct_rate = correct_count / total_answered if total_answered > 0 else 0
        
        # 按题型统计
        single_choice_total = sum(1 for h in history if h.get("type") == "single_choice")
        single_choice_correct = sum(1 for h in history if h.get("type") == "single_choice" and h.get("is_correct"))
        
        case_total = sum(1 for h in history if h.get("type") == "case_analysis")
        case_correct = sum(1 for h in history if h.get("type") == "case_analysis" and h.get("is_correct"))
        
        return {
            "total_answered": total_answered,
            "correct_count": correct_count,
            "wrong_count": total_answered - correct_count,
            "correct_rate": f"{correct_rate:.1%}",
            "wrong_notes_count": len(wrong_notes),
            "single_choice": {
                "total": single_choice_total,
                "correct": single_choice_correct,
                "rate": f"{single_choice_correct/single_choice_total:.1%}" if single_choice_total > 0 else "0%"
            },
            "case_analysis": {
                "total": case_total,
                "correct": case_correct,
                "rate": f"{case_correct/case_total:.1%}" if case_total > 0 else "0%"
            }
        }
