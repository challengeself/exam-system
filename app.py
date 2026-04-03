"""心理健康指导师考试模拟系统 - 增强版"""
import streamlit as st
import sys
import os
import json
import re
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doc_parser import parse_word_document, calculate_keyword_match
from storage import DataManager

# 页面配置
st.set_page_config(
    page_title="心理健康指导师考试模拟系统",
    page_icon="🧠",
    layout="wide"
)

# 初始化数据管理器
dm = DataManager("storage")

# ============== 初始化 session state ==============
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0  # 当前案例索引
if "sub_current_index" not in st.session_state:
    st.session_state.sub_current_index = 0  # 案例内小题索引
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "show_result" not in st.session_state:
    st.session_state.show_result = False
if "mode" not in st.session_state:
    st.session_state.mode = "home"
if "current_library" not in st.session_state:
    st.session_state.current_library = None
if "practice_from_wrong" not in st.session_state:
    st.session_state.practice_from_wrong = False
if "wrong_practice_questions" not in st.session_state:
    st.session_state.wrong_practice_questions = []
if "page_refreshed" not in st.session_state:
    st.session_state.page_refreshed = False
if "case_groups" not in st.session_state:
    st.session_state.case_groups = []  # 案例分组 [[案例 1 题目列表], [案例 2 题目列表], ...]


