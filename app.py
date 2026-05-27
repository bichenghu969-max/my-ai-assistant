import streamlit as st
import requests

st.set_page_config(page_title="我的AI助手", page_icon="🤖")
st.title("🤖 我的AI助手")

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 侧边栏
with st.sidebar:
    st.header("设置")

    # 显示可用的模型
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            st.success("✅ AI 服务已连接")
            models = [m["name"] for m in r.json().get("models", [])]
            if models:
                selected_model = st.selectbox("选择模型", models)
            else:
                selected_model = "llama3:8b"
        else:
            selected_model = "llama3:8b"
    except:
        selected_model = "llama3:8b"
        st.warning("检测中...")

    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 用户输入
if prompt := st.chat_input("输入你的问题..."):
    # 显示用户消息
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI 回复
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": selected_model, "prompt": prompt, "stream": False},
                    timeout=60
                )
                if response.status_code == 200:
                    answer = response.json().get("response", "无回复")
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"错误: {response.status_code}")
            except Exception as e:
                st.error(f"连接失败: {e}")