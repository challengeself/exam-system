"""最小化测试：检查多选题选项显示"""
import streamlit as st
import json

# 模拟加载的数据
test_question = {
    "id": "case_多选_1_4",
    "type": "multiple_choice",
    "content": "【案例】测试案例\n\n咨询目标由心理咨询师与求助者共同商定，以下哪些属于可行的咨询目标（）",
    "options": ['A. 属于心理学范畴', 'B. 积极的', 'C. 具体或量化的', 'D. 可以评估的'],
    "correct_option": "ABCD",
    "is_multiple": True
}

st.title("🧪 多选题选项测试")

question = test_question
current_case_idx = 0
current_sub_idx = 0

st.write(f"**题目类型**: {question['type']}")
st.write(f"**是否多选**: {question.get('is_multiple')}")
st.write(f"**选项数量**: {len(question.get('options', []))}")
st.write(f"**选项内容**: {question.get('options')}")

st.divider()

# 复制答题界面逻辑
if question["type"] in ["single_choice", "multiple_choice"]:
    options = question.get("options", [])
    is_multiple = question.get("is_multiple", False)
    
    st.info(f"🔍 检测：type={question['type']}, is_multiple={is_multiple}, options 数={len(options)}")
    
    form_key = f"question_{current_case_idx}_{current_sub_idx}"
    checkbox_key = f"checkbox_{current_case_idx}_{current_sub_idx}"
    
    with st.form(key=form_key):
        if is_multiple:
            st.write("**请选择答案（可多选）**")
            selected_options = []
            
            st.write(f"**遍历 options (共{len(options)}个):**")
            for idx, opt in enumerate(options):
                st.write(f"{idx}. opt = `{opt}`")
                opt_letter = opt.split(".")[0].strip()
                opt_text = opt.split(".", 1)[1].strip() if "." in opt else opt
                st.write(f"   → opt_letter = `{opt_letter}`, opt_text = `{opt_text}`")
                
                if st.checkbox(f"{opt_letter}. {opt_text}", key=f"{checkbox_key}_{opt_letter}"):
                    selected_options.append(opt_letter)
            
            st.write(f"**最终选择**: {selected_options}")
        
        submit = st.form_submit_button("提交答案")
        if submit:
            st.write(f"提交的选择：{selected_options}")
