import streamlit as st
import requests

st.set_page_config(page_title="我的AI助手", page_icon="🤖")
st.title("🤖 我的AI助手")

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "llama3:8b"

# 侧边栏
with st.sidebar:
    st.header("⚙️ 设置")

    # 获取已安装的模型列表
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            st.success("✅ AI 服务已连接")
            models = [m["name"] for m in r.json().get("models", [])]
            if models:
                # 模型选择下拉框
                selected_model = st.selectbox(
                    "🤖 选择模型",
                    models,
                    index=models.index(
                        st.session_state.selected_model) if st.session_state.selected_model in models else 0
                )
                st.session_state.selected_model = selected_model
                st.caption(f"当前使用：{selected_model}")
            else:
                st.warning("未检测到模型，请先运行 ollama pull llama3:8b")
                st.session_state.selected_model = "llama3:8b"
        else:
            st.error("❌ AI 服务连接失败")
            st.session_state.selected_model = "llama3:8b"
    except:
        st.error("❌ 无法连接 Ollama，请确认服务已启动")
        st.session_state.selected_model = "llama3:8b"

    st.divider()

    if st.button("🗑️ 清空对话"):
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
                    json={
                        "model": st.session_state.selected_model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    answer = response.json().get("response", "无回复")
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"错误: {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("❌ 连接失败！请确保 Ollama 正在运行")
            except Exception as e:
                st.error(f"出错了: {e}")