# ============== 辅助函数 ==============
def get_saved_libraries():
    """获取所有已保存的题库列表"""
    libraries_file = "storage/libraries.json"
    if os.path.exists(libraries_file):
        with open(libraries_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_library(library_name, questions_data):
    """保存题库"""
    libraries_file = "storage/libraries.json"
    libraries = get_saved_libraries()
    
    # 检查是否已存在
    for lib in libraries:
        if lib["name"] == library_name:
            lib["questions"] = questions_data
            lib["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    else:
        libraries.append({
            "name": library_name,
            "questions": questions_data,
            "question_count": len(questions_data),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    os.makedirs("storage", exist_ok=True)
    with open(libraries_file, 'w', encoding='utf-8') as f:
        json.dump(libraries, f, ensure_ascii=False, indent=2)

def load_library(library_name):
    """加载指定题库"""
    libraries = get_saved_libraries()
    for lib in libraries:
        if lib["name"] == library_name:
            return lib["questions"]
    return None

def delete_library(library_name):
    """删除题库"""
    libraries = get_saved_libraries()
    libraries = [lib for lib in libraries if lib["name"] != library_name]
    
    libraries_file = "storage/libraries.json"
    os.makedirs("storage", exist_ok=True)
    with open(libraries_file, 'w', encoding='utf-8') as f:
        json.dump(libraries, f, ensure_ascii=False, indent=2)

def group_questions_by_case(questions):
    """
    将题目按案例分组
    - 面试答辩题：每个案例单独一组
    - 笔试选择题：同一个案例的题目归为一组
    """
    groups = []
    current_group = []
    current_case_prefix = None
    
    for q in questions:
        # 提取案例前缀（从 ID 中提取）
        q_id = q.get("id", "")
        # 面试答辩题单独成组
        if q.get("type") == "case_interview":
            if current_group:
                groups.append(current_group)
                current_group = []
            groups.append([q])
            continue
        
        # 笔试选择题：从 ID 提取案例标识
        # ID 格式：case_单选_1_1, case_多选_1_3 等，第一个数字部分是案例索引
        import re
        match = re.search(r'case_.*?_(\d+)_(\d+)', q_id)
        if match:
            case_idx = match.group(1)
            if current_case_prefix is None:
                current_case_prefix = case_idx
                current_group = [q]
            elif case_idx == current_case_prefix:
                current_group.append(q)
            else:
                # 新案例
                if current_group:
                    groups.append(current_group)
                current_group = [q]
                current_case_prefix = case_idx
        else:
            # 普通题目（无案例）
            if current_group:
                groups.append(current_group)
                current_group = []
            groups.append([q])
    
    if current_group:
        groups.append(current_group)
    
    return groups


def reset_practice_state():
    """重置答题状态"""
    st.session_state.current_index = 0
    st.session_state.sub_current_index = 0
    st.session_state.answers = {}
    st.session_state.show_result = False
    st.session_state.practice_from_wrong = False


# ============== 侧边栏 ==============
with st.sidebar:
    st.title("🧠 心理考试模拟系统")
    st.markdown("---")
    
    # 导航
    menu = st.radio(
        "导航",
        ["📚 题库管理", "✏️ 开始答题", "❌ 错题集", "📊 统计"],
        index=1 if st.session_state.questions else 0
    )
    
    if menu == "📚 题库管理":
        st.session_state.mode = "import"
    elif menu == "✏️ 开始答题":
        st.session_state.mode = "practice"
    elif menu == "❌ 错题集":
        st.session_state.mode = "wrong_notes"
    elif menu == "📊 统计":
        st.session_state.mode = "stats"
    
    st.markdown("---")
    
    # 当前题库信息
    if st.session_state.questions:
        st.info(f"✅ 已加载 {len(st.session_state.questions)} 道题")
        if st.session_state.current_library:
            st.caption(f"📁 题库：{st.session_state.current_library}")
    else:
        st.warning("⚠️ 请先导入题库")


# ============== 页面：题库管理 ==============
if st.session_state.mode == "import":
    st.title("📚 题库管理")
    
    # 选项卡：上传新题库 / 选择已保存题库
    tab1, tab2 = st.tabs(["📤 上传新题库", "📂 选择已保存题库"])
    
    with tab1:
        st.markdown("支持上传多个 Word 文档格式（.docx），上传后自动保存到本地")
        
        uploaded_files = st.file_uploader(
            "上传 Word 题库文件（可多选）",
            type=["docx"],
            accept_multiple_files=True,
            help="按住 Ctrl 键可选择多个文件"
        )
        
        library_name = st.text_input(
            "题库名称（可选）",
            placeholder="例如：2026 年模拟题库",
            help="给这个题库起个名字，方便下次选择。不填写则使用文件名"
        )
        
        if uploaded_files:
            all_questions = []
            
            for uploaded_file in uploaded_files:
                with st.spinner(f"正在解析 {uploaded_file.name}..."):
                    file_path = f"uploads/{uploaded_file.name}"
                    os.makedirs("uploads", exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    try:
                        questions = parse_word_document(file_path)
                        
                        if questions:
                            # 去掉扩展名获取文件名
                            file_name_no_ext = os.path.splitext(uploaded_file.name)[0]
                            for q in questions:
                                q_dict = {
                                    "id": f"{file_name_no_ext}_{q.id}",
                                    "source_file": uploaded_file.name,
                                    "type": q.type.value,
                                    "content": q.content,
                                    "answer": q.answer,
                                    "analysis": q.analysis,
                                    "keywords": q.keywords if hasattr(q, 'keywords') else []
                                }
                                
                                if q.type.value == "single_choice":
                                    q_dict["options"] = q.options if hasattr(q, 'options') else []
                                    q_dict["correct_option"] = q.correct_option if hasattr(q, 'correct_option') else ""
                                elif q.type.value == "case_analysis":
                                    q_dict["sub_questions"] = q.sub_questions if hasattr(q, 'sub_questions') else []
                                    q_dict["case_background"] = q.case_background if hasattr(q, 'case_background') else ""
                                
                                all_questions.append(q_dict)
                            
                            st.success(f"✅ {uploaded_file.name}: 解析 {len(questions)} 道题目")
                        else:
                            st.warning(f"⚠️ {uploaded_file.name}: 未解析到题目")
                            
                    except Exception as e:
                        st.error(f"❌ {uploaded_file.name}: 解析失败 - {str(e)}")
            
            if all_questions:
                st.success(f"🎉 共解析 {len(all_questions)} 道题目！")
                
                # 自动保存题库
                auto_library_name = library_name or os.path.splitext(uploaded_files[0].name)[0]
                save_library(auto_library_name, all_questions)
                st.session_state.questions = all_questions
                st.session_state.current_library = auto_library_name
                # 按案例分组
                st.session_state.case_groups = group_questions_by_case(all_questions)
                reset_practice_state()
                st.success(f"✅ 题库 '{auto_library_name}' 已自动保存到本地并加载！")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 开始答题", type="primary", use_container_width=True):
                        st.session_state.mode = "practice"
                        st.rerun()
                with col2:
                    if st.button("📋 查看题目预览", use_container_width=True):
                        st.rerun()
                
                # 题目预览
                with st.expander("📋 题目预览", expanded=False):
                    single_count = sum(1 for q in all_questions if q["type"] == "single_choice")
                    multiple_count = sum(1 for q in all_questions if q["type"] == "multiple_choice")
                    interview_count = sum(1 for q in all_questions if q["type"] == "case_interview")
                    st.write(f"- 单选题：{single_count} 道")
                    st.write(f"- 多选题：{multiple_count} 道")
                    st.write(f"- 面试答辩题：{interview_count} 道")
                    st.caption("💡 注：笔试案例题中的单选/多选已拆分为独立题目")
    
    with tab2:
        st.markdown("### 已保存的题库")
        
        libraries = get_saved_libraries()
        
        if not libraries:
            st.info("📭 还没有保存的题库，请先上传题库")
        else:
            for lib in libraries:
                with st.container():
                    col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
                    with col1:
                        st.write(f"**📚 {lib['name']}**")
                        st.caption(f"共 {lib['question_count']} 道题 | 更新于 {lib['updated_at']}")
                    with col2:
                        if st.button("📖 加载", key=f"load_{lib['name']}", use_container_width=True):
                            questions = load_library(lib['name'])
                            if questions:
                                st.session_state.questions = questions
                                st.session_state.current_library = lib['name']
                                st.session_state.case_groups = group_questions_by_case(questions)
                                reset_practice_state()
                                st.success(f"✅ 已加载题库 '{lib['name']}'")
                                st.rerun()
                    with col3:
                        if st.button("🗑️ 删除", key=f"del_{lib['name']}", use_container_width=True):
                            delete_library(lib['name'])
                            st.success(f"✅ 题库 '{lib['name']}' 已删除")
                            st.rerun()
                    with col4:
                        if lib['name'] == st.session_state.current_library:
                            st.success("✅")
                    st.markdown("---")


# ============== 页面：开始答题 ==============
elif st.session_state.mode == "practice":
    if not st.session_state.questions:
        st.warning("⚠️ 请先在【题库管理】页面导入题库")
        st.stop()
    
    st.title("✏️ 开始答题")
    
    # 如果是从错题集开始的练习
    if st.session_state.practice_from_wrong:
        st.info(f"📝 错题集练习模式 - 共 {len(st.session_state.questions)} 道错题")
        if st.button("🔄 返回正常题库"):
            if st.session_state.current_library:
                st.session_state.questions = load_library(st.session_state.current_library)
                st.session_state.case_groups = group_questions_by_case(st.session_state.questions)
            st.session_state.practice_from_wrong = False
            st.session_state.wrong_practice_questions = []
            reset_practice_state()
            st.rerun()
    
    # 如果没有分组，按旧模式处理
    if not st.session_state.case_groups:
        st.session_state.case_groups = group_questions_by_case(st.session_state.questions)
    
    # 进度条
    total_cases = len(st.session_state.case_groups)
    current_case_idx = st.session_state.current_index
    current_case = st.session_state.case_groups[current_case_idx]
    total_sub = len(current_case)
    current_sub_idx = st.session_state.sub_current_index
    
    # 计算总进度
    completed_cases = current_case_idx
    completed_in_case = current_sub_idx
    total_questions = sum(len(g) for g in st.session_state.case_groups)
    completed_total = sum(len(st.session_state.case_groups[i]) for i in range(current_case_idx)) + current_sub_idx
    progress = (completed_total + 1) / total_questions if total_questions > 0 else 0
    st.progress(progress)
    
    # 题目概览 - 右上角悬浮面板
    st.markdown("""
    <style>
    .question-panel {
        position: fixed;
        top: 100px;
        right: 20px;
        width: 220px;
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 999;
    }
    .question-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 5px;
    }
    .question-btn {
        width: 100%;
        min-width: 18px;
        height: 28px;
        font-size: 12px;
        padding: 2px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 主答题区域
    with st.container():
        st.write(f"#### 案例 {current_case_idx + 1} / {total_cases} - 小题 {current_sub_idx + 1} / {total_sub}")
        
        # 统计信息（小字显示）
        answered_count = len(st.session_state.answers)
        correct_count = sum(1 for a in st.session_state.answers.values() if a.get("is_correct", False))
        st.caption(f"📊 已答：{answered_count}/{total_questions} | 正确：{correct_count}")
        
        # 显示案例背景（固定显示，不折叠）
        question = current_case[current_sub_idx]
        content = question.get("content", "")
        if content.startswith("【案例】"):
            parts = content.split("\n\n", 1)
            case_background = parts[0].replace("【案例】", "").strip()
            question_text = parts[1].strip() if len(parts) > 1 else ""
            
            # 案例背景固定在顶部
            st.markdown(f"**📖 案例背景**")
            st.info(case_background)
            
            # 显示当前小题
            st.markdown(f"**{question_text}**")
        else:
            # 普通题目（无案例背景）
            st.markdown(f"**{content}**")
        
        # 根据题型显示不同界面
        if question["type"] in ["single_choice", "multiple_choice"]:
            options = question.get("options", [])
            is_multiple = question.get("is_multiple", False)
            
            # 使用案例索引 + 小题索引作为唯一 key
            form_key = f"question_{current_case_idx}_{current_sub_idx}"
            radio_key = f"radio_{current_case_idx}_{current_sub_idx}"
            checkbox_key = f"checkbox_{current_case_idx}_{current_sub_idx}"
            
            with st.form(key=form_key):
                if is_multiple:
                    # 多选题使用多个 checkbox
                    st.write("**请选择答案（可多选）**")
                    selected_options = []
                    for opt in options:
                        opt_letter = opt.split(".")[0].strip()
                        opt_text = opt.split(".", 1)[1].strip() if "." in opt else opt
                        if st.checkbox(f"{opt_letter}. {opt_text}", key=f"{checkbox_key}_{opt_letter}"):
                            selected_options.append(opt_letter)
                else:
                    # 单选题使用单选框
                    selected = st.radio(
                        "请选择答案",
                        options,
                        key=radio_key,
                        index=None
                    )
                    selected_options = [selected.split(".")[0].strip()] if selected else []
                
                submit = st.form_submit_button("提交答案")
                
                if submit and selected_options:
                    correct_option = question.get("correct_option", "")
                    # 正确答案可能是多个字母（如"ABCD"）
                    correct_set = set(correct_option)
                    selected_set = set(selected_options)
                    is_correct = selected_set == correct_set
                    
                    user_answer_str = "".join(selected_options) if is_multiple else selected_options[0]
                    
                    st.session_state.answers[question["id"]] = {
                        "user_answer": user_answer_str,
                        "is_correct": is_correct,
                        "correct_answer": correct_option
                    }
                    
                    dm.save_history({
                        "question_id": question["id"],
                        "type": "multiple_choice" if is_multiple else "single_choice",
                        "user_answer": user_answer_str,
                        "correct_answer": correct_option,
                        "is_correct": is_correct
                    })
                    
                    if not is_correct:
                        dm.save_wrong_answer({
                            **question,
                            "user_answer": user_answer_str
                        })
                    
                    st.session_state.show_result = True
                    st.rerun()
        
        elif question["type"] == "case_analysis":
            # 显示案例背景
            case_background = question.get("case_background", "")
            if case_background:
                st.markdown(f"**【案例描述】**\n\n{case_background}")
                st.markdown("---")
            
            # 显示子问题列表
            sub_questions = question.get("sub_questions", [])
            if sub_questions:
                st.markdown("**【问题】**")
                for i, sq in enumerate(sub_questions, 1):
                    st.write(f"{i}. {sq}")
            
            user_answer = st.text_area(
                "请输入你的答案",
                key=f"text_{current_case_idx}_{current_sub_idx}",
                height=200,
                placeholder="请输入关键词或完整答案..."
            )
            
            if st.button("提交答案"):
                if user_answer.strip():
                    keywords = question.get("keywords", [])
                    is_correct, match_rate, matched_keywords = calculate_keyword_match(user_answer, keywords)
                    
                    st.session_state.answers[question["id"]] = {
                        "user_answer": user_answer,
                        "is_correct": is_correct,
                        "match_rate": match_rate,
                        "matched_keywords": matched_keywords
                    }
                    
                    dm.save_history({
                        "question_id": question["id"],
                        "type": "case_analysis",
                        "user_answer": user_answer,
                        "is_correct": is_correct,
                        "match_rate": match_rate
                    })
                    
                    if not is_correct:
                        dm.save_wrong_answer({
                            **question,
                            "user_answer": user_answer
                        })
                    
                    st.session_state.show_result = True
                    st.rerun()
                else:
                    st.warning("请先输入答案")
        
        elif question["type"] == "case_interview":
            # 面试答辩题
            case_background = question.get("case_background", "")
            if case_background:
                st.markdown(f"**【案例描述】**\n\n{case_background}")
                st.markdown("---")
            
            # 显示问题列表
            interview_questions = question.get("questions", [])
            if interview_questions:
                st.markdown("**【问题】**")
                for i, q in enumerate(interview_questions, 1):
                    st.write(f"{i}. {q}")
            
            st.markdown("**【请逐题回答】**")
            
            # 为每个问题创建独立的答题区域
            user_answers = {}
            for i, q in enumerate(interview_questions):
                user_answers[i] = st.text_area(
                    f"问题{i+1}的答案",
                    key=f"interview_q{current_case_idx}_{current_sub_idx}_{i}",
                    height=150,
                    placeholder=f"请回答问题{i+1}..."
                )
            
            if st.button("提交答案"):
                all_answers = {i: ans for i, ans in user_answers.items() if ans.strip()}
                if all_answers:
                    # 合并所有答案进行关键词匹配
                    combined_answer = "\n".join(all_answers.values())
                    keywords = question.get("keywords", [])
                    is_correct, match_rate, matched_keywords = calculate_keyword_match(combined_answer, keywords)
                    
                    st.session_state.answers[question["id"]] = {
                        "user_answer": all_answers,
                        "is_correct": is_correct,
                        "match_rate": match_rate,
                        "matched_keywords": matched_keywords
                    }
                    
                    dm.save_history({
                        "question_id": question["id"],
                        "type": "case_interview",
                        "user_answer": all_answers,
                        "is_correct": is_correct,
                        "match_rate": match_rate
                    })
                    
                    if not is_correct:
                        dm.save_wrong_answer({
                            **question,
                            "user_answer": combined_answer
                        })
                    
                    st.session_state.show_result = True
                    st.rerun()
                else:
                    st.warning("请至少回答一个问题")
    
    # 显示结果和解析
    if st.session_state.show_result and question["id"] in st.session_state.answers:
        answer_info = st.session_state.answers[question["id"]]
        
        st.markdown("---")
        
        if answer_info["is_correct"]:
            st.success("✅ 回答正确！")
        else:
            st.error("❌ 回答错误")
            
            if question["type"] == "case_analysis":
                match_rate = answer_info.get("match_rate", 0)
                matched = answer_info.get("matched_keywords", [])
                st.write(f"**关键词匹配度**: {match_rate:.1%}")
                if matched:
                    st.write(f"**命中的关键词**: {', '.join(matched)}")
        
        with st.expander("📖 查看参考答案", expanded=True):
            st.write(question["answer"])
        
        with st.expander("💡 查看解析", expanded=True):
            st.write(question["analysis"])
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            # 上一小题
            if current_sub_idx > 0:
                if st.button("⏮️ 上一小题", use_container_width=True):
                    st.session_state.sub_current_index -= 1
                    st.session_state.show_result = False
                    st.rerun()
            else:
                st.button("⏮️ 上一小题", disabled=True, use_container_width=True)
        with col2:
            # 下一小题 或 下一案例
            if current_sub_idx < total_sub - 1:
                if st.button("下一小题 ⏭️", use_container_width=True):
                    st.session_state.sub_current_index += 1
                    st.session_state.show_result = False
                    st.rerun()
            elif current_case_idx < total_cases - 1:
                if st.button("下一案例 ⏩", type="primary", use_container_width=True):
                    st.session_state.current_index += 1
                    st.session_state.sub_current_index = 0
                    st.session_state.show_result = False
                    st.rerun()
            else:
                st.success("🎉 已完成所有题目！")
        with col3:
            if st.button("🔁 重新作答", use_container_width=True):
                st.session_state.answers = {}
                st.session_state.current_index = 0
                st.session_state.sub_current_index = 0
                st.session_state.show_result = False
                st.rerun()
    
    # 悬浮题目面板 - 右上角固定位置
    with st.container():
        st.markdown('<div class="question-panel">', unsafe_allow_html=True)
        st.markdown("**📋 案例**")
        
        # 显示案例分组导航
        for case_idx, case_group in enumerate(st.session_state.case_groups):
            case_num = case_idx + 1
            is_current_case = case_idx == current_case_idx
            
            # 计算本案例答题进度
            answered_in_case = sum(1 for q in case_group if q.get("id") in st.session_state.answers)
            total_in_case = len(case_group)
            
            # 案例按钮
            if is_current_case:
                st.markdown(f"**📍 案例{case_num}** ({answered_in_case}/{total_in_case})")
            else:
                st.markdown(f"案例{case_num} ({answered_in_case}/{total_in_case})")
            
            # 显示本案例内各小题状态（每行最多 10 个）
            cols_count = min(total_in_case, 10)
            rows = (total_in_case + cols_count - 1) // cols_count
            
            for row in range(rows):
                row_cols = st.columns(cols_count)
                start_idx = row * cols_count
                end_idx = min(start_idx + cols_count, total_in_case)
                
                for col_idx, sub_idx in enumerate(range(start_idx, end_idx)):
                    with row_cols[col_idx]:
                        q = case_group[sub_idx]
                        q_id = q.get("id")
                        is_answered = q_id in st.session_state.answers
                        is_correct = st.session_state.answers.get(q_id, {}).get("is_correct", False) if is_answered else False
                        is_current = (case_idx == current_case_idx and sub_idx == current_sub_idx)
                        
                        # 按钮样式
                        if is_current:
                            btn_type = "primary"
                        elif is_correct:
                            btn_type = "success"
                        elif is_answered:
                            btn_type = "secondary"
                        else:
                            btn_type = "secondary"
                        
                        # 按钮标签
                        btn_label = f"{sub_idx + 1}"
                        if is_correct:
                            btn_label = "✅"
                        elif is_answered:
                            btn_label = "❌"
                        
                        if st.button(
                            btn_label,
                            key=f"nav_{case_idx}_{sub_idx}",
                            type=btn_type,
                            use_container_width=True,
                            help=f"案例{case_num}-小题{sub_idx+1}"
                        ):
                            st.session_state.current_index = case_idx
                            st.session_state.sub_current_index = sub_idx
                            st.session_state.show_result = False
                            st.rerun()
            
            st.markdown("---")
        
        # 快捷操作
        if st.button("🔁 从头开始", use_container_width=True, key="restart_practice"):
            st.session_state.current_index = 0
            st.session_state.sub_current_index = 0
            st.session_state.answers = {}
            st.session_state.show_result = False
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


# ============== 页面：错题集 ==============
elif st.session_state.mode == "wrong_notes":
    st.title("❌ 错题集")
    
    wrong_notes = dm.load_wrong_notes()
    
    if not wrong_notes:
        st.info("🎉 太棒了！目前没有错题")
    else:
        # 统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("错题总数", len(wrong_notes))
        with col2:
            single_wrong = sum(1 for n in wrong_notes if n.get("type") == "single_choice")
            st.metric("单选题", single_wrong)
        with col3:
            case_wrong = sum(1 for n in wrong_notes if n.get("type") == "case_analysis")
            st.metric("案例分析", case_wrong)
        
        st.markdown("---")
        
        # 操作按钮
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("📝 从错题集开始练习", type="primary", use_container_width=True):
                st.session_state.questions = wrong_notes
                st.session_state.practice_from_wrong = True
                st.session_state.wrong_practice_questions = wrong_notes.copy()
                reset_practice_state()
                st.session_state.mode = "practice"
                st.rerun()
        with col2:
            if st.button("🗑️ 清空错题集", use_container_width=True):
                dm.clear_wrong_notes()
                st.success("✅ 错题集已清空")
                st.rerun()
        
        st.markdown("---")
        
        # 错题列表
        st.markdown("### 错题列表")
        
        for i, note in enumerate(wrong_notes, 1):
            with st.expander(f"❌ 错题 {i} - {note.get('type', 'unknown')}", expanded=False):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**题目**: {note.get('content', '')}")
                    st.write(f"**你的答案**: {note.get('user_answer', '')}")
                    st.write(f"**正确答案**: {note.get('answer', '')}")
                    if note.get('analysis'):
                        st.write(f"**解析**: {note.get('analysis', '')}")
                    st.write(f"**错误次数**: {note.get('wrong_count', 1)}")
                with col2:
                    if st.button("🗑️ 移除", key=f"remove_wrong_{i}"):
                        dm.remove_wrong_answer(note.get('id', f'wrong_{i}'))
                        st.success("✅ 已移除")
                        st.rerun()


# ============== 页面：统计 ==============
elif st.session_state.mode == "stats":
    st.title("📊 统计信息")
    
    stats = dm.get_statistics()
    
    # 总体统计
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总答题数", stats["total_answered"])
    with col2:
        st.metric("正确数", stats["correct_count"])
    with col3:
        st.metric("错误数", stats["wrong_count"])
    with col4:
        st.metric("正确率", stats["correct_rate"])
    
    st.markdown("---")
    
    # 按题型统计
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("单选题")
        st.write(f"答题数：{stats['single_choice']['total']}")
        st.write(f"正确数：{stats['single_choice']['correct']}")
        st.write(f"正确率：{stats['single_choice']['rate']}")
    
    with col2:
        st.subheader("案例分析题")
        st.write(f"答题数：{stats['case_analysis']['total']}")
        st.write(f"正确数：{stats['case_analysis']['correct']}")
        st.write(f"正确率：{stats['case_analysis']['rate']}")
    
    st.markdown("---")
    st.write(f"❌ 错题集：{stats['wrong_notes_count']} 道题")
    
    # 题库信息
    st.markdown("---")
    st.subheader("📚 本地题库")
    libraries = get_saved_libraries()
    if libraries:
        for lib in libraries:
            st.write(f"- **{lib['name']}**: {lib['question_count']} 道题 (更新于 {lib['updated_at']})")
    else:
        st.info("还没有保存的题库")
