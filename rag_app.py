import streamlit as st
import requests
import io
from pypdf import PdfReader

st.set_page_config(page_title="AI知识库助手", page_icon="📚")
st.title("📚 AI知识库助手")
st.caption("上传 PDF 文档，AI 会根据文档内容回答问题")

# 初始化 session_state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = {}  # 存储 {文件名: 文本内容}
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "llama3:8b"


# 函数：提取 PDF 文本
def extract_pdf_text(uploaded_file):
    """从 PDF 文件中提取文本"""
    pdf = PdfReader(io.BytesIO(uploaded_file.getvalue()))
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"
    return text


# 函数：切分文本
def split_text(text, chunk_size=500):
    """将长文本切分成小块"""
    chunks = []
    lines = text.split("\n")
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) < chunk_size:
            current_chunk += line + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line + "\n"

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# 函数：从知识库检索相关内容
def retrieve_context(query, max_chunks=3):
    """从知识库中检索相关的内容片段"""
    if not st.session_state.knowledge_base:
        return None, []

    all_chunks = []
    for doc_name, doc_data in st.session_state.knowledge_base.items():
        for chunk in doc_data["chunks"]:
            all_chunks.append({
                "text": chunk,
                "source": doc_name
            })

    # 简单的关键词匹配检索
    query_words = query.lower().split()
    scored_chunks = []

    for chunk in all_chunks:
        chunk_lower = chunk["text"].lower()
        score = sum(1 for word in query_words if word in chunk_lower)
        if score > 0:
            scored_chunks.append((score, chunk))

    # 按相关度排序
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    top_chunks = [chunk for score, chunk in scored_chunks[:max_chunks]]

    return top_chunks, scored_chunks


# ========== 侧边栏 ==========
with st.sidebar:
    st.header("⚙️ 设置")

    # 模型选择
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            st.success("✅ AI 服务已连接")
            models = [m["name"] for m in r.json().get("models", [])]
            if models:
                selected_model = st.selectbox("🤖 选择模型", models)
                st.session_state.selected_model = selected_model
            else:
                st.warning("未检测到模型，请先运行 ollama pull llama3:8b")
        else:
            st.error("❌ AI 服务连接失败")
    except:
        st.error("❌ 无法连接 Ollama，请确认服务已启动")

    st.divider()

    # ========== 文档上传区域 ==========
    st.header("📁 上传知识库文档")

    uploaded_files = st.file_uploader(
        "支持 PDF 文件",
        type=["pdf"],
        accept_multiple_files=True,
        help="上传 PDF 文档，AI 将学习这些内容"
    )

    # 处理上传的文档
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.knowledge_base:
                with st.spinner(f"正在处理 {uploaded_file.name}..."):
                    try:
                        # 提取文本
                        text = extract_pdf_text(uploaded_file)
                        # 切分文本
                        chunks = split_text(text)
                        # 存储
                        st.session_state.knowledge_base[uploaded_file.name] = {
                            "chunks": chunks,
                            "full_text": text
                        }
                        st.success(f"✅ 已处理 {uploaded_file.name} ({len(chunks)} 个片段)")
                    except Exception as e:
                        st.error(f"处理 {uploaded_file.name} 失败: {e}")

    # 显示已上传的文档
    if st.session_state.knowledge_base:
        st.markdown("### 📚 已加载文档")
        for name in st.session_state.knowledge_base.keys():
            st.caption(f"• {name}")

    # 清空知识库按钮
    if st.button("🗑️ 清空知识库", type="secondary"):
        st.session_state.knowledge_base = {}
        st.success("知识库已清空！")
        st.rerun()

    st.divider()

    # 清空对话按钮
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.rerun()

    # 显示状态
    if st.session_state.knowledge_base:
        st.success(f"📚 知识库已加载 ({len(st.session_state.knowledge_base)} 个文档)")
    else:
        st.info("📚 未加载知识库")

# ========== 聊天界面 ==========
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
                # 从知识库检索相关内容
                context_parts, _ = retrieve_context(prompt)

                # 构建提示词
                if context_parts:
                    context = "\n\n---\n\n".join([c["text"] for c in context_parts])
                    full_prompt = f"""请根据以下知识库内容回答用户的问题。

【知识库内容】
{context}

【用户问题】
{prompt}

请基于以上知识库内容回答。如果知识库中没有相关信息，请如实告知用户。"""
                    st.caption(f"📚 从知识库检索到 {len(context_parts)} 个相关片段")
                else:
                    full_prompt = f"用户问题：{prompt}\n\n请直接回答用户的问题。"
                    st.caption("📚 未找到相关内容")

                # 调用 Ollama
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": st.session_state.selected_model,
                        "prompt": full_prompt,
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