import streamlit as st
import requests
import json
import os
import hashlib

st.set_page_config(page_title="AI智能助手", page_icon="🤖")
st.title("🤖 AI智能助手")

# ========== 初始化 ==========
CONVERSATIONS_FILE = "conversations.json"
KNOWLEDGE_FILE = "knowledge_base.json"


# 加载知识库
def load_knowledge_base():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"documents": []}


# 保存知识库
def save_knowledge_base(data):
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 加载对话
def load_conversations():
    if os.path.exists(CONVERSATIONS_FILE):
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"conversations": {}, "current_id": "default", "next_id": 2}


def save_conversations(data):
    with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 提取文本
def extract_text(uploaded_file):
    text = ""
    if uploaded_file.type == "application/pdf":
        try:
            from pypdf import PdfReader
            import io
            pdf = PdfReader(io.BytesIO(uploaded_file.getvalue()))
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        except:
            text = "PDF解析失败"
    else:
        try:
            text = uploaded_file.getvalue().decode("utf-8")
        except:
            text = uploaded_file.getvalue().decode("gbk", errors="ignore")
    return text


# 切分文本
def split_text(text, chunk_size=500):
    chunks = []
    sentences = text.replace('\n', ' ').split('。')
    current = ""
    for sent in sentences:
        if len(current) + len(sent) < chunk_size:
            current += sent + "。"
        else:
            if current:
                chunks.append(current)
            current = sent + "。"
    if current:
        chunks.append(current)
    return chunks


