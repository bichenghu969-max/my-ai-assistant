import streamlit as st

st.set_page_config(page_title="我的AI助手", page_icon="🤖")
st.title("🤖 我的AI助手")

st.info("""
### 📌 说明

这是一个部署在云端的 AI 助手演示界面。

**完整功能需要本地运行：**
1. 安装 Ollama
2. 下载模型：`ollama pull llama3:8b`
3. 运行：`streamlit run app.py`

**项目特点：**
- 完全本地化，数据隐私安全
- 无需联网，免费无限使用
- 支持多种开源模型切换
""")

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 侧边栏
with st.sidebar:
    st.header("⚙️ 设置")
    
    st.success("✅ 应用已成功部署！")
    st.markdown("""
    **技术栈：**
    - Streamlit (前端框架)
    - Ollama (本地大模型)
    - Python (后端逻辑)
    """)
    
    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 用户输入
if prompt := st.chat_input("输入你的问题..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        st.info("💡 这是云端演示版本。\n\n如需获得实际 AI 回复，请按照左侧说明在本地运行完整版应用。")
        st.session_state.messages.append({"role": "assistant", "content": "这是云端演示版本。请在本地运行完整版应用以获得 AI 回复。"})
