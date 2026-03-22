import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ✅ LangChain 버전별 import 경로 호환 처리 (Summary Memory)
try:
    from langchain.memory import ConversationSummaryMemory  # type: ignore
except Exception:
    try:
        from langchain_classic.memory import ConversationSummaryMemory  # type: ignore
    except Exception:
        raise ImportError(
            "ConversationSummaryMemory import 실패. "
            "pip show langchain langchain-community langchain-openai 결과를 알려주시면 "
            "정확한 경로로 맞춰드릴게요."
        )

load_dotenv()

st.set_page_config(page_title="PDF RAG Chatbot (Chat UI + Button)", layout="wide")
st.title("📄 PDF 기반 문서 Q&A (RAG + Summary Memory)")
st.caption("PDF를 인덱싱한 뒤, 질문 입력 후 Enter 또는 '질문' 버튼으로 전송하세요.")

# ----------------------------
# 사이드바: 설정
# ----------------------------
with st.sidebar:
    st.header("설정")
    embedding_model = st.text_input("Embedding 모델", value="text-embedding-3-small")
    chat_model = st.text_input("Chat 모델", value="gpt-5-nano")
    k = st.slider("검색 Top-k", min_value=1, max_value=10, value=3)
    chunk_size = st.slider("chunk_size", 200, 2000, 500, step=50)
    chunk_overlap = st.slider("chunk_overlap", 0, 500, 100, step=10)

    st.divider()
    st.subheader("메모리/대화")
    if st.button("🧹 대화 초기화"):
        st.session_state.memory = None
        st.session_state.messages = []
        st.success("대화를 초기화했습니다.")

# ----------------------------
# 세션 상태
# ----------------------------
if "vectordb" not in st.session_state:
    st.session_state.vectordb = None

if "memory" not in st.session_state:
    st.session_state.memory = None

# Chat UI용 메시지 저장소
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------------------
# PDF 인덱싱 유틸
# ----------------------------
def build_vectordb(pdf_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        docs = splitter.split_documents(pages)

        embeddings = OpenAIEmbeddings(model=embedding_model)
        vectordb = FAISS.from_documents(docs, embeddings)
        return vectordb, len(docs)

    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

# ----------------------------
# 메모리(요약) 생성/보장
# ----------------------------
def ensure_memory():
    if st.session_state.memory is None:
        llm_for_memory = ChatOpenAI(model=chat_model, temperature=0)
        st.session_state.memory = ConversationSummaryMemory(
            llm=llm_for_memory,
            return_messages=True,
        )
    return st.session_state.memory

# ----------------------------
# RAG 프롬프트
# ----------------------------
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "너는 업로드된 PDF 문서를 근거로 답변하는 어시스턴트다. "
            "반드시 제공된 [참고문서] 내용과 [대화요약]을 바탕으로 답변하라. "
            "근거가 없으면 '문서에서 근거를 찾지 못했습니다'라고 말하라. "
            "답변은 한국어로 간결하고 정확하게 작성하라.",
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "[참고문서]\n{context}\n\n[질문]\n{question}"),
    ]
)

# ----------------------------
# 질문 처리(공통)
# ----------------------------
def handle_user_question(user_text: str):
    user_text = (user_text or "").strip()
    if not user_text:
        return

    # 유저 메시지 표시/저장
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # 인덱싱 확인
    if st.session_state.vectordb is None:
        assistant_text = "먼저 PDF를 업로드한 뒤, 'PDF 인덱싱(벡터DB 생성)'을 진행해주세요."
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
        with st.chat_message("assistant"):
            st.markdown(assistant_text)
        return

    # 메모리 로드
    memory = ensure_memory()
    history = memory.load_memory_variables({})["history"]

    # 문서 검색
    retriever = st.session_state.vectordb.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(user_text) or []
    context = "\n\n".join(
        [f"- (p{d.metadata.get('page', '?')}) {d.page_content}" for d in docs]
    )

    # 답변 생성
    llm = ChatOpenAI(model=chat_model, temperature=0)
    chain = prompt | llm

    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):
            answer = chain.invoke({"history": history, "context": context, "question": user_text})
            assistant_text = answer.content
        st.markdown(assistant_text)

    # 저장 + 요약 메모리 업데이트
    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
    memory.save_context({"input": user_text}, {"output": assistant_text})

# ----------------------------
# 상단: PDF 업로드/인덱싱
# ----------------------------
with st.container(border=True):
    st.subheader("1) PDF 업로드 & 인덱싱")
    uploaded_pdf = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
    col_a, col_b = st.columns([1, 1])

    with col_a:
        if st.button("📌 PDF 인덱싱(벡터DB 생성)", disabled=(uploaded_pdf is None)):
            with st.spinner("PDF 읽는 중 → 청크 분할 → 임베딩 → FAISS 인덱싱..."):
                vectordb, n_chunks = build_vectordb(uploaded_pdf)
                st.session_state.vectordb = vectordb
            st.success(f"완료! 총 청크 수: {n_chunks}")

    with col_b:
        st.write("")
        if st.session_state.vectordb is None:
            st.warning("아직 인덱싱이 안 되어 있습니다.")
        else:
            st.success("인덱싱 완료: 아래에서 질문하세요.")

st.divider()

# ----------------------------
# 채팅 로그 렌더링
# ----------------------------
st.subheader("2) 채팅")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----------------------------
# ✅ 입력창 + '질문' 버튼: form을 사용하면 Enter = submit 가능
# ----------------------------
with st.form("chat_form", clear_on_submit=True):
    col_in, col_btn = st.columns([0.85, 0.15], vertical_alignment="bottom")
    with col_in:
        user_text = st.text_input(
            "질문 입력",
            label_visibility="collapsed",
            placeholder="질문을 입력하세요… (Enter 또는 오른쪽 '질문' 버튼)",
        )
    with col_btn:
        submitted = st.form_submit_button("질문", use_container_width=True)

    if submitted:
        # form_submit_button은 rerun을 일으키므로, 여기서 바로 처리하면 UI가 자연스럽습니다.
        handle_user_question(user_text)

# ----------------------------
# (선택) 메모리 요약 확인
# ----------------------------
with st.expander("현재 대화 요약(메모리) 보기"):
    if st.session_state.memory is None:
        st.write("메모리가 아직 생성되지 않았습니다.")
    else:
        st.write(st.session_state.memory.buffer)