import streamlit as st

st.set_page_config(page_title="我的AI助手", page_icon="🤖")
st.title("🤖 我的AI助手")

st.info("""
### 项目说明

这是一个基于 Ollama + Streamlit 的本地 AI 助手。

**本地运行方法：**
1. 安装 Ollama
2. 下载模型：ollama pull llama3:8b
3. 运行：streamlit run app.py

**项目特点：**
- 数据完全本地化，保护隐私
- 无需联网，免费使用
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("设置")
    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("输入你的问题..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        st.write("这是云端演示版本。请在本地运行完整版应用以获得 AI 回复。")
        st.session_state.messages.append({"role": "assistant", "content": "这是云端演示版本。请在本地运行完整版应用以获得 AI 回复。"})
