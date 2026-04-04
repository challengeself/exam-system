"""直接测试选项显示"""
import streamlit as st

st.title("🧪 测试多选题选项显示")

# 模拟题目数据
question = {
    "type": "multiple_choice",
    "options": ['A. 选项 1', 'B. 选项 2', 'C. 选项 3', 'D. 选项 4'],
    "is_multiple": True
}

st.write(f"**type**: {question['type']}")
st.write(f"**is_multiple**: {question.get('is_multiple')}")
st.write(f"**options**: {question.get('options')}")
st.write(f"**options 数量**: {len(question.get('options', []))}")

st.divider()

# 测试显示逻辑
options = question.get("options", [])
is_multiple = question.get("is_multiple", False)

st.write(f"**检测**: is_multiple={is_multiple}, options 数={len(options)}")

if is_multiple and options:
    st.success("✅ 进入多选题显示逻辑")
    
    st.write("**请选择答案（可多选）**")
    
    # 方式 1: 直接在页面显示 checkbox（不在 form 中）
    st.subheader("方式 1: 不在 form 中")
    for opt in options:
        opt_letter = opt.split(".")[0].strip()
        opt_text = opt.split(".", 1)[1].strip() if "." in opt else opt
        st.checkbox(f"{opt_letter}. {opt_text}")
    
    st.divider()
    
    # 方式 2: 在 form 中显示
    st.subheader("方式 2: 在 form 中")
    with st.form(key="test_form"):
        for opt in options:
            opt_letter = opt.split(".")[0].strip()
            opt_text = opt.split(".", 1)[1].strip() if "." in opt else opt
            st.checkbox(f"{opt_letter}. {opt_text}", key=f"form_{opt_letter}")
        
        submit = st.form_submit_button("提交")
        
        if submit:
            selected = []
            for opt in options:
                opt_letter = opt.split(".")[0].strip()
                if st.session_state.get(f"form_{opt_letter}", False):
                    selected.append(opt_letter)
            st.write(f"选择：{selected}")
else:
    st.error(f"❌ 未进入多选题逻辑：is_multiple={is_multiple}, options={len(options)}")