# 搜索知识库
def search_knowledge(query, documents, max_results=3):
    """简单的关键词搜索"""
    query_words = set(query.lower().split())
    results = []

    for doc in documents:
        doc_content = doc.get("content", "")
        doc_name = doc.get("name", "")
        # 计算匹配分数
        score = 0
        for word in query_words:
            if word in doc_content.lower():
                score += doc_content.lower().count(word)
        if score > 0:
            results.append({
                "name": doc_name,
                "content": doc_content,
                "score": score
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


# 初始化
if "conv_data" not in st.session_state:
    st.session_state.conv_data = load_conversations()
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "llama3:8b"
if "language" not in st.session_state:
    st.session_state.language = "中文"
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = load_knowledge_base()


# 获取当前对话
def get_current_messages():
    conv_id = st.session_state.conv_data["current_id"]
    if conv_id not in st.session_state.conv_data["conversations"]:
        st.session_state.conv_data["conversations"][conv_id] = {
            "name": "新对话",
            "messages": []
        }
    return st.session_state.conv_data["conversations"][conv_id]["messages"]


def save_current_messages(messages):
    conv_id = st.session_state.conv_data["current_id"]
    st.session_state.conv_data["conversations"][conv_id]["messages"] = messages
    save_conversations(st.session_state.conv_data)


def new_conversation():
    new_id = str(st.session_state.conv_data["next_id"])
    st.session_state.conv_data["conversations"][new_id] = {
        "name": f"对话{st.session_state.conv_data['next_id']}",
        "messages": []
    }
    st.session_state.conv_data["current_id"] = new_id
    st.session_state.conv_data["next_id"] += 1
    save_conversations(st.session_state.conv_data)
    st.rerun()


def delete_conversation(conv_id):
    if conv_id in st.session_state.conv_data["conversations"]:
        del st.session_state.conv_data["conversations"][conv_id]
        if st.session_state.conv_data["current_id"] == conv_id:
            first_id = list(st.session_state.conv_data["conversations"].keys())[0] if st.session_state.conv_data[
                "conversations"] else "default"
            st.session_state.conv_data["current_id"] = first_id
        save_conversations(st.session_state.conv_data)
        st.rerun()


# ========== 侧边栏 ==========
with st.sidebar:
    st.header("💬 对话管理")

    if st.button("➕ 新对话", use_container_width=True):
        new_conversation()

    st.subheader("历史对话")
    conv_items = list(st.session_state.conv_data["conversations"].items())
    for conv_id, conv in conv_items:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            if st.button(f"📄 {conv['name']}", key=f"conv_{conv_id}", use_container_width=True):
                st.session_state.conv_data["current_id"] = conv_id
                save_conversations(st.session_state.conv_data)
                st.rerun()
        with col2:
            if st.button("✏️", key=f"rename_{conv_id}"):
                new_name = st.text_input("新名称", value=conv['name'])
                if new_name:
                    st.session_state.conv_data["conversations"][conv_id]["name"] = new_name
                    save_conversations(st.session_state.conv_data)
                    st.rerun()
        with col3:
            if len(conv_items) > 1:
                if st.button("🗑️", key=f"del_{conv_id}"):
                    delete_conversation(conv_id)

    st.divider()

    # ========== 知识库管理 ==========
    st.header("📚 知识库")

    # 上传文档
    uploaded_files = st.file_uploader(
        "上传文档 (PDF/TXT)",
        type=["pdf", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        for file in uploaded_files:
            # 检查是否已存在
            exists = False
            for doc in st.session_state.knowledge_base["documents"]:
                if doc["name"] == file.name:
                    exists = True
                    break
            if not exists:
                with st.spinner(f"处理 {file.name}..."):
                    text = extract_text(file)
                    chunks = split_text(text)
                    st.session_state.knowledge_base["documents"].append({
                        "name": file.name,
                        "content": text,
                        "chunks": chunks,
                        "size": len(text)
                    })
                    save_knowledge_base(st.session_state.knowledge_base)
                    st.success(f"✅ 已添加 {file.name}")
                    st.rerun()

    # 显示文档列表
    if st.session_state.knowledge_base["documents"]:
        st.subheader("📄 已加载文档")
        for i, doc in enumerate(st.session_state.knowledge_base["documents"]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.caption(f"📄 {doc['name']} ({doc['size']} 字符)")
            with col2:
                if st.button("🗑️", key=f"del_doc_{i}"):
                    st.session_state.knowledge_base["documents"].pop(i)
                    save_knowledge_base(st.session_state.knowledge_base)
                    st.rerun()

        if st.button("🗑️ 清空全部文档", use_container_width=True):
            st.session_state.knowledge_base["documents"] = []
            save_knowledge_base(st.session_state.knowledge_base)
            st.rerun()

        st.info(f"📊 共 {len(st.session_state.knowledge_base['documents'])} 个文档")
    else:
        st.info("暂无文档，请上传 PDF 或 TXT 文件")

    st.divider()

    # ========== 模型设置 ==========
    st.header("⚙️ 模型设置")

    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            st.success("✅ AI 已连接")
            models = [m["name"] for m in r.json().get("models", [])]
            if models:
                st.session_state.selected_model = st.selectbox("选择模型", models, key="main_model")
    except:
        st.error("❌ 连接失败")

    st.divider()

    # ========== 语言设置 ==========
    st.subheader("🌐 语言")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("中文", use_container_width=True):
            st.session_state.language = "中文"
            st.rerun()
    with col2:
        if st.button("English", use_container_width=True):
            st.session_state.language = "English"
            st.rerun()

    st.divider()

    if st.button("🗑️ 清空当前对话", use_container_width=True):
        current_msgs = get_current_messages()
        current_msgs.clear()
        save_current_messages(current_msgs)
        st.rerun()


# ========== 调用 AI ==========
def call_ai(prompt, system_prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": st.session_state.selected_model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 2048}
            },
            timeout=120
        )
        if response.status_code == 200:
            return response.json().get("response", "")
        return f"错误: {response.status_code}"
    except Exception as e:
        return f"出错了: {e}"


# ========== 聊天界面 ==========
messages = get_current_messages()

for msg in messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 用户输入
if prompt := st.chat_input("输入问题..."):
    with st.chat_message("user"):
        st.write(prompt)
    messages.append({"role": "user", "content": prompt})
    save_current_messages(messages)

    with st.chat_message("assistant"):
        with st.spinner("搜索知识库并思考中..."):
            # 语言指令
            if st.session_state.language == "中文":
                system_prompt = "你必须只使用中文回答。不要使用任何英文。"
            else:
                system_prompt = "You must answer in English only."

            # 知识库检索
            context = ""
            if st.session_state.knowledge_base["documents"]:
                results = search_knowledge(prompt, st.session_state.knowledge_base["documents"])
                if results:
                    context = "【参考文档内容】\n\n"
                    for r in results:
                        context += f"来自《{r['name']}》：\n{r['content'][:1500]}\n\n---\n\n"
                    context += "请基于以上文档内容回答用户的问题。如果文档中没有相关信息，请如实告知。\n\n"
                    st.caption(f"📚 从 {len(results)} 个文档中找到相关内容")

            # 对话历史
            if len(messages) > 1:
                recent = messages[-6:-1]
                history = ""
                for msg in recent:
                    role = "用户" if msg["role"] == "user" else "助手"
                    history += f"{role}：{msg['content']}\n\n"
                full_prompt = f"{context}对话历史：\n{history}\n用户最新问题：{prompt}"
            else:
                full_prompt = f"{context}{prompt}"

            answer = call_ai(full_prompt, system_prompt)
            st.write(answer)
            messages.append({"role": "assistant", "content": answer})
            save_current_messages(messages)