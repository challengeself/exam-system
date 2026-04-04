import streamlit as st

st.title("简单测试")

options = ['A. 选项 1', 'B. 选项 2', 'C. 选项 3', 'D. 选项 4']

st.write(f"options: {options}")
st.write(f"数量：{len(options)}")

with st.form("test"):
    st.write("**选项**")
    for opt in options:
        st.write(f"  - {opt}")
        opt_letter = opt.split(".")[0].strip()
        opt_text = opt.split(".", 1)[1].strip()
        st.checkbox(f"{opt_letter}. {opt_text}", key=f"chk_{opt_letter}")
    
    st.form_submit_button("提交")

st.write("Form 外内容")
