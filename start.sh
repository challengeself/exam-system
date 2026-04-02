#!/bin/bash
# 启动心理健康指导师考试模拟系统

cd /root/.openclaw/workspace/exam-system

echo "🧠 启动心理健康指导师考试模拟系统..."
echo "访问地址：http://localhost:8501"
echo ""

streamlit run app.py --server.port 8501 --server.headless true
